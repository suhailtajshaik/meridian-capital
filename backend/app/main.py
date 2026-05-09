"""Meridian FastAPI application entry point.

Endpoints:
    POST /api/upload                — parse file, run full snapshot, return results
    POST /api/chat                  — streaming SSE chat with the advisor graph
    GET  /api/snapshot/{session_id} — retrieve latest snapshot for a session
    DELETE /api/data/{session_id}   — drop session data + LangGraph checkpoints
    GET  /api/health                — health check
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.agents.graph import create_advisor_graph, run_full_snapshot
from app.agents.schemas import (
    ChatMessage,
    ChatRequest,
    Snapshot,
    TraceEvent,
)
from app.config import settings
from app.ingestion.anonymizer import anonymize_for_llm
from app.ingestion.parser import parse_document
from app.ingestion.tabular_rag import TabularRAG
from app.llm import get_llm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Meridian Finance Advisor API",
    description="Multi-agent AI financial advisor backend.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{settings.frontend_port}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory session store
# (In production this would be Redis; for hackathon, a process-level dict is fine.)
# ---------------------------------------------------------------------------

# session_id -> {"snapshot": Snapshot, "financial_data": dict, "table_name": str}
# In-memory cache backed by per-session JSON files in DATA_DIR so state survives restarts.
_sessions: dict[str, dict] = {}

# LangGraph graph singleton (lazy init to avoid startup overhead when LLM key is missing)
_graph: Optional[object] = None


def _get_graph() -> object:
    global _graph
    if _graph is None:
        llm = get_llm()
        _graph = create_advisor_graph(llm, settings.checkpoints_db_path)
    return _graph


def _session_db(session_id: str) -> str:
    return settings.session_db_path(session_id)


def _session_state_path(session_id: str) -> Path:
    return Path(settings.data_dir) / f"{session_id}_state.json"


def _persist_session(session_id: str) -> None:
    """Write the session's snapshot + financial_data to disk so it survives restarts."""
    sess = _sessions.get(session_id)
    if not sess:
        return
    snap = sess.get("snapshot")
    payload = {
        "snapshot": json.loads(snap.model_dump_json()) if isinstance(snap, Snapshot) else None,
        "financial_data": sess.get("financial_data", {}),
        "table_name": sess.get("table_name"),
    }
    path = _session_state_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(payload, default=str))
    except Exception as exc:
        logger.warning("Failed to persist session %s: %s", session_id, exc)


def _load_session(session_id: str) -> Optional[dict]:
    """Load a previously-persisted session from disk into the in-memory cache."""
    path = _session_state_path(session_id)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
        snap_dict = payload.get("snapshot")
        snapshot = Snapshot(**snap_dict) if snap_dict else None
        sess = {
            "snapshot": snapshot,
            "financial_data": payload.get("financial_data", {}),
            "table_name": payload.get("table_name"),
        }
        _sessions[session_id] = sess
        return sess
    except Exception as exc:
        logger.warning("Failed to load session %s from disk: %s", session_id, exc)
        return None


def _get_session(session_id: str) -> Optional[dict]:
    """Look up a session, loading from disk if not in the in-memory cache."""
    sess = _sessions.get(session_id)
    if sess is not None:
        return sess
    return _load_session(session_id)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# POST /api/upload
# ---------------------------------------------------------------------------


def _save_raw_upload(session_id: str, filename: str, content: bytes) -> Path:
    """Save the raw uploaded file under data/{session_id}/uploads/{filename}."""
    safe_name = Path(filename).name  # strip any path components
    target = Path(settings.data_dir) / session_id / "uploads" / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


async def _upload_event_stream(
    file_content: bytes,
    filename: str,
    session_id: str,
) -> AsyncGenerator[str, None]:
    """SSE generator: streams ingestion stages, then live agent trace events."""
    from app.agents.graph import trace_queue_var

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data, default=str)}\n\n"

    # Stage 1 — parse
    yield _sse({"type": "stage", "stage": "parse", "label": "Parsing document"})
    try:
        df = await parse_document(file_content, filename)
    except Exception as exc:
        logger.exception("Parse failed: %s", filename)
        yield _sse({"type": "error", "stage": "parse", "message": str(exc)})
        yield _sse({"type": "done"})
        return

    if df.empty:
        yield _sse({"type": "error", "stage": "parse", "message": "Document is empty"})
        yield _sse({"type": "done"})
        return

    # Stage 2 — normalize (parser already snake_cased columns; emit stage for UI)
    yield _sse({"type": "stage", "stage": "normalize", "label": "Normalizing columns"})
    await asyncio.sleep(0)  # let event flush

    # Stage 3 — redact / anonymize
    yield _sse({"type": "stage", "stage": "redact", "label": "Anonymizing PII"})
    financial_summary = anonymize_for_llm(df)
    financial_summary["source_filename"] = filename

    # Save raw file alongside structured data
    raw_path = _save_raw_upload(session_id, filename, file_content)

    # Stage 4 — index into per-session SQLite
    yield _sse({"type": "stage", "stage": "index", "label": "Indexing into SQLite"})
    db_path = _session_db(session_id)
    table_name = Path(filename).stem.replace(" ", "_").replace("-", "_").lower()
    try:
        rag = TabularRAG(db_path=db_path, llm=get_llm())
        rag.ingest(df, table_name)
    except Exception as exc:
        logger.error("TabularRAG ingest failed: %s", exc)

    # Merge into session financial data
    if session_id not in _sessions:
        if _load_session(session_id) is None:
            _sessions[session_id] = {"snapshot": None, "financial_data": {}, "table_name": None}

    existing = _sessions[session_id].get("financial_data", {})
    if existing:
        merged = {**existing, f"doc_{table_name}": financial_summary}
    else:
        merged = financial_summary
    _sessions[session_id]["financial_data"] = merged
    _sessions[session_id]["table_name"] = table_name

    # Emit ingest_complete with metadata
    yield _sse({
        "type": "ingest_complete",
        "rows": int(len(df)),
        "columns": list(df.columns),
        "table_name": table_name,
        "raw_path": str(raw_path.relative_to(Path.cwd())) if raw_path.is_relative_to(Path.cwd()) else str(raw_path),
        "session_id": session_id,
    })

    # Stage 5 — analyze (run LangGraph with live trace streaming)
    yield _sse({"type": "stage", "stage": "analyze", "label": "Running advisor agents"})

    # Set up streaming trace queue and run snapshot in a background task
    queue: asyncio.Queue = asyncio.Queue()
    token = trace_queue_var.set(queue)
    snapshot: Optional[Snapshot] = None

    async def _run_snapshot() -> None:
        nonlocal snapshot
        try:
            snapshot = await run_full_snapshot(
                graph=_get_graph(),
                user_data=merged,
                session_id=session_id,
            )
        except Exception as exc:
            logger.exception("Snapshot generation failed")
            snapshot = Snapshot(generated_at=_now_iso())
        finally:
            await queue.put(None)  # sentinel

    snapshot_task = asyncio.create_task(_run_snapshot())

    try:
        # Drain trace events until the sentinel arrives
        while True:
            event = await queue.get()
            if event is None:
                break
            yield _sse({"type": "trace", "event": json.loads(event.model_dump_json())})

        await snapshot_task  # ensure done

        if snapshot is not None:
            _sessions[session_id]["snapshot"] = snapshot
            _persist_session(session_id)
            yield _sse({"type": "snapshot", "snapshot": json.loads(snapshot.model_dump_json())})
    finally:
        trace_queue_var.reset(token)

    yield _sse({"type": "done"})


@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(default_factory=lambda: str(uuid.uuid4())),
) -> StreamingResponse:
    """Parse, persist, and analyze an uploaded document — streams progress as SSE.

    SSE event shapes:
        {type:"stage", stage:"parse"|"normalize"|"redact"|"index"|"analyze", label}
        {type:"ingest_complete", rows, columns, table_name, raw_path, session_id}
        {type:"trace", event:TraceEvent}
        {type:"snapshot", snapshot:Snapshot}
        {type:"error", stage, message}
        {type:"done"}
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}")

    return StreamingResponse(
        _upload_event_stream(content, file.filename, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Session-Id": session_id,
        },
    )


# Old JSON-style upload kept for compatibility with any non-SSE clients (e.g. curl tests)
async def _legacy_upload_response(content: bytes, filename: str, session_id: str) -> dict:
    """Run the same pipeline synchronously and return a JSON dict (no streaming)."""
    df = await parse_document(content, filename)
    if df.empty:
        raise HTTPException(status_code=422, detail="Document is empty")

    financial_summary = anonymize_for_llm(df)
    financial_summary["source_filename"] = filename
    _save_raw_upload(session_id, filename, content)

    table_name = Path(filename).stem.replace(" ", "_").replace("-", "_").lower()
    try:
        TabularRAG(db_path=_session_db(session_id), llm=get_llm()).ingest(df, table_name)
    except Exception as exc:
        logger.error("TabularRAG ingest failed: %s", exc)

    if session_id not in _sessions:
        if _load_session(session_id) is None:
            _sessions[session_id] = {"snapshot": None, "financial_data": {}, "table_name": None}
    existing = _sessions[session_id].get("financial_data", {})
    merged = {**existing, f"doc_{table_name}": financial_summary} if existing else financial_summary
    _sessions[session_id]["financial_data"] = merged
    _sessions[session_id]["table_name"] = table_name

    try:
        snapshot = await run_full_snapshot(graph=_get_graph(), user_data=merged, session_id=session_id)
    except Exception as exc:
        logger.error("Snapshot failed: %s", exc)
        snapshot = Snapshot(generated_at=_now_iso())

    _sessions[session_id]["snapshot"] = snapshot
    _persist_session(session_id)

    return {
        "session_id": session_id,
        "rows": int(len(df)),
        "columns": list(df.columns),
        "table_name": table_name,
        "snapshot": json.loads(snapshot.model_dump_json()),
    }


# ---------------------------------------------------------------------------
# POST /api/chat  (SSE streaming)
# ---------------------------------------------------------------------------


async def _stream_chat(request: ChatRequest) -> AsyncGenerator[str, None]:
    """Generate SSE events for a chat response."""

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    session_id = request.session_id
    financial_data = {}

    # Load session financial data if available (from memory or disk)
    sess = _get_session(session_id)
    if sess:
        financial_data = sess.get("financial_data", {})

    # Collect trace events during execution
    trace_events: list[TraceEvent] = []

    def trace_callback(event: TraceEvent) -> None:
        trace_events.append(event)

    # Yield a heartbeat immediately so the connection stays alive
    yield _sse({"type": "heartbeat", "timestamp": _now_iso()})

    graph = _get_graph()
    llm = get_llm()

    # Convert ChatMessage objects to the format graph expects
    messages_for_graph = [
        {"role": msg.role, "content": msg.content}
        for msg in request.messages
    ]

    # Merge in any context provided by the client
    if request.context:
        financial_data = {**financial_data, **request.context}

    from app.agents.graph import AdvisorState

    initial_state: AdvisorState = {
        "messages": messages_for_graph,
        "user_financial_data": financial_data,
        "debt_analysis": _sessions.get(session_id, {}).get("snapshot") and
                         getattr(_sessions[session_id].get("snapshot"), "debt_analysis", None),
        "budget_advice": _sessions.get(session_id, {}).get("snapshot") and
                         getattr(_sessions[session_id].get("snapshot"), "budget_advice", None),
        "savings_strategy": _sessions.get(session_id, {}).get("snapshot") and
                            getattr(_sessions[session_id].get("snapshot"), "savings_strategy", None),
        "payoff_plan": _sessions.get(session_id, {}).get("snapshot") and
                       getattr(_sessions[session_id].get("snapshot"), "payoff_plan", None),
        "current_agent": "supervisor",
        "needs_clarification": False,
        "clarification_question": None,
        "intent": "full_snapshot",
        "agents_completed": [],
        "trace": [],
    }

    config = {"configurable": {"thread_id": session_id}}

    try:
        # Stream graph execution
        from app.agents.graph import FallbackGraph

        if isinstance(graph, FallbackGraph):
            final_state = await graph.ainvoke(initial_state)
        else:
            final_state = await graph.ainvoke(initial_state, config=config)

        # Emit all trace events
        for event in final_state.get("trace", []):
            if isinstance(event, TraceEvent):
                yield _sse({"type": "trace", "event": json.loads(event.model_dump_json())})
            elif isinstance(event, dict):
                yield _sse({"type": "trace", "event": event})

        # Emit the assistant message
        all_messages = final_state.get("messages", [])
        for msg in all_messages:
            if isinstance(msg, dict):
                role = msg.get("role")
                content = msg.get("content", "")
                agent = msg.get("agent")
            else:
                role = getattr(msg, "role", None)
                content = getattr(msg, "content", "")
                agent = getattr(msg, "agent", None)

            if role == "assistant":
                chat_msg = ChatMessage(role="assistant", content=content, agent=agent)
                yield _sse({"type": "message", "message": json.loads(chat_msg.model_dump_json())})

        # Update session snapshot if new analysis was produced
        new_snapshot = Snapshot(
            debt_analysis=final_state.get("debt_analysis"),
            budget_advice=final_state.get("budget_advice"),
            savings_strategy=final_state.get("savings_strategy"),
            payoff_plan=final_state.get("payoff_plan"),
            generated_at=_now_iso(),
        )
        if session_id not in _sessions:
            _sessions[session_id] = {"snapshot": None, "financial_data": financial_data, "table_name": None}
        _sessions[session_id]["snapshot"] = new_snapshot
        _persist_session(session_id)

    except asyncio.CancelledError:
        logger.info("Chat stream cancelled for session %s", session_id)
        return
    except Exception as exc:
        logger.exception("Chat stream error for session %s", session_id)
        error_msg = ChatMessage(
            role="assistant",
            content=(
                "I encountered an error while processing your request. "
                "Please try again or rephrase your question."
            ),
            agent="error_handler",
        )
        yield _sse({"type": "message", "message": json.loads(error_msg.model_dump_json())})

    yield _sse({"type": "done"})


@app.post("/api/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Stream an SSE response for a chat turn.

    Each SSE event is a JSON line with one of these shapes:
        {"type": "trace", "event": TraceEvent}
        {"type": "message", "message": ChatMessage}
        {"type": "heartbeat", "timestamp": str}
        {"type": "done"}
    """

    async def heartbeat_wrapper() -> AsyncGenerator[str, None]:
        """Wrap the main stream with a periodic 15-second heartbeat."""
        last_heartbeat = asyncio.get_event_loop().time()
        heartbeat_interval = 15.0

        async for chunk in _stream_chat(request):
            yield chunk
            now = asyncio.get_event_loop().time()
            if now - last_heartbeat >= heartbeat_interval:
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': _now_iso()})}\n\n"
                last_heartbeat = now

    return StreamingResponse(
        heartbeat_wrapper(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# GET /api/snapshot/{session_id}
# ---------------------------------------------------------------------------


@app.get("/api/snapshot/{session_id}")
async def get_snapshot(session_id: str) -> JSONResponse:
    """Return the latest Snapshot for a session, or 404 if not found."""
    session = _get_session(session_id)
    if not session or not session.get("snapshot"):
        raise HTTPException(
            status_code=404,
            detail=f"No snapshot found for session '{session_id}'. Upload a document first.",
        )

    snapshot: Snapshot = session["snapshot"]
    return JSONResponse(json.loads(snapshot.model_dump_json()))


# ---------------------------------------------------------------------------
# DELETE /api/data/{session_id}
# ---------------------------------------------------------------------------


@app.delete("/api/data/{session_id}")
async def delete_session_data(session_id: str) -> JSONResponse:
    """Drop all data for a session (SQLite tables + LangGraph checkpoints)."""

    # Remove from in-memory store
    removed = _sessions.pop(session_id, None)

    # Remove persisted session state JSON
    state_path = _session_state_path(session_id)
    if state_path.exists():
        try:
            state_path.unlink()
            removed = True
        except Exception as exc:
            logger.warning("Could not delete session state %s: %s", state_path, exc)

    # Remove session SQLite file
    db_path = Path(settings.session_db_path(session_id))
    db_removed = False
    if db_path.exists():
        try:
            db_path.unlink()
            db_removed = True
        except Exception as exc:
            logger.warning("Could not delete session DB %s: %s", db_path, exc)

    # Clear LangGraph checkpoints for this thread
    try:
        checkpoints_db = Path(settings.checkpoints_db_path)
        if checkpoints_db.exists():
            with sqlite3.connect(str(checkpoints_db)) as conn:
                conn.execute(
                    "DELETE FROM checkpoints WHERE thread_id = ?", (session_id,)
                )
                conn.execute(
                    "DELETE FROM writes WHERE thread_id = ?", (session_id,)
                )
    except Exception as exc:
        logger.warning("Could not clear LangGraph checkpoints for %s: %s", session_id, exc)

    return JSONResponse(
        {
            "deleted": bool(removed or db_removed),
            "session_id": session_id,
        }
    )


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------


@app.get("/api/health")
async def health() -> JSONResponse:
    """Basic health check."""
    return JSONResponse(
        {
            "status": "ok",
            "model": settings.openrouter_model,
            "timestamp": _now_iso(),
        }
    )


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )

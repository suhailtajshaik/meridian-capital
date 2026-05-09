"""LangGraph StateGraph orchestrator for Meridian.

State fields:
    messages              list[ChatMessage]       — full conversation
    user_financial_data   dict                    — anonymized financial summary
    debt_analysis         Optional[DebtAnalysis]
    budget_advice         Optional[BudgetAdvice]
    savings_strategy      Optional[SavingsStrategy]
    payoff_plan           Optional[PayoffPlan]
    current_agent         str                     — which node is active
    needs_clarification   bool
    clarification_question Optional[str]
    trace                 list[TraceEvent]        — hero feature: full audit trail

Nodes: supervisor → (debt_analyzer | budget_coach | savings_strategist |
                      payoff_optimizer | clarify | synth)

After each specialist, control returns to supervisor which decides whether
to run more specialists or route to synth.
"""
from __future__ import annotations

import asyncio
import contextvars
import json
import logging
from datetime import date, datetime, timezone
from typing import Any, Callable, Optional


# Per-task trace queue — when set, _make_trace_collector also pushes events here
# so callers (like the SSE upload endpoint) can stream progress in real time.
trace_queue_var: contextvars.ContextVar[Optional[asyncio.Queue]] = contextvars.ContextVar(
    "meridian_trace_queue", default=None
)

from langchain_core.messages import HumanMessage, SystemMessage

try:
    from langgraph.graph import END, StateGraph  # type: ignore[import]
    from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore[import]
    _LANGGRAPH_AVAILABLE = True
except ImportError:
    _LANGGRAPH_AVAILABLE = False
    StateGraph = None  # type: ignore[assignment]
    SqliteSaver = None  # type: ignore[assignment]

from typing import TypedDict

from app.agents.budget_coach import BudgetCoach
from app.agents.debt_analyzer import DebtAnalyzer
from app.agents.payoff_optimizer import PayoffOptimizer
from app.agents.savings_strategist import SavingsStrategist
from app.agents.schemas import (
    BudgetAdvice,
    ChatMessage,
    DebtAnalysis,
    PayoffPlan,
    SavingsStrategy,
    Snapshot,
    TraceEvent,
)
from app.agents.supervisor import Supervisor

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------------


class AdvisorState(TypedDict, total=False):
    messages: list
    user_financial_data: dict
    debt_analysis: Optional[DebtAnalysis]
    budget_advice: Optional[BudgetAdvice]
    savings_strategy: Optional[SavingsStrategy]
    payoff_plan: Optional[PayoffPlan]
    current_agent: str
    needs_clarification: bool
    clarification_question: Optional[str]
    intent: str
    agents_completed: list
    trace: list


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------


def _make_trace_collector(state: dict) -> Callable[[TraceEvent], None]:
    """Return a callback that appends trace events to state['trace'].

    Also pushes the event onto the contextvar trace queue if one is set,
    so streaming endpoints can yield events as they happen.
    """
    queue = trace_queue_var.get()

    def callback(event: TraceEvent) -> None:
        trace = state.get("trace", [])
        trace.append(event)
        state["trace"] = trace
        if queue is not None:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass
    return callback


def _emit_to_queue(event_type: str, agent: str, payload: dict) -> None:
    """Push a synthetic trace event directly to the streaming queue (no state)."""
    queue = trace_queue_var.get()
    if queue is None:
        return
    try:
        queue.put_nowait(
            TraceEvent(
                type=event_type,  # type: ignore[arg-type]
                agent=agent,
                payload=payload,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
    except asyncio.QueueFull:
        pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_trace(state: AdvisorState, event_type: str, agent: str, payload: dict) -> None:
    trace = list(state.get("trace", []))
    trace.append(
        TraceEvent(
            type=event_type,  # type: ignore[arg-type]
            agent=agent,
            payload=payload,
            timestamp=_now_iso(),
        )
    )
    state["trace"] = trace  # type: ignore[typeddict-item]


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def create_advisor_graph(llm: Any, db_path: str) -> Any:
    """Build and compile the LangGraph StateGraph.

    Args:
        llm: LangChain chat model (from app.llm.get_llm).
        db_path: Path to the SQLite file used for LangGraph checkpointing.

    Returns:
        Compiled LangGraph app (or a FallbackGraph if LangGraph is not installed).
    """
    if not _LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph not installed — using FallbackGraph.")
        return FallbackGraph(llm)

    # ------------------------------------------------------------------
    # Node: supervisor
    # ------------------------------------------------------------------
    async def supervisor_node(state: AdvisorState) -> AdvisorState:
        _append_trace(state, "agent_start", "supervisor", {"intent_classification": True})
        supervisor = Supervisor(llm=llm)

        messages = state.get("messages", [])
        has_data = bool(state.get("user_financial_data"))

        classification = await supervisor.classify(messages, has_financial_data=has_data)
        intent = classification.get("intent", "full_snapshot")

        _append_trace(
            state,
            "agent_complete",
            "supervisor",
            {
                "intent": intent,
                "reasoning": classification.get("reasoning", ""),
                "needs_clarification": classification.get("needs_clarification", False),
            },
        )

        return {
            **state,
            "intent": intent,
            "current_agent": "supervisor",
            "needs_clarification": classification.get("needs_clarification", False),
            "clarification_question": classification.get("clarification_question"),
            "agents_completed": state.get("agents_completed", []),
        }

    # ------------------------------------------------------------------
    # Node: debt_analyzer
    # ------------------------------------------------------------------
    async def debt_analyzer_node(state: AdvisorState) -> AdvisorState:
        trace_cb = _make_trace_collector(state)  # type: ignore[arg-type]
        agent = DebtAnalyzer(llm=llm, trace_callback=trace_cb)

        user_data = state.get("user_financial_data", {})
        messages = state.get("messages", [])

        try:
            result = await agent.run(user_data, messages)
            completed = list(state.get("agents_completed", []))
            completed.append("debt_analyzer")
            return {**state, "debt_analysis": result, "agents_completed": completed}
        except Exception as exc:
            logger.error("debt_analyzer_node failed: %s", exc)
            _append_trace(state, "agent_complete", "debt_analyzer", {"error": str(exc)})
            completed = list(state.get("agents_completed", []))
            completed.append("debt_analyzer")
            return {**state, "agents_completed": completed}

    # ------------------------------------------------------------------
    # Node: budget_coach
    # ------------------------------------------------------------------
    async def budget_coach_node(state: AdvisorState) -> AdvisorState:
        trace_cb = _make_trace_collector(state)  # type: ignore[arg-type]
        agent = BudgetCoach(llm=llm, trace_callback=trace_cb)

        user_data = state.get("user_financial_data", {})
        messages = state.get("messages", [])

        try:
            result = await agent.run(user_data, messages)
            completed = list(state.get("agents_completed", []))
            completed.append("budget_coach")
            return {**state, "budget_advice": result, "agents_completed": completed}
        except Exception as exc:
            logger.error("budget_coach_node failed: %s", exc)
            _append_trace(state, "agent_complete", "budget_coach", {"error": str(exc)})
            completed = list(state.get("agents_completed", []))
            completed.append("budget_coach")
            return {**state, "agents_completed": completed}

    # ------------------------------------------------------------------
    # Node: savings_strategist
    # ------------------------------------------------------------------
    async def savings_strategist_node(state: AdvisorState) -> AdvisorState:
        trace_cb = _make_trace_collector(state)  # type: ignore[arg-type]
        agent = SavingsStrategist(llm=llm, trace_callback=trace_cb)

        user_data = state.get("user_financial_data", {})
        messages = state.get("messages", [])

        try:
            result = await agent.run(user_data, messages)
            completed = list(state.get("agents_completed", []))
            completed.append("savings_strategist")
            return {**state, "savings_strategy": result, "agents_completed": completed}
        except Exception as exc:
            logger.error("savings_strategist_node failed: %s", exc)
            _append_trace(state, "agent_complete", "savings_strategist", {"error": str(exc)})
            completed = list(state.get("agents_completed", []))
            completed.append("savings_strategist")
            return {**state, "agents_completed": completed}

    # ------------------------------------------------------------------
    # Node: payoff_optimizer
    # ------------------------------------------------------------------
    async def payoff_optimizer_node(state: AdvisorState) -> AdvisorState:
        trace_cb = _make_trace_collector(state)  # type: ignore[arg-type]
        agent = PayoffOptimizer(llm=llm, trace_callback=trace_cb)

        user_data = state.get("user_financial_data", {})
        messages = state.get("messages", [])
        debt_analysis = state.get("debt_analysis")

        try:
            result = await agent.run(user_data, messages, debt_analysis=debt_analysis)
            completed = list(state.get("agents_completed", []))
            completed.append("payoff_optimizer")
            return {**state, "payoff_plan": result, "agents_completed": completed}
        except Exception as exc:
            logger.error("payoff_optimizer_node failed: %s", exc)
            _append_trace(state, "agent_complete", "payoff_optimizer", {"error": str(exc)})
            completed = list(state.get("agents_completed", []))
            completed.append("payoff_optimizer")
            return {**state, "agents_completed": completed}

    # ------------------------------------------------------------------
    # Node: clarify
    # ------------------------------------------------------------------
    async def clarify_node(state: AdvisorState) -> AdvisorState:
        question = state.get("clarification_question") or (
            "Could you provide more details about your financial situation? "
            "For example, uploading a bank statement or credit card statement would help me give you precise advice."
        )
        _append_trace(state, "synth", "clarify", {"question": question})

        clarify_msg = ChatMessage(
            role="assistant",
            content=question,
            agent="supervisor",
        )
        messages = list(state.get("messages", []))
        messages.append(clarify_msg)
        return {**state, "messages": messages}

    # ------------------------------------------------------------------
    # Node: synth (final answer composer)
    # ------------------------------------------------------------------
    async def synth_node(state: AdvisorState) -> AdvisorState:
        _append_trace(state, "synth", "synth", {"composing_answer": True})

        # Build a concise context summary for the LLM
        parts: list[str] = []

        debt = state.get("debt_analysis")
        if debt:
            parts.append(
                f"Debt Analysis: {len(debt.debts)} debts totalling ${debt.total_debt:,.2f}. "
                f"Risk: {debt.risk_level.value}. {debt.summary}"
            )

        budget = state.get("budget_advice")
        if budget:
            surplus_label = "surplus" if budget.surplus_or_deficit >= 0 else "deficit"
            parts.append(
                f"Budget: ${budget.monthly_income:,.2f}/mo income, ${budget.total_expenses:,.2f} expenses, "
                f"${abs(budget.surplus_or_deficit):,.2f} {surplus_label}."
            )

        savings = state.get("savings_strategy")
        if savings:
            parts.append(
                f"Savings: {savings.months_of_runway:.1f} months runway. "
                f"Recommend saving ${savings.recommended_monthly_savings:,.2f}/mo. "
                f"{savings.strategy_narrative}"
            )

        payoff = state.get("payoff_plan")
        if payoff:
            parts.append(
                f"Payoff Plan ({payoff.strategy.value}): debt-free by {payoff.debt_free_date}, "
                f"saving ${payoff.total_interest_saved_vs_minimum:,.2f} vs minimums only."
            )

        context_str = "\n".join(parts) if parts else "No structured analysis available yet."

        user_question = ""
        for msg in reversed(state.get("messages", [])):
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
            if role == "user":
                content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
                user_question = content
                break

        synth_prompt = (
            f"You are Meridian, a friendly and precise AI financial advisor.\n\n"
            f"Structured analysis results:\n{context_str}\n\n"
            f"User's question: {user_question}\n\n"
            f"Write a clear, conversational response (3-6 sentences) that:\n"
            f"1. Directly answers the user's question using the structured data above.\n"
            f"2. Highlights 1-2 key insights or action items.\n"
            f"3. Ends with an invitation to explore a specific area further.\n"
            f"Do not repeat all the numbers — the dashboard shows those. Be warm and actionable."
        )

        messages_to_send = [
            SystemMessage(content="You are Meridian, a friendly AI financial advisor."),
            HumanMessage(content=synth_prompt),
        ]

        try:
            raw = await llm.ainvoke(messages_to_send)
            answer = raw.content if hasattr(raw, "content") else str(raw)
        except Exception as exc:
            logger.error("synth_node LLM call failed: %s", exc)
            answer = (
                "I've analyzed your financial data. "
                "Check the dashboard panels for detailed breakdowns of your debts, budget, savings, and payoff plan."
            )

        completed = state.get("agents_completed", [])
        agents_used = ", ".join(completed) if completed else "supervisor"

        response_msg = ChatMessage(
            role="assistant",
            content=answer,
            agent=agents_used,
        )

        messages = list(state.get("messages", []))
        messages.append(response_msg)

        _append_trace(state, "synth", "synth", {"answer_length": len(answer), "agents_used": agents_used})

        return {**state, "messages": messages}

    # ------------------------------------------------------------------
    # Routing functions
    # ------------------------------------------------------------------

    def route_supervisor(state: AdvisorState) -> str:
        """Determine which node to run after the supervisor."""
        if state.get("needs_clarification"):
            return "clarify"

        intent = state.get("intent", "full_snapshot")
        completed = state.get("agents_completed", [])

        # Intent → required agents mapping
        required = {
            "debt_analysis": ["debt_analyzer"],
            "budget_advice": ["budget_coach"],
            "savings_strategy": ["savings_strategist"],
            "payoff_plan": ["debt_analyzer", "payoff_optimizer"],
            "full_snapshot": ["debt_analyzer", "budget_coach", "savings_strategist", "payoff_optimizer"],
            "general_chat": [],
            "clarify": [],
        }.get(intent, ["debt_analyzer", "budget_coach", "savings_strategist", "payoff_optimizer"])

        # Find first not-yet-completed required agent
        for agent_name in required:
            if agent_name not in completed:
                return agent_name

        # All required agents done — go to synth
        return "synth"

    def route_after_specialist(state: AdvisorState) -> str:
        """After any specialist, return to supervisor to re-evaluate."""
        return "supervisor_check"

    async def supervisor_check_node(state: AdvisorState) -> AdvisorState:
        """Lightweight re-entry: no LLM call, just re-evaluate routing."""
        return state

    def route_supervisor_check(state: AdvisorState) -> str:
        """Route after supervisor_check — same logic as route_supervisor."""
        return route_supervisor(state)

    # ------------------------------------------------------------------
    # Build the graph
    # ------------------------------------------------------------------
    graph = StateGraph(AdvisorState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("supervisor_check", supervisor_check_node)
    graph.add_node("debt_analyzer", debt_analyzer_node)
    graph.add_node("budget_coach", budget_coach_node)
    graph.add_node("savings_strategist", savings_strategist_node)
    graph.add_node("payoff_optimizer", payoff_optimizer_node)
    graph.add_node("clarify", clarify_node)
    graph.add_node("synth", synth_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "clarify": "clarify",
            "debt_analyzer": "debt_analyzer",
            "budget_coach": "budget_coach",
            "savings_strategist": "savings_strategist",
            "payoff_optimizer": "payoff_optimizer",
            "synth": "synth",
        },
    )

    graph.add_conditional_edges(
        "supervisor_check",
        route_supervisor_check,
        {
            "clarify": "clarify",
            "debt_analyzer": "debt_analyzer",
            "budget_coach": "budget_coach",
            "savings_strategist": "savings_strategist",
            "payoff_optimizer": "payoff_optimizer",
            "synth": "synth",
        },
    )

    # All specialists return to supervisor_check
    for specialist in ["debt_analyzer", "budget_coach", "savings_strategist", "payoff_optimizer"]:
        graph.add_edge(specialist, "supervisor_check")

    graph.add_edge("clarify", END)
    graph.add_edge("synth", END)

    # Compile without a checkpointer. Sync SqliteSaver is incompatible with
    # graph.ainvoke (the async path), and AsyncSqliteSaver requires manual
    # context-manager lifecycle. We persist snapshots + financial_data
    # ourselves in main.py, so multi-turn graph state isn't needed.
    return graph.compile()


# ---------------------------------------------------------------------------
# run_full_snapshot helper
# ---------------------------------------------------------------------------


async def run_full_snapshot(
    graph: Any,
    user_data: dict,
    session_id: str,
    messages: Optional[list] = None,
) -> Snapshot:
    """Run all four agents and return a Snapshot.

    Args:
        graph: Compiled LangGraph app from create_advisor_graph().
        user_data: Anonymized financial summary dict.
        session_id: Session identifier for LangGraph thread persistence.
        messages: Optional conversation history.

    Returns:
        Snapshot with all four agent outputs (some may be None on failure).
    """
    if messages is None:
        messages = [
            ChatMessage(
                role="user",
                content="Please provide a complete financial snapshot analysis.",
            )
        ]

    # Fast path: bypass LangGraph for full snapshots and run the 3 independent
    # agents (debt / budget / savings) in parallel via asyncio.gather, then run
    # payoff (which needs the debt result) sequentially. Cuts wall time roughly
    # from sum(t_i) to max(t_debt, t_budget, t_savings) + t_payoff.
    #
    # We still emit trace events through the contextvar queue so the SSE
    # /api/upload handler can stream live progress to the UI.
    from app.agents.budget_coach import BudgetCoach
    from app.agents.debt_analyzer import DebtAnalyzer
    from app.agents.payoff_optimizer import PayoffOptimizer
    from app.agents.savings_strategist import SavingsStrategist

    # Pull the LLM out of the graph if we can; otherwise build one fresh.
    llm = getattr(graph, "llm", None)
    if llm is None:
        from app.llm import get_llm
        llm = get_llm()

    # Per-agent trace collector that BOTH appends to a local trace list AND
    # forwards to the contextvar queue (so SSE consumers see events live).
    trace: list[TraceEvent] = []

    def make_cb() -> Callable[[TraceEvent], None]:
        queue = trace_queue_var.get()
        def cb(event: TraceEvent) -> None:
            trace.append(event)
            if queue is not None:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    pass
        return cb

    async def _run(agent_cls, **kwargs):
        agent = agent_cls(llm=llm, trace_callback=make_cb())
        try:
            return await agent.run(user_data, messages, **kwargs)
        except Exception as exc:
            logger.error("%s failed: %s", agent_cls.__name__, exc)
            return None

    # Wave 1 — three independent agents in parallel
    debt_result, budget_result, savings_result = await asyncio.gather(
        _run(DebtAnalyzer),
        _run(BudgetCoach),
        _run(SavingsStrategist),
    )

    # Wave 2 — payoff depends on debt analysis
    payoff_result = None
    if debt_result is not None:
        payoff_agent = PayoffOptimizer(llm=llm, trace_callback=make_cb())
        try:
            payoff_result = await payoff_agent.run(
                user_data, messages, debt_analysis=debt_result
            )
        except Exception as exc:
            logger.error("PayoffOptimizer failed: %s", exc)

    return Snapshot(
        debt_analysis=debt_result,
        budget_advice=budget_result,
        savings_strategy=savings_result,
        payoff_plan=payoff_result,
        generated_at=_now_iso(),
    )


# ---------------------------------------------------------------------------
# FallbackGraph — used when LangGraph is not installed
# ---------------------------------------------------------------------------


class FallbackGraph:
    """Minimal sequential runner used as a fallback when LangGraph is absent."""

    def __init__(self, llm: Any) -> None:
        self.llm = llm

    async def ainvoke(self, state: AdvisorState, config: Optional[dict] = None) -> AdvisorState:
        """Run all four agents sequentially without graph routing."""
        trace: list = []

        def make_cb(s: dict) -> Callable[[TraceEvent], None]:
            def cb(e: TraceEvent) -> None:
                trace.append(e)
            return cb

        user_data = state.get("user_financial_data", {})
        messages = state.get("messages", [])

        debt_result: Optional[DebtAnalysis] = None
        budget_result: Optional[BudgetAdvice] = None
        savings_result: Optional[SavingsStrategy] = None
        payoff_result: Optional[PayoffPlan] = None

        for AgentClass, key in [
            (DebtAnalyzer, "debt"),
            (BudgetCoach, "budget"),
            (SavingsStrategist, "savings"),
        ]:
            try:
                agent = AgentClass(llm=self.llm, trace_callback=make_cb({}))
                result = await agent.run(user_data, messages)
                if key == "debt":
                    debt_result = result
                elif key == "budget":
                    budget_result = result
                elif key == "savings":
                    savings_result = result
            except Exception as exc:
                logger.error("FallbackGraph %s failed: %s", AgentClass.__name__, exc)

        try:
            po = PayoffOptimizer(llm=self.llm, trace_callback=make_cb({}))
            payoff_result = await po.run(user_data, messages, debt_analysis=debt_result)
        except Exception as exc:
            logger.error("FallbackGraph PayoffOptimizer failed: %s", exc)

        return {
            **state,
            "debt_analysis": debt_result,
            "budget_advice": budget_result,
            "savings_strategy": savings_result,
            "payoff_plan": payoff_result,
            "agents_completed": ["debt_analyzer", "budget_coach", "savings_strategist", "payoff_optimizer"],
            "trace": trace,
        }

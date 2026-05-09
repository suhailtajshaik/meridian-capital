"""SelfCorrectingAgent — base class for all Meridian specialist agents.

Design:
- Tries ``llm.with_structured_output(schema)`` for one-shot structured extraction.
- Falls back to ``PydanticOutputParser`` + format instructions in the prompt.
- Up to 3 retries on Pydantic ValidationError: appends the error as a
  HumanMessage so the LLM can self-correct.
- Emits TraceEvent objects via an optional ``trace_callback`` so the
  LangGraph layer can forward them to the SSE stream.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Type

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from app.agents.schemas import TraceEvent

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class SelfCorrectingAgent:
    """Base class that wraps an LLM and produces a validated Pydantic model."""

    name: str = "base_agent"

    def __init__(
        self,
        llm: Any,
        output_schema: Type[BaseModel],
        system_prompt: str,
        trace_callback: Optional[Callable[[TraceEvent], None]] = None,
    ) -> None:
        self.llm = llm
        self.output_schema = output_schema
        self.system_prompt = system_prompt
        self.trace_callback = trace_callback

        # Attempt to build a structured-output chain; fall back to parser.
        self._structured_chain: Any = None
        self._parser: Any = None
        self._use_structured: bool = False

        try:
            self._structured_chain = llm.with_structured_output(output_schema)
            self._use_structured = True
        except (AttributeError, NotImplementedError):
            from langchain_core.output_parsers import PydanticOutputParser  # type: ignore[import]

            self._parser = PydanticOutputParser(pydantic_object=output_schema)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit(self, event_type: str, payload: dict) -> None:
        if self.trace_callback is None:
            return
        event = TraceEvent(
            type=event_type,  # type: ignore[arg-type]
            agent=self.name,
            payload=payload,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.trace_callback(event)

    def _build_messages(self, user_content: str, chat_history: list) -> list:
        """Assemble the message list to send to the LLM."""
        messages: list = [SystemMessage(content=self.system_prompt)]

        # Replay relevant chat history (skip system messages to avoid duplication)
        for msg in chat_history:
            role = getattr(msg, "role", None) or (
                msg.get("role") if isinstance(msg, dict) else None
            )
            content = getattr(msg, "content", None) or (
                msg.get("content") if isinstance(msg, dict) else str(msg)
            )
            if role == "assistant":
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=content))
            elif role == "user":
                messages.append(HumanMessage(content=content))

        messages.append(HumanMessage(content=user_content))
        return messages

    def _format_user_prompt(self, user_data: dict) -> str:
        """Convert the user_data dict into a prompt string."""
        try:
            data_str = json.dumps(user_data, indent=2, default=str)
        except Exception:
            data_str = str(user_data)

        if self._parser:
            format_instructions = self._parser.get_format_instructions()
            return (
                f"Analyze the following financial data and return a structured response.\n\n"
                f"Financial Data:\n{data_str}\n\n"
                f"{format_instructions}"
            )
        return (
            f"Analyze the following financial data and return your analysis.\n\n"
            f"Financial Data:\n{data_str}"
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run(self, user_data: dict, chat_history: list) -> BaseModel:
        """Run the agent and return a validated Pydantic model.

        Args:
            user_data: Anonymized financial data dict from the ingestion layer.
            chat_history: Previous ChatMessage objects for context.

        Returns:
            Validated Pydantic model of type ``self.output_schema``.

        Raises:
            ValueError: If the model fails to produce valid output after all retries.
        """
        self._emit("agent_start", {"input_keys": list(user_data.keys())})

        user_prompt = self._format_user_prompt(user_data)
        messages = self._build_messages(user_prompt, chat_history)
        last_error: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self._emit(
                    "tool_call",
                    {"attempt": attempt, "strategy": "structured" if self._use_structured else "parser"},
                )

                if self._use_structured and self._structured_chain is not None:
                    result = await self._structured_chain.ainvoke(messages)
                else:
                    raw = await self.llm.ainvoke(messages)
                    raw_text = raw.content if hasattr(raw, "content") else str(raw)
                    result = self._parser.parse(raw_text)

                # Validate (re-run validation in case structured output skipped it)
                if not isinstance(result, self.output_schema):
                    result = self.output_schema.model_validate(
                        result if isinstance(result, dict) else result.model_dump()
                    )

                self._emit("agent_complete", {"status": "success", "attempt": attempt})
                return result

            except (ValidationError, Exception) as exc:
                last_error = exc
                error_msg = str(exc)
                logger.warning(
                    "Agent %s attempt %d failed: %s",
                    self.name,
                    attempt,
                    error_msg[:200],
                )
                self._emit(
                    "tool_result",
                    {"attempt": attempt, "status": "error", "error": error_msg[:500]},
                )

                if attempt < MAX_RETRIES:
                    # Ask the LLM to fix the error on the next turn
                    correction_prompt = (
                        f"Your previous response had a validation error: {error_msg}\n\n"
                        f"Please fix the response so it conforms exactly to the required schema. "
                        f"Return only the corrected JSON object."
                    )
                    messages.append(HumanMessage(content=correction_prompt))

        self._emit("agent_complete", {"status": "failed", "attempts": MAX_RETRIES})
        raise ValueError(
            f"Agent {self.name} failed after {MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

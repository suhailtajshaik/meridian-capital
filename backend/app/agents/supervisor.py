"""Supervisor — LLM-powered router that classifies user intent and orchestrates agents.

Intent classes:
    debt_analysis       -> DebtAnalyzer only
    budget_advice       -> BudgetCoach only
    savings_strategy    -> SavingsStrategist only
    payoff_plan         -> DebtAnalyzer + PayoffOptimizer
    full_snapshot       -> all 4 agents sequentially
    clarify             -> ask user a follow-up question
    general_chat        -> answer directly without running a specialist
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.schemas import TraceEvent

logger = logging.getLogger(__name__)

VALID_INTENTS = {
    "debt_analysis",
    "budget_advice",
    "savings_strategy",
    "payoff_plan",
    "full_snapshot",
    "clarify",
    "general_chat",
}

# Deterministic keyword → intent map. Match before invoking the LLM to avoid
# a 1-2s classification round-trip for unambiguous questions.
_INTENT_RULES: list[tuple[str, str]] = [
    (r"\b(debt[-\s]?free|payoff|pay\s+off|amortization|snowball|avalanche|interest\s+saved|months?\s+to\s+payoff)\b", "payoff_plan"),
    (r"\b(emergency\s+fund|runway|months?\s+of\s+expenses|savings?\s+(goal|plan|strategy)|nest\s+egg|hys?a)\b", "savings_strategy"),
    (r"\b(budget|spending|expenses?|categor(y|ies)|over[-\s]?spend|cut\s+spending|50/30/20|where.*(money|spend))\b", "budget_advice"),
    (r"\b(debt|owe|liabilit(y|ies)|apr|interest\s+rate|credit\s+card|loan|mortgage|balance|highest[-\s]?rate)\b", "debt_analysis"),
    (r"\b(snapshot|overview|full\s+picture|big\s+picture|everything|all\s+of\s+(it|my))\b", "full_snapshot"),
    (r"^\s*(hi|hey|hello|thanks|thank\s+you|ok|okay|cool|got\s+it)\s*[!?\.]?\s*$", "general_chat"),
]


def _rule_based_intent(text: str) -> Optional[str]:
    """Return an intent if a deterministic rule matches; else None."""
    if not text:
        return None
    lowered = text.lower().strip()
    import re
    for pattern, intent in _INTENT_RULES:
        if re.search(pattern, lowered):
            return intent
    return None

SUPERVISOR_SYSTEM_PROMPT = """You are the Meridian supervisor agent.  Your only job is to
classify the user's intent into exactly one of these categories and return a JSON object.

Categories:
- "debt_analysis"      — user wants to know about their debts, rates, risk
- "budget_advice"      — user wants spending analysis or budgeting help
- "savings_strategy"   — user wants a savings or emergency fund plan
- "payoff_plan"        — user wants a payoff schedule or strategy comparison
- "full_snapshot"      — user wants a complete financial overview / uploaded new documents
- "clarify"            — you need more information before answering (explain what is missing)
- "general_chat"       — greeting, off-topic, or question you can answer without data

Return ONLY this JSON (no extra text):
{
  "intent": "<one of the categories above>",
  "reasoning": "<one sentence explaining why>",
  "needs_clarification": false,
  "clarification_question": null
}

If intent is "clarify", set needs_clarification=true and provide the question.
"""


class Supervisor:
    """Routes user messages to the appropriate specialist agent(s)."""

    name = "supervisor"

    def __init__(
        self,
        llm: Any,
        trace_callback: Optional[Callable[[TraceEvent], None]] = None,
    ) -> None:
        self.llm = llm
        self.trace_callback = trace_callback

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

    async def classify(self, messages: list, has_financial_data: bool = False) -> dict:
        """Classify the user's intent from the conversation.

        Args:
            messages: Full conversation history (list of ChatMessage or dicts).
            has_financial_data: Whether the user has uploaded financial documents.

        Returns:
            Dict with keys: intent, reasoning, needs_clarification, clarification_question.
        """
        self._emit("agent_start", {"has_financial_data": has_financial_data})

        last_user_text = ""
        for m in reversed(messages):
            role = m.get("role") if isinstance(m, dict) else getattr(m, "role", None)
            content = m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")
            if role == "user" and content:
                last_user_text = content
                break

        rule_intent = _rule_based_intent(last_user_text)
        if rule_intent is not None:
            self._emit(
                "agent_complete",
                {"intent": rule_intent, "path": "rule_based", "reasoning": "keyword match"},
            )
            return {
                "intent": rule_intent,
                "reasoning": "Deterministic keyword match — skipped LLM classification.",
                "needs_clarification": False,
                "clarification_question": None,
            }

        conversation_text = "\n".join(
            f"{m.get('role', 'user') if isinstance(m, dict) else getattr(m, 'role', 'user')}: "
            f"{m.get('content', '') if isinstance(m, dict) else getattr(m, 'content', '')}"
            for m in messages[-6:]  # last 3 turns
        )

        context_note = (
            "The user HAS uploaded financial documents."
            if has_financial_data
            else "The user has NOT uploaded any financial documents yet."
        )

        prompt = (
            f"Context: {context_note}\n\n"
            f"Recent conversation:\n{conversation_text}\n\n"
            f"Classify the user's intent."
        )

        llm_messages = [
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        try:
            raw = await self.llm.ainvoke(llm_messages)
            raw_text = raw.content if hasattr(raw, "content") else str(raw)

            # Strip markdown fences if present
            raw_text = raw_text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            raw_text = raw_text.strip()

            result = json.loads(raw_text)

            # Validate intent
            intent = result.get("intent", "full_snapshot")
            if intent not in VALID_INTENTS:
                intent = "full_snapshot"
                result["intent"] = intent

            self._emit(
                "agent_complete",
                {"intent": intent, "reasoning": result.get("reasoning", "")},
            )
            return result

        except Exception as exc:
            logger.warning("Supervisor classification failed: %s", exc)
            self._emit("agent_complete", {"intent": "full_snapshot", "error": str(exc)})
            return {
                "intent": "full_snapshot",
                "reasoning": "Defaulting to full snapshot due to classification error.",
                "needs_clarification": False,
                "clarification_question": None,
            }

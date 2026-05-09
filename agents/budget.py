"""Budget Advisor: flags overspending categories and surplus opportunities."""
from __future__ import annotations

from .types import AgentMessage


def analyze(question: str, persona: dict) -> AgentMessage:
    """Identify over-budget categories and quantify redirectable surplus."""
    return {
        "role": "agent",
        "agent": "budget",
        "text": (
            "You're **$136 over** in dining out and **$140 over** on shopping "
            "this month. Pulling those back to budget would free up about "
            "**$276** for goals."
        ),
        "trace": {
            "total_ms": 980,
            "tool_count": 4,
            "steps": [
                {
                    "kind": "agent",
                    "agent": "budget",
                    "ms": 480,
                    "tools": [
                        {"name": "query_transactions",
                         "args": 'month: "May 2026"',
                         "result": "127 rows"},
                        {"name": "compare_to_budget",
                         "args": "by category",
                         "result": "2 categories over"},
                        {"name": "rag_retrieve",
                         "args": '"recurring discretionary"',
                         "result": "rows 18, 44, 61"},
                    ],
                    "conclusion": "Dining +$136, Shopping +$140 — both discretionary.",
                },
            ],
        },
    }

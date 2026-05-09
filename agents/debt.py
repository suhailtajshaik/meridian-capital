"""Debt Analyzer: ranks debts by APR, flags highest-yield payoff target."""
from __future__ import annotations

from .types import AgentMessage


def analyze(question: str, persona: dict) -> AgentMessage:
    """Identify the highest-yield debt to pay down. Stubbed to match CHAT_SEED."""
    return {
        "role": "agent",
        "agent": "debt",
        "text": (
            "**Sapphire Preferred** is your highest-yield payoff target at "
            "**22.49% APR**. Avalanche order is Sapphire → Quicksilver → Auto → "
            "Student → Mortgage."
        ),
        "trace": {
            "total_ms": 540,
            "tool_count": 2,
            "steps": [
                {
                    "kind": "agent",
                    "agent": "debt",
                    "ms": 540,
                    "tools": [
                        {"name": "query_debt_table",
                         "args": 'filter: "active", sort: "apr desc"',
                         "result": "3 rows"},
                        {"name": "compute_apr_weighted_risk",
                         "args": "debts",
                         "result": "22.49% top APR"},
                    ],
                    "conclusion": "Sapphire Preferred is the highest-yield payoff target.",
                },
            ],
        },
    }

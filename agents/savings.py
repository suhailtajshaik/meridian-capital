"""Savings Strategy: surfaces emergency-fund gaps, projects goal ETAs."""
from __future__ import annotations

from .types import AgentMessage


def analyze(question: str, persona: dict) -> AgentMessage:
    """Counter-take that flags emergency-fund coverage. Stubbed to match CHAT_SEED."""
    return {
        "role": "agent",
        "agent": "savings",
        "text": (
            "Counter-take: your **emergency fund is at 51%** of your 6-month "
            "target. If job stability is a concern, a 70/30 split "
            "(debt/emergency) keeps the avalanche logic mostly intact while "
            "strengthening your runway."
        ),
        "trace": {
            "total_ms": 740,
            "tool_count": 3,
            "steps": [
                {
                    "kind": "agent",
                    "agent": "savings",
                    "ms": 540,
                    "tools": [
                        {"name": "query_savings_goals",
                         "args": 'filter: "emergency"',
                         "result": "balance: $7,200 / $14,000"},
                        {"name": "rag_retrieve",
                         "args": '"monthly fixed expenses 6mo"',
                         "result": "rows 4, 18, 31"},
                        {"name": "project_runway",
                         "args": "balance: 7200, burn: 4380/mo",
                         "result": "1.6mo runway"},
                    ],
                    "conclusion": "Runway too thin for full payoff. Recommend 70/30 split.",
                },
            ],
        },
    }

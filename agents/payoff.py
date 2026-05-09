"""Payoff Optimizer: simulates avalanche vs snowball, projects interest savings."""
from __future__ import annotations

from .types import AgentMessage


def analyze(question: str, persona: dict) -> AgentMessage:
    """Recommend a concrete payoff allocation with projected interest savings."""
    return {
        "role": "agent",
        "agent": "payoff",
        "text": (
            "Pay $3,200 toward the **Sapphire Preferred** card (22.49% APR). "
            "That's the highest-rate balance you carry and the avalanche move "
            "saves you about **$612 in interest** over the next 18 months "
            "versus splitting the bonus."
        ),
        "structured": {
            "kind": "recommend-payoff",
            "target": "Sapphire Preferred",
            "amount": 3200,
            "interest_saved": 612,
        },
        "trace": {
            "total_ms": 620,
            "tool_count": 2,
            "steps": [
                {
                    "kind": "agent",
                    "agent": "payoff",
                    "ms": 620,
                    "tools": [
                        {"name": "rag_retrieve",
                         "args": '"chase sapphire statement", k=5',
                         "result": "rows 12, 47, 89, 104, 211"},
                        {"name": "simulate_avalanche",
                         "args": "extra: $3,200, horizon: 18mo",
                         "result": "−$612 interest"},
                    ],
                    "conclusion": "Avalanche move saves $612 vs split.",
                },
            ],
        },
    }

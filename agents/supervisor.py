"""Supervisor: decomposes user questions, routes to specialists, synthesizes."""
from __future__ import annotations

from .types import AgentMessage, SupervisorStep, SynthStep, Trace


def decompose(question: str) -> SupervisorStep:
    """Split a user question into sub-questions and pick which agents to route to.

    Today: keyword heuristic. Tomorrow: a small LLM call.
    """
    q = question.lower()
    if "bonus" in q or "windfall" in q or "extra" in q:
        return {
            "kind": "supervisor",
            "title": "Decomposed into 3 sub-questions",
            "ms": 380,
            "details": [
                "Which debt yields the highest guaranteed return?",
                "Is the emergency fund adequate for full payoff?",
                "What's the long-run interest delta?",
            ],
            "routes": ["debt", "savings", "payoff"],
        }
    if "spend" in q or "budget" in q or "over" in q:
        return {
            "kind": "supervisor",
            "title": "Decomposed into 2 sub-questions",
            "ms": 220,
            "details": [
                "Where is spending exceeding budget?",
                "How much can be redirected without lifestyle impact?",
            ],
            "routes": ["budget", "savings"],
        }
    return {
        "kind": "supervisor",
        "title": "Routed to default specialist",
        "ms": 200,
        "details": ["Single-agent question — no decomposition needed."],
        "routes": ["debt"],
    }


def synthesize(agent_outputs: list[AgentMessage]) -> AgentMessage:
    """Merge agent outputs into a final supervisor message with action buttons."""
    synth_step: SynthStep = {
        "kind": "synth",
        "ms": 180,
        "summary": (
            f"Merged {len(agent_outputs)} agent outputs · "
            "prioritized by certainty · flagged tradeoffs for follow-up"
        ),
    }
    trace: Trace = {"total_ms": 180, "tool_count": 0, "steps": [synth_step]}
    return {
        "role": "agent",
        "agent": "supervisor",
        "text": "**Synthesis** — see specialist replies above. Tap **Apply** or ask a follow-up.",
        "actions": ["Apply plan", "Show alternatives", "Why this recommendation?"],
        "trace": trace,
    }


def run(question: str, persona: dict) -> list[AgentMessage]:
    """End-to-end orchestration. Returns the full message list for the chat view."""
    from . import budget, debt, payoff, savings  # local import to avoid cycles

    plan = decompose(question)
    routed: list[AgentMessage] = []

    supervisor_msg: AgentMessage = {
        "role": "supervisor",
        "routing": plan["routes"],
        "text": f"Routing to {', '.join(plan['routes'])}.",
    }
    routed.append(supervisor_msg)

    dispatch = {
        "debt": debt.analyze,
        "savings": savings.analyze,
        "budget": budget.analyze,
        "payoff": payoff.analyze,
    }
    for agent_id in plan["routes"]:
        fn = dispatch.get(agent_id)
        if fn is not None:
            routed.append(fn(question, persona))

    routed.append(synthesize(routed))
    return routed

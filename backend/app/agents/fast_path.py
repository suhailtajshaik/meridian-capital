"""Deterministic fast-path answers — return instantly without invoking the LLM.

Matches questions whose answers are pure lookups against the cached snapshot
(or pure UI state like the active advisor scope). When a pattern hits, the
chat endpoint short-circuits the supervisor → specialist → synth pipeline.

Add new patterns here when a question is (a) common, (b) answerable from
structured data, and (c) doesn't need natural-language reasoning.
"""
from __future__ import annotations

import re
from typing import Optional

from app.agents.schemas import Snapshot

ADVISOR_LABELS = {
    "debt": "Debt Analyzer",
    "budget": "Budget Coach",
    "savings": "Savings Strategist",
    "payoff": "Payoff Optimizer",
}


def _money(amount: Optional[float]) -> str:
    if amount is None:
        return "$0"
    return f"${amount:,.0f}" if abs(amount) >= 100 else f"${amount:,.2f}"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def try_fast_answer(
    text: str,
    snapshot: Optional[Snapshot],
    advisor_scope: Optional[str],
) -> Optional[tuple[str, str]]:
    """Return (answer, agent_label) if the message matches a fast-path pattern."""
    q = _norm(text)
    if not q:
        return None

    if re.search(r"\b(which|what)\b.*\b(tab|view|page|advisor|screen)\b", q) or q in {
        "where am i", "what tab", "which tab", "what view", "which view",
    }:
        if advisor_scope and advisor_scope in ADVISOR_LABELS:
            return (
                f"You're on the **{ADVISOR_LABELS[advisor_scope]}** view. "
                f"Ask anything about your {advisor_scope} and I'll route to that specialist.",
                "fast_path",
            )
        return (
            "You're on a general view (Dashboard, Documents, or Settings). "
            "Switch to Debt, Budget, Savings, or Payoff to scope my answers to that advisor.",
            "fast_path",
        )

    if re.search(r"\b(which|what)\b.*\b(agents?|specialists?|advisors?)\b.*(running|available|exist|are there)", q):
        return (
            "Four specialist agents are available: **Debt Analyzer**, **Budget Coach**, "
            "**Savings Strategist**, and **Payoff Optimizer**. A Supervisor routes each "
            "question to the right one (or runs all four for a snapshot).",
            "fast_path",
        )

    da = snapshot.debt_analysis if snapshot else None
    ba = snapshot.budget_advice if snapshot else None
    sa = snapshot.savings_strategy if snapshot else None
    pp = snapshot.payoff_plan if snapshot else None

    if re.search(r"\btotal\s+debt\b|\bhow much\b.*\b(debt|owe)\b|\bdebt\s+balance\b", q):
        if da:
            import json as _json
            block = _json.dumps({
                "label": "Total debt",
                "value": _money(da.total_debt),
                "tone": "neg",
                "sub": f"across {len(da.debts)} liabilities · {da.weighted_avg_interest:.2f}% avg APR",
            })
            return (
                f"```meridian-stat\n{block}\n```\n\n"
                f"Highest priority debt: **{da.highest_priority_debt}**.",
                "debt_analyzer",
            )

    if re.search(r"\b(monthly\s+)?income\b|\btake[- ]home\b|\bsalary\b", q):
        if ba:
            return (f"Your monthly income is **{_money(ba.monthly_income)}**.", "budget_coach")

    if re.search(r"\b(monthly\s+)?(expenses?|spend(ing)?|spent)\b", q):
        if ba:
            return (
                f"Your monthly expenses total **{_money(ba.total_expenses)}** across "
                f"{len(ba.categories)} categories.",
                "budget_coach",
            )

    if re.search(r"\b(surplus|deficit|cash[- ]?flow|left\s*over)\b", q):
        if ba:
            import json as _json
            v = ba.surplus_or_deficit
            label = "surplus" if v >= 0 else "deficit"
            tone = "pos" if v >= 0 else "neg"
            block = _json.dumps({
                "label": f"Monthly {label}",
                "value": _money(abs(v)),
                "tone": tone,
                "sub": f"{_money(ba.monthly_income)} income − {_money(ba.total_expenses)} expenses",
            })
            return (
                f"```meridian-stat\n{block}\n```\n\n"
                f"{'Good news — you have room to accelerate debt payoff or boost savings.' if v >= 0 else 'Expenses exceed income — review your spending categories to find cuts.'}",
                "budget_coach",
            )

    if re.search(r"\bdebt[- ]?free\b|\bpaid\s+off\b|\bwhen\b.*\bdebt\b", q):
        if pp:
            import json as _json
            block = _json.dumps({
                "label": "Debt-free date",
                "value": pp.debt_free_date,
                "tone": "pos",
                "sub": f"{pp.strategy.value} · {_money(pp.monthly_budget_for_debt)}/mo · saves {_money(pp.total_interest_saved_vs_minimum)} vs minimums",
            })
            return (
                f"```meridian-stat\n{block}\n```\n\n"
                f"Switch to the Payoff tab for the full schedule and strategy comparison.",
                "payoff_optimizer",
            )

    if re.search(r"\b(emergency\s+fund|runway|how long.*last|months?\s+of\s+expenses)\b", q):
        if sa:
            return (
                f"Your emergency fund covers **{sa.months_of_runway:.1f} months** of expenses. "
                f"Target is {_money(sa.emergency_fund_target)}; recommended monthly contribution: "
                f"{_money(sa.recommended_monthly_savings)}.",
                "savings_strategist",
            )

    if re.search(r"\blist\b.*\bdebts?\b|\bshow\b.*\bdebts?\b|\bwhat\b.*\bdebts?\b.*\bhave\b", q):
        if da and da.debts:
            import json as _json
            table = _json.dumps({
                "headers": ["Debt", "Balance", "APR", "Min/mo"],
                "rows": [
                    [d.name, _money(d.balance), f"{d.interest_rate:.2f}%", _money(d.minimum_payment)]
                    for d in da.debts
                ],
            })
            return (
                f"You have {len(da.debts)} active debts:\n\n"
                f"```meridian-table\n{table}\n```\n\n"
                f"Focus on **{da.highest_priority_debt}** first — it carries the highest cost.",
                "debt_analyzer",
            )

    if re.search(r"\bhighest\s+(rate|apr|interest)\b|\bworst\s+debt\b|\bmost\s+expensive\b.*\bdebt\b", q):
        if da and da.debts:
            import json as _json
            worst = max(da.debts, key=lambda d: d.interest_rate)
            block = _json.dumps({
                "tone": "warn",
                "title": f"{worst.name} — {worst.interest_rate:.2f}% APR",
                "body": f"Balance {_money(worst.balance)} · min payment {_money(worst.minimum_payment)}/mo. This is your most expensive debt — target it first.",
            })
            return (
                f"```meridian-callout\n{block}\n```\n\n"
                f"Use the avalanche strategy in the Payoff tab to tackle it efficiently.",
                "debt_analyzer",
            )

    if not snapshot and re.search(r"\b(snapshot|status|analysis|advisors?)\b", q) and re.search(r"\b(ready|done|status|when)\b", q):
        return (
            "No analysis yet — add documents in the Documents tab to populate the advisors.",
            "fast_path",
        )

    return None

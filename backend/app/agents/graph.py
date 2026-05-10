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
import re
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
    BudgetCategoryAnalysis,
    ChatMessage,
    DebtAnalysis,
    DebtCategory,
    DebtItem,
    Milestone,
    PayoffOrderItem,
    PayoffPlan,
    PayoffStrategy,
    Recommendation,
    RiskLevel,
    SavingsStrategy,
    SavingsVehicle,
    Snapshot,
    TraceEvent,
)
from app.agents.supervisor import Supervisor
from app.utils.math_engine import compare_strategies, avalanche_plan

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


def _build_structured_fallback(
    debt: Optional[Any],
    budget: Optional[Any],
    savings: Optional[Any],
    payoff: Optional[Any],
    user_question: str,
) -> str:
    """Compose a DSL-block answer from already-computed agent outputs.

    Used when the synth LLM call fails — we still have all the structured data,
    so we render it directly instead of apologizing.
    """
    q = (user_question or "").lower()
    parts: list[str] = []

    def _money(v: Optional[float]) -> str:
        if v is None:
            return "$0"
        return f"${v:,.0f}" if abs(v) >= 100 else f"${v:,.2f}"

    show_debt = debt is not None and (
        not q or any(k in q for k in ("debt", "owe", "balance", "loan", "credit", "apr", "rate"))
    )
    show_budget = budget is not None and (
        not q or any(k in q for k in ("budget", "spend", "expense", "income", "surplus", "deficit", "category"))
    )
    show_savings = savings is not None and (
        not q or any(k in q for k in ("savings", "save", "emergency", "fund", "runway"))
    )
    show_payoff = payoff is not None and (
        not q or any(k in q for k in ("payoff", "free", "schedule", "avalanche", "snowball", "interest"))
    )

    if not any([show_debt, show_budget, show_savings, show_payoff]):
        show_debt = debt is not None
        show_budget = budget is not None
        show_savings = savings is not None
        show_payoff = payoff is not None

    if show_debt and debt is not None:
        block = json.dumps({
            "label": "Total debt",
            "value": _money(debt.total_debt),
            "tone": "neg",
            "sub": f"across {len(debt.debts)} liabilities · {debt.weighted_avg_interest:.2f}% avg APR · highest: {debt.highest_priority_debt}",
        })
        parts.append(f"```meridian-stat\n{block}\n```")

        if any(k in q for k in ("list", "show", "what debts", "all debts")):
            table = json.dumps({
                "headers": ["Debt", "Balance", "APR", "Min/mo"],
                "rows": [
                    [d.name, _money(d.balance), f"{d.interest_rate:.2f}%", _money(d.minimum_payment)]
                    for d in debt.debts
                ],
            })
            parts.append(f"```meridian-table\n{table}\n```")

    if show_budget and budget is not None:
        v = budget.surplus_or_deficit
        label = "surplus" if v >= 0 else "deficit"
        block = json.dumps({
            "label": f"Monthly {label}",
            "value": _money(abs(v)),
            "tone": "pos" if v >= 0 else "neg",
            "sub": f"{_money(budget.monthly_income)} income − {_money(budget.total_expenses)} expenses",
        })
        parts.append(f"```meridian-stat\n{block}\n```")

    if show_savings and savings is not None:
        parts.append(
            f"**Savings:** runway {savings.months_of_runway:.1f} months · "
            f"target {_money(savings.emergency_fund_target)} · "
            f"recommended {_money(savings.recommended_monthly_savings)}/mo."
        )

    if show_payoff and payoff is not None:
        block = json.dumps({
            "label": "Debt-free date",
            "value": payoff.debt_free_date,
            "tone": "pos",
            "sub": f"{payoff.strategy.value} · {_money(payoff.monthly_budget_for_debt)}/mo · saves {_money(payoff.total_interest_saved_vs_minimum)} vs minimums",
        })
        parts.append(f"```meridian-stat\n{block}\n```")

    if not parts:
        return (
            "I don't have enough analyzed data to answer that yet. "
            "Add documents in the Documents tab to populate the advisors."
        )

    return "\n\n".join(parts)


def _categorize_debt(name: str) -> DebtCategory:
    n = name.lower()
    if any(k in n for k in ("credit", "card", "capital one", "chase sapphire", "amex")):
        return DebtCategory.credit_card
    if any(k in n for k in ("student", "sofi", "navient", "fafsa")):
        return DebtCategory.student_loan
    if any(k in n for k in ("mortgage", "wells", "rocket", "home loan")):
        return DebtCategory.mortgage
    if any(k in n for k in ("auto", "honda", "toyota", "ford", "car loan")):
        return DebtCategory.auto_loan
    if any(k in n for k in ("medical", "hospital")):
        return DebtCategory.medical
    if "personal" in n:
        return DebtCategory.personal_loan
    return DebtCategory.other


def _pretty_source_name(filename: str | None, fallback: str) -> str:
    """Convert a CSV filename like 'capital_one_apr2026.csv' to 'Capital One'."""
    raw = (filename or fallback or "").lower()
    raw = raw.replace(".csv", "").replace(".xlsx", "").replace(".pdf", "")
    raw = re.sub(r"[_\-]?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|q[1-4])[_\-]?\d{0,4}", "", raw)
    raw = raw.strip("_- ")

    KNOWN = [
        ("capital_one", "Capital One Credit Card"),
        ("chase_checking", "Chase Checking"),
        ("chase_sapphire", "Chase Sapphire"),
        ("wells_mortgage", "Wells Fargo Mortgage"),
        ("wells", "Wells Fargo"),
        ("sofi_student_loan", "SoFi Student Loan"),
        ("sofi", "SoFi"),
        ("honda_auto_loan", "Honda Auto Loan"),
        ("honda", "Honda Financial"),
        ("schwab", "Schwab Brokerage"),
    ]
    for key, label in KNOWN:
        if key in raw:
            return label

    return " ".join(w.capitalize() for w in re.split(r"[_\s]+", raw) if w) or "Unknown"


def build_deterministic_snapshot(financial_data: dict) -> Snapshot:
    """Construct a Snapshot directly from anonymized doc_* entries.

    Used when LLM agents fail (e.g., OpenRouter quota): we still have
    structured numbers from the anonymizer + math_engine, so every
    advisor view can populate without any model call.
    """
    debts: list[DebtItem] = []
    monthly_income = 0.0
    monthly_expenses = 0.0
    spending_by_category: dict[str, float] = {}

    for key, doc in financial_data.items():
        if not isinstance(doc, dict):
            continue
        doc_type = doc.get("doc_type")
        pretty = _pretty_source_name(doc.get("source_filename"), key.replace("doc_", ""))

        if doc_type == "debt_statement":
            balance = doc.get("balance")
            apr = doc.get("apr")
            payment = doc.get("monthly_payment") or 0.0
            lender_label = doc.get("lender")
            display_name = (
                f"{lender_label} {pretty.split(' ', 1)[1]}" if lender_label and " " in pretty
                else lender_label or pretty
            )
            if balance and apr is not None:
                debts.append(DebtItem(
                    name=display_name,
                    category=_categorize_debt(display_name),
                    balance=float(balance),
                    interest_rate=float(apr),
                    minimum_payment=float(payment),
                    due_date=doc.get("statement_date"),
                ))

        elif doc_type == "amortization":
            balance = doc.get("current_balance")
            apr = doc.get("implied_apr")
            payment = doc.get("monthly_payment") or 0.0
            if balance and apr is not None:
                debts.append(DebtItem(
                    name=pretty,
                    category=_categorize_debt(pretty),
                    balance=float(balance),
                    interest_rate=float(apr),
                    minimum_payment=float(payment),
                    due_date=None,
                ))

        elif doc_type == "credit_card_statement":
            balance = doc.get("current_balance")
            apr = doc.get("apr")
            min_payment = doc.get("minimum_payment") or 0.0
            if balance and apr is not None:
                debts.append(DebtItem(
                    name=pretty,
                    category=DebtCategory.credit_card,
                    balance=float(balance),
                    interest_rate=float(apr),
                    minimum_payment=float(min_payment),
                    due_date=None,
                ))

        if doc_type in ("transactions", "credit_card_statement"):
            inc = doc.get("estimated_monthly_income") or 0.0
            spend = doc.get("estimated_monthly_spend") or 0.0
            if doc_type == "transactions":
                monthly_income += float(inc)
                monthly_expenses += float(spend)
            cat_map = doc.get("spending_by_category") or {}
            for cat, amt in cat_map.items():
                spending_by_category[cat] = spending_by_category.get(cat, 0.0) + float(amt)

    # ── DebtAnalysis
    debt_analysis: Optional[DebtAnalysis] = None
    if debts:
        total_debt = sum(d.balance for d in debts)
        weighted_avg = (sum(d.balance * d.interest_rate for d in debts) / total_debt) if total_debt > 0 else 0.0
        worst = max(debts, key=lambda d: d.interest_rate)
        min_total = sum(d.minimum_payment for d in debts)
        if weighted_avg >= 18:
            risk = RiskLevel.critical
        elif weighted_avg >= 10:
            risk = RiskLevel.high
        elif weighted_avg >= 6:
            risk = RiskLevel.moderate
        else:
            risk = RiskLevel.low
        debt_analysis = DebtAnalysis(
            debts=debts,
            total_debt=round(total_debt, 2),
            weighted_avg_interest=round(weighted_avg, 2),
            highest_priority_debt=worst.name,
            monthly_minimum_total=round(min_total, 2),
            debt_to_income_ratio=round(total_debt / (monthly_income * 12), 2) if monthly_income > 0 else None,
            risk_level=risk,
            summary=(
                f"{len(debts)} liabilities totaling ${total_debt:,.0f} at {weighted_avg:.2f}% weighted APR. "
                f"Highest cost: {worst.name} at {worst.interest_rate:.2f}%."
            ),
        )

    # ── BudgetAdvice
    budget_advice: Optional[BudgetAdvice] = None
    if monthly_income > 0 or spending_by_category:
        categories: list[BudgetCategoryAnalysis] = []
        for cat, amt in sorted(spending_by_category.items(), key=lambda kv: -kv[1]):
            pct_income = (amt / monthly_income * 100) if monthly_income > 0 else 0.0
            if cat.lower() in ("housing", "rent", "mortgage"):
                rec = Recommendation.on_track
            elif pct_income > 15:
                rec = Recommendation.reduce
            else:
                rec = Recommendation.on_track
            categories.append(BudgetCategoryAnalysis(
                category=cat,
                amount=round(amt, 2),
                percentage_of_income=round(pct_income, 2),
                recommendation=rec,
                suggested_amount=None,
            ))
        surplus = monthly_income - monthly_expenses
        sorted_cats = sorted(spending_by_category.items(), key=lambda kv: -kv[1])
        top3 = [f"Reduce {cat} (${amt:,.0f}/mo)" for cat, amt in sorted_cats[:3]] or ["No major spending categories detected."]
        actionable = (
            ["Build an emergency fund", "Pay down highest-APR debt first", "Automate monthly savings"]
            if surplus > 0
            else ["Cut discretionary spending", "Review subscriptions", "Defer non-essential purchases"]
        )
        budget_advice = BudgetAdvice(
            monthly_income=round(monthly_income, 2),
            total_expenses=round(monthly_expenses, 2),
            surplus_or_deficit=round(surplus, 2),
            categories=categories,
            top_3_savings_opportunities=top3,
            actionable_steps=actionable,
            fifty_thirty_twenty={
                "needs": round(monthly_income * 0.5, 2),
                "wants": round(monthly_income * 0.3, 2),
                "savings": round(monthly_income * 0.2, 2),
            },
        )

    # ── SavingsStrategy
    savings_strategy: Optional[SavingsStrategy] = None
    if budget_advice:
        target = round(monthly_expenses * 3, 2)
        rec_save = round(max(0.0, budget_advice.surplus_or_deficit) * 0.5, 2)
        savings_strategy = SavingsStrategy(
            emergency_fund_target=target,
            current_emergency_fund=0.0,
            months_of_runway=0.0,
            recommended_monthly_savings=rec_save,
            savings_vehicles=[
                SavingsVehicle(type="High-Yield Savings Account", reason="Liquid, FDIC-insured emergency fund vehicle.", expected_yield=4.5),
            ],
            milestone_timeline=[
                Milestone(goal="1-month emergency fund", eta=f"{int((monthly_expenses / rec_save)) if rec_save > 0 else 0} months", target_amount=round(monthly_expenses, 2)),
                Milestone(goal="3-month emergency fund", eta=f"{int((target / rec_save)) if rec_save > 0 else 0} months", target_amount=target),
            ],
            strategy_narrative=(
                f"Build a ${target:,.0f} emergency fund (3 months expenses). "
                f"At ${rec_save:,.0f}/month savings, milestones reach steadily."
            ),
        )

    # ── PayoffPlan
    payoff_plan: Optional[PayoffPlan] = None
    if debt_analysis and debt_analysis.debts:
        debt_inputs = [
            {"name": d.name, "balance": d.balance, "apr": d.interest_rate / 100.0, "minimum_payment": d.minimum_payment}
            for d in debt_analysis.debts
        ]
        budget_for_debt = debt_analysis.monthly_minimum_total + (
            max(0.0, budget_advice.surplus_or_deficit) * 0.5 if budget_advice else 0.0
        )
        try:
            cmp = compare_strategies(debt_inputs, budget_for_debt)
            avalanche = avalanche_plan(debt_inputs, budget_for_debt)
            order = [
                PayoffOrderItem(
                    debt_name=name,
                    months_to_payoff=avalanche["months_to_payoff"].get(name, 0),
                    total_interest_paid=round(avalanche["total_interest_by_debt"].get(name, 0.0), 2),
                )
                for name in avalanche["payoff_order"]
            ]
            min_total_interest = cmp.get("minimum_only_total_interest", avalanche["total_interest"])
            saved = max(0.0, min_total_interest - avalanche["total_interest"])
            payoff_plan = PayoffPlan(
                strategy=PayoffStrategy.avalanche,
                monthly_budget_for_debt=round(budget_for_debt, 2),
                payoff_order=order,
                total_interest_saved_vs_minimum=round(saved, 2),
                debt_free_date=avalanche["debt_free_date"],
                monthly_schedule=avalanche["monthly_schedule"],
                comparison={
                    "avalanche": {
                        "total_interest": round(cmp["avalanche"]["total_interest"], 2),
                        "debt_free_date": cmp["avalanche"]["debt_free_date"],
                        "months_to_payoff": cmp["avalanche"]["months_to_payoff"],
                    },
                    "snowball": {
                        "total_interest": round(cmp["snowball"]["total_interest"], 2),
                        "debt_free_date": cmp["snowball"]["debt_free_date"],
                        "months_to_payoff": cmp["snowball"]["months_to_payoff"],
                    },
                },
            )
        except Exception as exc:
            logger.warning("Deterministic payoff math failed: %s", exc)

    return Snapshot(
        debt_analysis=debt_analysis,
        budget_advice=budget_advice,
        savings_strategy=savings_strategy,
        payoff_plan=payoff_plan,
        generated_at=_now_iso(),
    )


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
        pre_intent = state.get("intent", "full_snapshot")
        if pre_intent and pre_intent != "full_snapshot":
            _append_trace(state, "agent_complete", "supervisor", {"intent": pre_intent, "pre_set": True})
            return {
                **state,
                "current_agent": "supervisor",
                "agents_completed": state.get("agents_completed", []),
            }

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

        callout = json.dumps({"tone": "info", "title": "A little more context needed", "body": question})
        clarify_content = f"```meridian-callout\n{callout}\n```"

        clarify_msg = ChatMessage(
            role="assistant",
            content=clarify_content,
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

        all_messages = state.get("messages", [])
        recent_messages = all_messages[-8:] if len(all_messages) > 8 else all_messages

        transcript_lines: list[str] = []
        user_question = ""
        for msg in recent_messages:
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
            if role in ("user", "assistant"):
                transcript_lines.append(f"{role}: {content}")
            if role == "user":
                user_question = content

        transcript_str = "\n".join(transcript_lines) if transcript_lines else ""

        synth_prompt = (
            f"You are Meridian, a friendly and precise AI financial advisor.\n\n"
            f"Structured analysis results:\n{context_str}\n\n"
            f"Conversation so far:\n{transcript_str}\n\n"
            f"Latest user question: {user_question}\n\n"
            f"You can include rich rendering blocks in your reply. The UI parses fenced JSON blocks tagged\n"
            f"`meridian-stat`, `meridian-bars`, `meridian-table`, `meridian-callout`, `meridian-list`.\n\n"
            f"When the user asks for a list, comparison, or specific number, prefer a block over a sentence.\n"
            f"Schemas:\n"
            f'  meridian-stat:    {{"label","value","sub?","tone": "neg|pos|info|neutral"}}\n'
            f'  meridian-bars:    {{"title","unit?","rows":[{{"label","value","tone?"}}]}}\n'
            f'  meridian-table:   {{"headers":[...], "rows":[[...],...]}}\n'
            f'  meridian-callout: {{"tone","title","body"}}\n'
            f'  meridian-list:    {{"title?","items":[{{"text","tone?"}}]}}\n\n'
            f"Use AT MOST 2 blocks per reply. Wrap each block in triple backticks with the language tag, e.g.\n\n"
            f"```meridian-stat\n"
            f'{{"label": "Total debt", "value": "<dollar amount from data>", "tone": "neg"}}\n'
            f"```\n\n"
            f"Keep surrounding text concise — one sentence to set up, one to follow up.\n\n"
            f"Write a clear, conversational response that:\n"
            f"1. Directly answers the user's question using the structured data above.\n"
            f"2. Uses a meridian-* block when answering with a number, comparison, or list — but never more than 2 blocks per reply.\n"
            f"3. Highlights 1-2 key insights or action items.\n"
            f"4. Ends with an invitation to explore a specific area further.\n"
            f"Do not repeat all the numbers in prose if you've put them in a block. Be warm and actionable."
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
            answer = _build_structured_fallback(
                debt=state.get("debt_analysis"),
                budget=state.get("budget_advice"),
                savings=state.get("savings_strategy"),
                payoff=state.get("payoff_plan"),
                user_question=user_question,
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

    snap = Snapshot(
        debt_analysis=debt_result,
        budget_advice=budget_result,
        savings_strategy=savings_result,
        payoff_plan=payoff_result,
        generated_at=_now_iso(),
    )

    if not any([debt_result, budget_result, savings_result, payoff_result]):
        det = build_deterministic_snapshot(user_data)
        if any([det.debt_analysis, det.budget_advice, det.savings_strategy, det.payoff_plan]):
            logger.warning("All LLM agents failed — using deterministic snapshot from anonymized data.")
            return det

    if any(r is None for r in (debt_result, budget_result, savings_result, payoff_result)):
        det = build_deterministic_snapshot(user_data)
        return Snapshot(
            debt_analysis=debt_result or det.debt_analysis,
            budget_advice=budget_result or det.budget_advice,
            savings_strategy=savings_result or det.savings_strategy,
            payoff_plan=payoff_result or det.payoff_plan,
            generated_at=snap.generated_at,
        )

    return snap


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

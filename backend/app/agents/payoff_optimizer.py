"""PayoffOptimizer — builds a mathematically correct debt payoff plan.

IMPORTANT: All amortization math is pre-computed by math_engine.py before
the LLM is called.  The LLM only narrates and formats the results — it
never guesses interest totals or payoff dates.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from app.agents.schemas import (
    DebtAnalysis,
    MonthlyScheduleItem,
    PayoffOrderItem,
    PayoffPlan,
    PayoffStrategy,
    TraceEvent,
)
from app.utils.math_engine import (
    DebtInput,
    avalanche_plan,
    compare_strategies,
    snowball_plan,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Meridian Payoff Optimizer, a specialist agent that creates
precise debt payoff plans.

You will receive pre-computed amortization results from a math engine (not guesses).
Your job is to:
1. Select the best strategy for this user (avalanche saves most interest; snowball provides
   motivational quick wins; hybrid when balances are close in size).
2. Format the math engine output into a PayoffPlan JSON object.
3. Write nothing — return only the JSON.

All numbers come from the math engine.  DO NOT recalculate or adjust them.
Return a single JSON object matching the PayoffPlan schema exactly.
"""


def _extract_debts_from_analysis(debt_analysis: DebtAnalysis) -> list[DebtInput]:
    """Convert DebtAnalysis items into DebtInput dicts for the math engine."""
    return [
        DebtInput(
            name=debt.name,
            balance=debt.balance,
            apr=debt.interest_rate / 100.0,  # schema stores as percentage
            minimum_payment=debt.minimum_payment,
        )
        for debt in debt_analysis.debts
    ]


class PayoffOptimizer:
    """Payoff plan builder that uses deterministic math + LLM narration."""

    name = "payoff_optimizer"

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

    async def run(
        self,
        user_data: dict,
        chat_history: list,
        debt_analysis: Optional[DebtAnalysis] = None,
    ) -> PayoffPlan:
        """Generate a PayoffPlan using deterministic math + LLM formatting.

        Args:
            user_data: Anonymized financial data dict (used to extract monthly budget).
            chat_history: Previous messages for context.
            debt_analysis: Pre-computed DebtAnalysis from the DebtAnalyzer agent.

        Returns:
            Validated PayoffPlan.
        """
        self._emit("agent_start", {"has_debt_analysis": debt_analysis is not None})

        # ------------------------------------------------------------------
        # 1. Extract debts from analysis or user_data
        # ------------------------------------------------------------------
        if debt_analysis and debt_analysis.debts:
            debts = _extract_debts_from_analysis(debt_analysis)
            monthly_minimum = debt_analysis.monthly_minimum_total
        else:
            # Fallback: parse debts directly from user_data
            raw_debts = user_data.get("debts", [])
            debts = [
                DebtInput(
                    name=d.get("name", f"Debt {i+1}"),
                    balance=float(d.get("balance", 0)),
                    apr=float(d.get("interest_rate", 0)) / 100.0,
                    minimum_payment=float(d.get("minimum_payment", 0)),
                )
                for i, d in enumerate(raw_debts)
                if float(d.get("balance", 0)) > 0
            ]
            monthly_minimum = sum(d["minimum_payment"] for d in debts)

        if not debts:
            raise ValueError("No debts found to optimize.")

        # ------------------------------------------------------------------
        # 2. Determine monthly budget (minimum + any stated extra payment)
        # ------------------------------------------------------------------
        extra_payment = float(user_data.get("extra_monthly_payment", 0))
        monthly_budget = monthly_minimum + extra_payment

        # Ensure budget is at least the sum of minimums
        if monthly_budget <= monthly_minimum:
            # Add a sensible default extra payment (10% of minimums)
            monthly_budget = monthly_minimum * 1.10

        self._emit(
            "tool_call",
            {
                "math_engine": "compare_strategies",
                "num_debts": len(debts),
                "monthly_budget": round(monthly_budget, 2),
            },
        )

        # ------------------------------------------------------------------
        # 3. Run deterministic math
        # ------------------------------------------------------------------
        comparison = compare_strategies(debts, monthly_budget)
        av_result = avalanche_plan(debts, monthly_budget)
        sb_result = snowball_plan(debts, monthly_budget)

        self._emit(
            "tool_result",
            {
                "avalanche_total_interest": comparison["avalanche"]["total_interest"],
                "snowball_total_interest": comparison["snowball"]["total_interest"],
                "avalanche_months": comparison["avalanche"]["months_to_payoff"],
            },
        )

        # ------------------------------------------------------------------
        # 4. Ask LLM to select strategy and format output
        # ------------------------------------------------------------------
        math_context = json.dumps(
            {
                "debts": [
                    {
                        "name": d["name"],
                        "balance": d["balance"],
                        "apr_pct": round(d["apr"] * 100, 2),
                        "minimum_payment": d["minimum_payment"],
                    }
                    for d in debts
                ],
                "monthly_budget_for_debt": round(monthly_budget, 2),
                "avalanche": av_result,
                "snowball": sb_result,
                "comparison": comparison,
            },
            indent=2,
            default=str,
        )

        prompt = (
            f"The math engine has produced the following pre-computed payoff results.\n\n"
            f"Math Engine Output:\n{math_context}\n\n"
            f"Instructions:\n"
            f"1. Choose the best strategy (avalanche / snowball / hybrid) for this user.\n"
            f"2. Return a JSON object matching the PayoffPlan schema using ONLY the numbers above.\n"
            f"3. For monthly_schedule, include all rows from the chosen strategy's schedule.\n"
            f"4. For comparison, use the 'comparison' dict (keys: avalanche, snowball).\n"
            f"5. total_interest_saved_vs_minimum = minimum_only_total_interest - chosen_total_interest "
            f"(use {comparison.get('minimum_only_total_interest', 0)} as minimum_only baseline).\n"
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        last_error: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                structured_chain = self.llm.with_structured_output(PayoffPlan)
                result = await structured_chain.ainvoke(messages)

                if not isinstance(result, PayoffPlan):
                    result = PayoffPlan.model_validate(
                        result if isinstance(result, dict) else result.model_dump()
                    )

                self._emit("agent_complete", {"status": "success", "attempt": attempt})
                return result

            except (ValidationError, Exception) as exc:
                last_error = exc
                logger.warning("PayoffOptimizer attempt %d failed: %s", attempt, str(exc)[:200])
                if attempt < 3:
                    messages.append(
                        HumanMessage(
                            content=(
                                f"Validation error on attempt {attempt}: {exc}\n"
                                f"Fix the JSON and return only the corrected PayoffPlan object."
                            )
                        )
                    )

        # ------------------------------------------------------------------
        # 5. Hard fallback: build PayoffPlan directly from math engine output
        # ------------------------------------------------------------------
        logger.warning("PayoffOptimizer LLM failed — constructing plan from math engine directly.")
        self._emit("agent_complete", {"status": "fallback", "reason": str(last_error)[:200]})

        chosen = av_result  # avalanche default
        strategy_enum = PayoffStrategy.avalanche

        payoff_order_items = [
            PayoffOrderItem(
                debt_name=name,
                months_to_payoff=chosen["months_to_payoff"].get(name, chosen["months_total"]),
                total_interest_paid=chosen["total_interest_by_debt"].get(name, 0.0),
            )
            for name in chosen["payoff_order"]
        ]

        schedule_items = [
            MonthlyScheduleItem(
                month=row["month"],
                debt_name=row["debt_name"],
                payment=row["payment"],
                principal=row["principal"],
                interest=row["interest"],
                remaining_balance=row["remaining_balance"],
            )
            for row in chosen["monthly_schedule"]
        ]

        min_only = comparison.get("minimum_only_total_interest", 0.0)
        interest_saved = max(0.0, min_only - chosen["total_interest"])

        return PayoffPlan(
            strategy=strategy_enum,
            monthly_budget_for_debt=round(monthly_budget, 2),
            payoff_order=payoff_order_items,
            total_interest_saved_vs_minimum=round(interest_saved, 2),
            debt_free_date=chosen["debt_free_date"],
            monthly_schedule=schedule_items,
            comparison={
                "avalanche": comparison["avalanche"],
                "snowball": comparison["snowball"],
            },
        )

"""Pure-Python financial math engine.

All calculations here are deterministic and never delegated to the LLM.
The PayoffOptimizer agent calls these functions first, then passes the
pre-computed numbers to the LLM as context so it can narrate results
without guessing.
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import TypedDict


# ---------------------------------------------------------------------------
# Types (plain dicts — not Pydantic so this module stays LLM-free)
# ---------------------------------------------------------------------------


class AmortizationRow(TypedDict):
    month: int
    payment: float
    principal: float
    interest: float
    remaining_balance: float


class DebtInput(TypedDict):
    name: str
    balance: float
    apr: float          # annual percentage rate as a decimal (e.g. 0.2499 for 24.99%)
    minimum_payment: float


class PayoffResult(TypedDict):
    payoff_order: list[str]
    months_to_payoff: dict[str, int]
    total_interest_by_debt: dict[str, float]
    total_interest: float
    months_total: int
    debt_free_date: str
    monthly_schedule: list[dict]


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------


def _round2(value: float) -> float:
    return round(value, 2)


def _monthly_rate(apr: float) -> float:
    """Convert annual rate (0.0-1.0) to monthly rate."""
    return apr / 12.0


def _debt_free_date(months: int) -> str:
    """Return the projected payoff date as an ISO date string."""
    today = date.today()
    target = today + timedelta(days=months * 30)
    return target.isoformat()


# ---------------------------------------------------------------------------
# Single-debt amortization
# ---------------------------------------------------------------------------


def amortize(
    balance: float,
    apr: float,
    monthly_payment: float,
    *,
    max_months: int = 600,
) -> list[AmortizationRow]:
    """Generate a full amortization schedule for a single debt.

    Args:
        balance: Current outstanding principal in USD.
        apr: Annual percentage rate as a decimal (0.2499 = 24.99%).
        monthly_payment: Fixed monthly payment in USD.
        max_months: Safety cap to prevent infinite loops.

    Returns:
        List of monthly rows.  The last row will have remaining_balance ≈ 0.
    """
    if balance <= 0:
        return []

    monthly_rate = _monthly_rate(apr)
    rows: list[AmortizationRow] = []
    remaining = balance

    for month in range(1, max_months + 1):
        interest = _round2(remaining * monthly_rate)
        # On the last payment the payment may be smaller than the fixed amount
        payment = min(_round2(monthly_payment), _round2(remaining + interest))
        principal = _round2(payment - interest)
        remaining = max(_round2(remaining - principal), 0.0)

        rows.append(
            AmortizationRow(
                month=month,
                payment=payment,
                principal=principal,
                interest=interest,
                remaining_balance=remaining,
            )
        )

        if remaining <= 0:
            break

    return rows


def _minimum_payment_months(balance: float, apr: float, min_payment: float) -> float:
    """Return total interest paid when making only minimum payments (no extra)."""
    monthly_rate = _monthly_rate(apr)
    if monthly_rate == 0:
        return balance  # no interest
    if min_payment <= balance * monthly_rate:
        # Payment doesn't cover interest — never pays off
        return float("inf")
    rows = amortize(balance, apr, min_payment, max_months=1200)
    return sum(r["interest"] for r in rows)


# ---------------------------------------------------------------------------
# Avalanche strategy (highest APR first)
# ---------------------------------------------------------------------------


def avalanche_plan(debts: list[DebtInput], monthly_budget: float) -> PayoffResult:
    """Compute an avalanche (highest-APR-first) debt payoff plan.

    Args:
        debts: List of debt inputs (name, balance, apr, minimum_payment).
        monthly_budget: Total dollars available for debt payments each month.

    Returns:
        PayoffResult with full monthly schedule.
    """
    return _compute_plan(debts, monthly_budget, strategy="avalanche")


# ---------------------------------------------------------------------------
# Snowball strategy (lowest balance first)
# ---------------------------------------------------------------------------


def snowball_plan(debts: list[DebtInput], monthly_budget: float) -> PayoffResult:
    """Compute a snowball (lowest-balance-first) debt payoff plan.

    Args:
        debts: List of debt inputs.
        monthly_budget: Total dollars available for debt payments each month.

    Returns:
        PayoffResult with full monthly schedule.
    """
    return _compute_plan(debts, monthly_budget, strategy="snowball")


# ---------------------------------------------------------------------------
# Internal plan engine
# ---------------------------------------------------------------------------


def _compute_plan(
    debts: list[DebtInput],
    monthly_budget: float,
    strategy: str,
) -> PayoffResult:
    """Core planner used by both avalanche and snowball.

    Implements the "debt snowball/avalanche roll-up" algorithm:
    - Each month pay minimums on all debts.
    - Apply any leftover budget to the priority debt.
    - When a debt is paid off, its minimum payment rolls into the next priority debt.
    """
    if not debts:
        return PayoffResult(
            payoff_order=[],
            months_to_payoff={},
            total_interest_by_debt={},
            total_interest=0.0,
            months_total=0,
            debt_free_date=date.today().isoformat(),
            monthly_schedule=[],
        )

    # Sort by priority
    if strategy == "avalanche":
        ordered = sorted(debts, key=lambda d: d["apr"], reverse=True)
    else:  # snowball
        ordered = sorted(debts, key=lambda d: d["balance"])

    # Mutable state
    balances: dict[str, float] = {d["name"]: float(d["balance"]) for d in debts}
    rates: dict[str, float] = {d["name"]: float(d["apr"]) for d in debts}
    min_payments: dict[str, float] = {d["name"]: float(d["minimum_payment"]) for d in debts}
    active_names = [d["name"] for d in ordered]  # priority order

    total_interest_by_debt: dict[str, float] = {d["name"]: 0.0 for d in debts}
    months_to_payoff: dict[str, int] = {}
    payoff_order: list[str] = []
    monthly_schedule: list[dict] = []
    month = 0
    max_months = 600

    while active_names and month < max_months:
        month += 1
        budget_remaining = float(monthly_budget)

        # Accrue interest on all active debts first
        accrued: dict[str, float] = {}
        for name in list(active_names):
            rate = _monthly_rate(rates[name])
            accrued[name] = _round2(balances[name] * rate)

        # Pay minimums on non-priority debts
        priority_debt = active_names[0]
        for name in active_names[1:]:
            min_pay = min(min_payments[name], balances[name] + accrued[name])
            interest = accrued[name]
            principal = _round2(min_pay - interest)
            balances[name] = max(_round2(balances[name] - principal), 0.0)
            total_interest_by_debt[name] += interest
            budget_remaining -= min_pay
            monthly_schedule.append(
                {
                    "month": month,
                    "debt_name": name,
                    "payment": _round2(min_pay),
                    "principal": _round2(principal),
                    "interest": _round2(interest),
                    "remaining_balance": balances[name],
                }
            )

        # Apply all remaining budget to priority debt
        budget_remaining = max(budget_remaining, 0.0)
        pri_interest = accrued[priority_debt]
        pri_payment = min(budget_remaining, _round2(balances[priority_debt] + pri_interest))
        pri_principal = _round2(pri_payment - pri_interest)
        balances[priority_debt] = max(_round2(balances[priority_debt] - pri_principal), 0.0)
        total_interest_by_debt[priority_debt] += pri_interest
        monthly_schedule.append(
            {
                "month": month,
                "debt_name": priority_debt,
                "payment": _round2(pri_payment),
                "principal": _round2(pri_principal),
                "interest": _round2(pri_interest),
                "remaining_balance": balances[priority_debt],
            }
        )

        # Check for payoffs
        newly_paid_off = [n for n in active_names if balances[n] <= 0.01]
        for name in newly_paid_off:
            months_to_payoff[name] = month
            payoff_order.append(name)
            active_names.remove(name)
            # Roll the freed minimum payment into the budget for subsequent months
            # (it becomes part of the implicit budget since we track budget_remaining already)

    return PayoffResult(
        payoff_order=payoff_order,
        months_to_payoff=months_to_payoff,
        total_interest_by_debt={k: _round2(v) for k, v in total_interest_by_debt.items()},
        total_interest=_round2(sum(total_interest_by_debt.values())),
        months_total=month,
        debt_free_date=_debt_free_date(month),
        monthly_schedule=monthly_schedule,
    )


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


def compare_strategies(debts: list[DebtInput], monthly_budget: float) -> dict:
    """Run both avalanche and snowball and return a comparison dict.

    Returns:
        Dict with keys "avalanche" and "snowball", each containing:
            - total_interest (float)
            - debt_free_date (str ISO)
            - months_to_payoff (int)
        Plus a "minimum_only" baseline for interest-saved calculation.
    """
    av = avalanche_plan(debts, monthly_budget)
    sb = snowball_plan(debts, monthly_budget)

    # Minimum-only baseline (pay only minimums, no extra)
    min_total_interest = sum(
        _minimum_payment_months(d["balance"], d["apr"], d["minimum_payment"])
        for d in debts
        if d["minimum_payment"] > d["balance"] * _monthly_rate(d["apr"])
    )

    return {
        "avalanche": {
            "total_interest": av["total_interest"],
            "debt_free_date": av["debt_free_date"],
            "months_to_payoff": av["months_total"],
        },
        "snowball": {
            "total_interest": sb["total_interest"],
            "debt_free_date": sb["debt_free_date"],
            "months_to_payoff": sb["months_total"],
        },
        "minimum_only_total_interest": _round2(min_total_interest),
    }

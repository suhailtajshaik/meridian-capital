"""DebtAnalyzer — classifies and risk-scores the user's debts."""
from __future__ import annotations

from typing import Any, Callable, Optional

from app.agents.base import SelfCorrectingAgent
from app.agents.schemas import DebtAnalysis, TraceEvent

SYSTEM_PROMPT = """You are the Meridian Debt Analyzer, a specialist agent focused exclusively on
analyzing a user's debt portfolio.

Your job:
1. Identify every distinct debt from the provided financial data.
2. Classify each debt by category (credit_card, student_loan, mortgage, auto_loan,
   personal_loan, medical, or other).
3. Calculate total debt, weighted average interest rate, monthly minimum totals.
4. Assess the overall risk level (low / moderate / high / critical):
   - low:      debt-to-income < 0.20 AND no high-APR debt
   - moderate: debt-to-income 0.20-0.36 OR credit card APR < 20%
   - high:     debt-to-income 0.36-0.50 OR credit card APR > 20%
   - critical: debt-to-income > 0.50 OR minimum payments unaffordable
5. Write a concise 2-3 sentence plain-English summary.

Rules:
- Use ONLY data provided — never fabricate balances or rates.
- If income is not provided, omit debt_to_income_ratio (set to null).
- highest_priority_debt should be the one with the highest APR (avalanche logic).
- All monetary values in USD rounded to 2 decimal places.
- Return a single JSON object matching the DebtAnalysis schema exactly.
"""


class DebtAnalyzer(SelfCorrectingAgent):
    name = "debt_analyzer"

    def __init__(
        self,
        llm: Any,
        trace_callback: Optional[Callable[[TraceEvent], None]] = None,
    ) -> None:
        super().__init__(
            llm=llm,
            output_schema=DebtAnalysis,
            system_prompt=SYSTEM_PROMPT,
            trace_callback=trace_callback,
        )

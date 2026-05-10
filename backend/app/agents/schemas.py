"""Pydantic v2 contracts for the Meridian multi-agent finance advisor.

These shapes are the public API contract — the frontend depends on every
field name and type defined here.  Do not rename fields without also
updating the React components.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class DebtCategory(str, Enum):
    credit_card = "credit_card"
    student_loan = "student_loan"
    mortgage = "mortgage"
    auto_loan = "auto_loan"
    personal_loan = "personal_loan"
    medical = "medical"
    other = "other"


class PayoffStrategy(str, Enum):
    avalanche = "avalanche"
    snowball = "snowball"
    hybrid = "hybrid"


class RiskLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class Recommendation(str, Enum):
    on_track = "on_track"
    reduce = "reduce"
    increase = "increase"


# ---------------------------------------------------------------------------
# DebtAnalysis
# ---------------------------------------------------------------------------


class DebtItem(BaseModel):
    name: str = Field(..., description="Human-readable label for this debt (e.g. 'Chase Sapphire')")
    category: DebtCategory = Field(..., description="Classification of the debt type")
    balance: float = Field(..., gt=0, description="Current outstanding balance in USD")
    interest_rate: float = Field(..., ge=0, le=100, description="Annual percentage rate (APR) as a percentage, e.g. 24.99")
    minimum_payment: float = Field(..., ge=0, description="Minimum required monthly payment in USD")
    due_date: Optional[str] = Field(None, description="Payment due date as ISO date string (YYYY-MM-DD) or natural language")


class DebtAnalysis(BaseModel):
    debts: list[DebtItem] = Field(..., description="All identified debts")
    total_debt: float = Field(..., description="Sum of all outstanding balances in USD")
    weighted_avg_interest: float = Field(..., description="Balance-weighted average APR across all debts")
    highest_priority_debt: str = Field(..., description="Name of the debt that should be paid off first (highest APR or smallest balance)")
    monthly_minimum_total: float = Field(..., description="Sum of all minimum monthly payments in USD")
    debt_to_income_ratio: Optional[float] = Field(None, description="Total debt divided by annual income; null if income unknown")
    risk_level: RiskLevel = Field(..., description="Overall debt risk assessment")
    summary: str = Field(..., description="Narrative summary of the debt situation in 2-3 sentences")


# ---------------------------------------------------------------------------
# BudgetAdvice
# ---------------------------------------------------------------------------


class BudgetCategoryAnalysis(BaseModel):
    category: str = Field(..., description="Spending category label (e.g. 'Groceries', 'Dining out')")
    amount: float = Field(..., description="Actual monthly spend in this category in USD")
    percentage_of_income: float = Field(..., description="This category's spend as a percentage of monthly income")
    recommendation: Recommendation = Field(..., description="Whether spending is on-track, should be reduced, or increased")
    suggested_amount: Optional[float] = Field(None, description="Recommended monthly target if not on-track, in USD")


class BudgetAdvice(BaseModel):
    monthly_income: float = Field(..., description="Estimated or stated monthly take-home income in USD")
    total_expenses: float = Field(..., description="Total monthly expenses across all categories in USD")
    surplus_or_deficit: float = Field(..., description="Income minus expenses; negative means deficit")
    categories: list[BudgetCategoryAnalysis] = Field(..., description="Per-category spending breakdown and recommendations")
    top_3_savings_opportunities: list[str] = Field(..., description="Three highest-impact areas to cut spending, as plain-English strings")
    actionable_steps: list[str] = Field(..., description="Concrete next steps the user can take this month")
    fifty_thirty_twenty: dict[str, float] = Field(
        ...,
        description="Breakdown of income into needs/wants/savings buckets per the 50/30/20 rule. Keys must be 'needs', 'wants', 'savings'.",
    )


# ---------------------------------------------------------------------------
# SavingsStrategy
# ---------------------------------------------------------------------------


class SavingsVehicle(BaseModel):
    type: str = Field(..., description="Account or investment type (e.g. 'High-Yield Savings Account', 'Roth IRA')")
    reason: str = Field(..., description="Why this vehicle is appropriate for this user's situation")
    expected_yield: Optional[float] = Field(None, description="Expected annual yield as a percentage (e.g. 4.5 for 4.5%)")

    @field_validator("expected_yield", mode="before")
    @classmethod
    def _coerce_yield(cls, v):
        if v is None or isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            cleaned = v.strip().rstrip("%").strip()
            if not cleaned:
                return None
            try:
                return float(cleaned)
            except ValueError:
                return None
        return v


class Milestone(BaseModel):
    goal: str = Field(..., description="Description of the savings goal (e.g. 'Fully funded emergency fund')")
    eta: str = Field(..., description="Estimated time to reach this milestone (e.g. '8 months', '2027-Q2')")
    target_amount: float = Field(..., description="Dollar amount to reach this milestone")


class SavingsStrategy(BaseModel):
    emergency_fund_target: float = Field(..., description="Recommended emergency fund size in USD (typically 3-6 months of expenses)")
    current_emergency_fund: float = Field(..., description="Estimated current emergency fund balance in USD")
    months_of_runway: float = Field(..., description="How many months of expenses the current emergency fund covers")
    recommended_monthly_savings: float = Field(..., description="Suggested monthly contribution to savings in USD")
    savings_vehicles: list[SavingsVehicle] = Field(..., description="Recommended account types ordered by priority")
    milestone_timeline: list[Milestone] = Field(..., description="Key savings milestones in chronological order")
    strategy_narrative: str = Field(..., description="Cohesive narrative explaining the savings strategy in 3-4 sentences")


# ---------------------------------------------------------------------------
# PayoffPlan
# ---------------------------------------------------------------------------


class PayoffOrderItem(BaseModel):
    debt_name: str = Field(..., description="Name of the debt matching a DebtItem.name")
    months_to_payoff: int = Field(..., description="Number of months until this debt reaches zero balance")
    total_interest_paid: float = Field(..., description="Total interest paid on this debt over its payoff period in USD")


class MonthlyScheduleItem(BaseModel):
    month: int = Field(..., description="Month number (1-based) in the payoff schedule")
    debt_name: str = Field(..., description="Which debt this payment row applies to")
    payment: float = Field(..., description="Total payment applied this month in USD")
    principal: float = Field(..., description="Portion of payment reducing principal in USD")
    interest: float = Field(..., description="Portion of payment covering interest in USD")
    remaining_balance: float = Field(..., description="Remaining balance after this payment in USD")


class PayoffPlan(BaseModel):
    strategy: PayoffStrategy = Field(..., description="The selected payoff strategy")
    monthly_budget_for_debt: float = Field(..., description="Total monthly dollars allocated to debt payoff in USD")
    payoff_order: list[PayoffOrderItem] = Field(..., description="Debts in the order they will be paid off")
    total_interest_saved_vs_minimum: float = Field(..., description="Total interest saved vs paying minimums only in USD")
    debt_free_date: str = Field(..., description="Projected debt-free date as ISO date string (YYYY-MM-DD)")
    monthly_schedule: list[MonthlyScheduleItem] = Field(..., description="Month-by-month amortization schedule")
    comparison: dict[str, dict] = Field(
        ...,
        description=(
            "Side-by-side comparison of avalanche and snowball strategies. "
            "Keys are 'avalanche' and 'snowball', each with sub-keys: "
            "'total_interest' (float), 'debt_free_date' (str), 'months_to_payoff' (int)."
        ),
    )


# ---------------------------------------------------------------------------
# Snapshot — aggregate output of all four agents
# ---------------------------------------------------------------------------


class Snapshot(BaseModel):
    debt_analysis: Optional[DebtAnalysis] = Field(None, description="Output of the DebtAnalyzer agent")
    budget_advice: Optional[BudgetAdvice] = Field(None, description="Output of the BudgetCoach agent")
    savings_strategy: Optional[SavingsStrategy] = Field(None, description="Output of the SavingsStrategist agent")
    payoff_plan: Optional[PayoffPlan] = Field(None, description="Output of the PayoffOptimizer agent")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp (UTC) when this snapshot was generated",
    )


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"] = Field(..., description="Message sender role")
    content: str = Field(..., description="Text content of the message")
    agent: Optional[str] = Field(None, description="Which specialist agent produced this message, if applicable")


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="Full conversation history including the new user message")
    session_id: str = Field(..., description="Unique session identifier for state persistence")
    context: Optional[dict] = Field(None, description="Optional extra context (e.g. pre-uploaded financial data summary)")


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------


class TraceEvent(BaseModel):
    type: Literal["agent_start", "tool_call", "tool_result", "agent_complete", "synth"] = Field(
        ..., description="Category of trace event for the 'How I answered this' panel"
    )
    agent: str = Field(..., description="Name of the agent or component that emitted this event")
    payload: dict = Field(..., description="Arbitrary structured data relevant to this event (inputs, outputs, metadata)")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp (UTC) when this event occurred",
    )

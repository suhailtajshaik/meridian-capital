"""Anonymizer — converts raw DataFrames into LLM-safe structured summaries.

Rules:
- Strip all merchant names, account numbers, and PII.
- Aggregate transactions to category-level sums.
- Preserve financial signals (amounts, dates, categories, rates).
- Return a structured dict that the agents can reason about.

Document types detected by column heuristics:
    transactions    — date + description + amount + category columns
    debt_statement  — balance + apr/interest_rate + payment columns
    holdings        — symbol/ticker + value/market_value columns
    amortization    — payment_date + payment + interest + principal + remaining columns
    unknown         — best-effort aggregation
"""
from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Document type detection
# ---------------------------------------------------------------------------

_TRANSACTION_COLS = {"amount", "description", "category", "date"}
_DEBT_COLS = {"balance", "apr", "interest_rate", "monthly_payment", "lender"}
_HOLDINGS_COLS = {"symbol", "ticker", "market_value", "value", "shares"}
_AMORTIZATION_COLS = {"payment_date", "payment", "interest", "principal", "remaining_balance"}


def _detect_doc_type(df: pd.DataFrame) -> str:
    """Infer document type from column names.

    Priority: most-specific matches first. A transactions CSV often has a
    ``balance`` running-total column, so we cannot use ``balance`` alone to
    decide debt_statement — debt_statement must lack ``description`` and
    must carry an APR / payment field.
    """
    cols = set(df.columns)

    # amortization needs at least 3 of its signature columns
    if len(_AMORTIZATION_COLS & cols) >= 3:
        return "amortization"

    # holdings needs both an instrument identifier and a value/quantity column
    if (cols & {"symbol", "ticker"}) and (
        cols & {"value", "market_value", "current_value", "amount_or_value", "shares", "quantity"}
    ):
        return "holdings"

    # transactions: per-row entries with description + amount, ideally + date/category
    has_description = "description" in cols or "merchant" in cols
    if has_description and "amount" in cols:
        return "transactions"

    # debt_statement: account-level summary (no per-row description, has APR or payment)
    has_rate = bool(cols & {"apr", "interest_rate", "rate"})
    has_payment = bool(cols & {"monthly_payment", "min_payment", "payment"})
    has_balance = bool(cols & {"balance", "principal_balance", "outstanding_balance"})
    if not has_description and has_balance and (has_rate or has_payment):
        return "debt_statement"

    # Loose fallback: amount + date without description ⇒ transactions
    if "amount" in cols and any("date" in c for c in cols):
        return "transactions"

    return "unknown"


# ---------------------------------------------------------------------------
# Format-specific summarizers
# ---------------------------------------------------------------------------


def _summarize_transactions(df: pd.DataFrame) -> dict:
    """Aggregate transaction data to category-level sums."""
    summary: dict = {"doc_type": "transactions"}

    # Find amount column
    amount_col = next((c for c in ["amount", "debit", "credit"] if c in df.columns), None)
    category_col = next((c for c in ["category", "type", "merchant_category"] if c in df.columns), None)
    date_col = next((c for c in df.columns if "date" in c), None)

    if amount_col:
        df["_amount"] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)
    else:
        return {**summary, "error": "No amount column found"}

    # Separate debits (negative) and credits (positive)
    debits = df[df["_amount"] < 0].copy()
    credits = df[df["_amount"] > 0].copy()

    summary["total_spent"] = round(float(debits["_amount"].sum()), 2)  # negative
    summary["total_received"] = round(float(credits["_amount"].sum()), 2)
    summary["net_cash_flow"] = round(float(df["_amount"].sum()), 2)
    summary["transaction_count"] = int(len(df))

    # Category breakdown (spending only)
    if category_col and category_col in df.columns:
        cat_sums = (
            debits.groupby(category_col)["_amount"]
            .sum()
            .abs()
            .sort_values(ascending=False)
        )
        summary["spending_by_category"] = {
            k: round(float(v), 2) for k, v in cat_sums.items()
        }
        summary["top_categories"] = list(cat_sums.head(5).index)
    else:
        summary["spending_by_category"] = {}

    # Date range
    if date_col and date_col in df.columns:
        dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
        if not dates.empty:
            summary["period_start"] = dates.min().date().isoformat()
            summary["period_end"] = dates.max().date().isoformat()
            days = (dates.max() - dates.min()).days or 1
            summary["period_days"] = int(days)
            # Annualize to monthly
            monthly_factor = 30.0 / days if days > 0 else 1.0
            summary["estimated_monthly_spend"] = round(
                abs(float(debits["_amount"].sum())) * monthly_factor, 2
            )
            summary["estimated_monthly_income"] = round(
                float(credits["_amount"].sum()) * monthly_factor, 2
            )

    # Balance column (for credit card statements)
    balance_col = next((c for c in ["balance_owed", "balance", "running_balance"] if c in df.columns), None)
    if balance_col:
        last_balance = pd.to_numeric(df[balance_col], errors="coerce").dropna()
        if not last_balance.empty:
            summary["current_balance"] = round(float(last_balance.iloc[-1]), 2)

    return summary


def _summarize_debt_statement(df: pd.DataFrame) -> dict:
    """Extract key fields from a debt/loan statement."""
    summary: dict = {"doc_type": "debt_statement"}

    def _get_first(df: pd.DataFrame, cols: list[str]) -> float | None:
        for c in cols:
            if c in df.columns:
                val = pd.to_numeric(df[c], errors="coerce").dropna()
                if not val.empty:
                    return round(float(val.iloc[0]), 2)
        return None

    def _get_str_first(df: pd.DataFrame, cols: list[str]) -> str | None:
        for c in cols:
            if c in df.columns and not df[c].dropna().empty:
                return str(df[c].dropna().iloc[0])
        return None

    summary["balance"] = _get_first(df, ["balance", "principal_balance", "outstanding_balance"])
    summary["apr"] = _get_first(df, ["apr", "interest_rate", "rate"])
    summary["monthly_payment"] = _get_first(df, ["monthly_payment", "payment", "min_payment"])
    summary["lender"] = _get_str_first(df, ["lender", "servicer", "bank", "institution"])

    date_val = _get_str_first(df, ["statement_date", "next_due", "due_date"])
    if date_val:
        summary["statement_date"] = date_val

    return {k: v for k, v in summary.items() if v is not None}


def _summarize_amortization(df: pd.DataFrame) -> dict:
    """Summarize an amortization schedule."""
    summary: dict = {"doc_type": "amortization"}

    if "remaining_balance" in df.columns:
        balances = pd.to_numeric(df["remaining_balance"], errors="coerce").dropna()
        if not balances.empty:
            summary["current_balance"] = round(float(balances.iloc[0]), 2)
            summary["final_balance"] = round(float(balances.iloc[-1]), 2)
            summary["months_remaining"] = int(len(balances))

    if "payment" in df.columns:
        payments = pd.to_numeric(df["payment"], errors="coerce").dropna()
        if not payments.empty:
            summary["monthly_payment"] = round(float(payments.mode().iloc[0]), 2)
            summary["total_remaining_payments"] = round(float(payments.sum()), 2)

    if "interest" in df.columns:
        interest = pd.to_numeric(df["interest"], errors="coerce").dropna()
        if not interest.empty:
            summary["total_remaining_interest"] = round(float(interest.sum()), 2)

    # Infer APR from first row if possible
    if "remaining_balance" in df.columns and "interest" in df.columns and len(df) > 0:
        try:
            first_balance = float(pd.to_numeric(df["remaining_balance"], errors="coerce").dropna().iloc[0])
            first_interest = float(pd.to_numeric(df["interest"], errors="coerce").dropna().iloc[0])
            if first_balance > 0:
                monthly_rate = first_interest / first_balance
                summary["implied_apr"] = round(monthly_rate * 12 * 100, 2)
        except Exception:
            pass

    return summary


def _summarize_holdings(df: pd.DataFrame) -> dict:
    """Summarize a brokerage holdings statement."""
    summary: dict = {"doc_type": "holdings"}

    value_col = next(
        (c for c in ["market_value", "value", "current_value", "amount_or_value"] if c in df.columns),
        None,
    )
    if value_col:
        values = pd.to_numeric(df[value_col], errors="coerce").dropna()
        summary["total_portfolio_value"] = round(float(values.sum()), 2)
        summary["num_positions"] = int(len(values))

    type_col = next((c for c in ["asset_type", "type", "security_type"] if c in df.columns), None)
    if type_col and type_col in df.columns and value_col:
        type_breakdown = (
            df.groupby(type_col)[value_col]
            .apply(lambda x: pd.to_numeric(x, errors="coerce").sum())
            .sort_values(ascending=False)
        )
        summary["by_asset_type"] = {k: round(float(v), 2) for k, v in type_breakdown.items()}

    return summary


def _summarize_unknown(df: pd.DataFrame) -> dict:
    """Best-effort aggregation for unrecognized documents."""
    summary: dict = {"doc_type": "unknown", "columns": list(df.columns), "rows": int(len(df))}

    # Try to find any numeric columns and report their stats
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols:
        stats: dict = {}
        for col in numeric_cols[:5]:  # limit to first 5
            series = df[col].dropna()
            if not series.empty:
                stats[col] = {
                    "sum": round(float(series.sum()), 2),
                    "mean": round(float(series.mean()), 2),
                    "min": round(float(series.min()), 2),
                    "max": round(float(series.max()), 2),
                }
        summary["numeric_stats"] = stats

    return summary


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def anonymize_for_llm(df: pd.DataFrame, doc_type: str | None = None) -> dict:
    """Convert a raw DataFrame into a PII-free structured summary for the LLM.

    Args:
        df: Parsed and normalized DataFrame.
        doc_type: Optional hint for document type. If None, auto-detected.

    Returns:
        Structured summary dict safe to send to the LLM.
        Keys vary by document type but never include raw merchant names,
        account numbers, or personal identifiers.
    """
    if df.empty:
        return {"doc_type": doc_type or "empty", "error": "No data found in document"}

    detected_type = doc_type or _detect_doc_type(df)

    if detected_type == "transactions":
        return _summarize_transactions(df)
    elif detected_type == "debt_statement":
        return _summarize_debt_statement(df)
    elif detected_type == "amortization":
        return _summarize_amortization(df)
    elif detected_type == "holdings":
        return _summarize_holdings(df)
    else:
        return _summarize_unknown(df)

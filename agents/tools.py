"""Tool registry for the agent layer.

Each function is a stub that returns the canned result string from CHAT_SEED.
Future implementations will wire these to the local document vault (tabular
RAG over indexed bank exports) and small deterministic numeric simulators.
"""
from __future__ import annotations


def query_debt_table(filter: str, sort: str) -> str:
    """Query the persona's active debts. TODO: real implementation against vault."""
    return "3 rows"


def compute_apr_weighted_risk(debts: list[dict]) -> str:
    """Rank debts by APR-weighted risk. TODO: real implementation."""
    return "22.49% top APR"


def rag_retrieve(query: str, k: int = 5) -> str:
    """Retrieve k most relevant rows from the local tabular RAG store. TODO: real."""
    return f"rows 12, 47, 89, 104, 211"


def simulate_avalanche(extra: float, horizon: int) -> str:
    """Simulate avalanche payoff with extra payment over horizon months. TODO: real."""
    return "−$612 interest"


def query_savings_goals(filter: str) -> str:
    """Look up savings goals (e.g., emergency fund coverage). TODO: real."""
    return "1 row · 51% of target"


def project_runway(balance: float, burn: float) -> str:
    """Project months of runway given balance and monthly burn. TODO: real."""
    return "1.6mo runway"


def query_transactions(month: str) -> str:
    """Query transactions for a given month from indexed CSVs. TODO: real."""
    return "127 rows"


def compare_to_budget(by: str) -> str:
    """Compare actuals to budget targets. TODO: real."""
    return "2 categories over"


def project_goal_eta(extra: float) -> str:
    """Project savings goal ETA shift given extra monthly contribution. TODO: real."""
    return "−2mo to kitchen reno"

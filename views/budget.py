"""Budget Advisor view — ported from BudgetView in views.jsx."""

import plotly.graph_objects as go
import streamlit as st

from theme import (
    INFO,
    INK_2,
    INK_3,
    INK_4,
    NEGATIVE,
    POSITIVE,
    WARN,
)
from views.debt import view_header

# ---------------------------------------------------------------------------
# Category-to-color mapping (mirrors design intent)
# ---------------------------------------------------------------------------

_CAT_COLORS: dict[str, str] = {
    "housing":       INFO,
    "groceries":     POSITIVE,
    "dining out":    NEGATIVE,
    "transport":     INK_2,
    "subscriptions": WARN,
    "health":        POSITIVE,
    "shopping":      NEGATIVE,
    "travel":        INK_4,
}


def _cat_color(cat: str) -> str:
    return _CAT_COLORS.get(cat.lower(), INK_3)


# ---------------------------------------------------------------------------
# Plotly defaults helper (local copy to avoid cross-import of private fn)
# ---------------------------------------------------------------------------

def _plotly_defaults() -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=20),
        font=dict(family="Geist, sans-serif", color=INK_3, size=11),
    )


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(persona: dict) -> None:
    budget_rows = persona["budget"]

    total_spent = sum(b["spent"] for b in budget_rows)
    total_budget = sum(b["budget"] for b in budget_rows)
    over_cats = [b for b in budget_rows if b["spent"] > b["budget"]]

    spend_trend = [6800, 7100, 6500, 6900, 7200, 7800, 8200, 7100, 6700, 6500, 6800, total_spent]
    monthly_avg = round(sum(spend_trend) / 12)

    months_labels = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
                     "Jan", "Feb", "Mar", "Apr", "May"]

    # ---------- Header ----------
    view_header(
        "budget",
        "Budget advisor",
        "Spending categorized from transactions. "
        "The agent flags categories trending over budget and suggests reallocations.",
    )

    # ---------- 4-up stats ----------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spent · May", f"${total_spent:,}")
    c2.metric("Budget · May", f"${total_budget:,}")
    c3.metric("Categories over", str(len(over_cats)))
    c4.metric("Monthly avg · 12mo", f"${monthly_avg:,}")

    # ---------- Split row ----------
    col_left, col_right = st.columns([1.6, 1])

    # LEFT: horizontal bar chart — spent vs budgeted
    with col_left:
        st.markdown(
            """
<div class="card" style="margin-bottom:0;">
  <div style="margin-bottom:10px;">
    <div class="card-title">Category breakdown &middot; May</div>
    <div class="card-sub">Spent vs budgeted &middot; markers show targets</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        cats = [b["cat"] for b in budget_rows]
        spents = [b["spent"] for b in budget_rows]
        budgets_vals = [b["budget"] for b in budget_rows]
        colors = [_cat_color(b["cat"]) for b in budget_rows]

        fig_bar = go.Figure()

        # Spent bars
        fig_bar.add_trace(
            go.Bar(
                y=cats,
                x=spents,
                orientation="h",
                marker=dict(color=colors, opacity=0.85),
                text=[f"${v:,}" for v in spents],
                textposition="outside",
                textfont=dict(size=11, color=INK_3),
                showlegend=False,
                name="Spent",
            )
        )

        # Budget markers (scatter as vertical ticks)
        fig_bar.add_trace(
            go.Scatter(
                y=cats,
                x=budgets_vals,
                mode="markers",
                marker=dict(
                    symbol="line-ns",
                    size=14,
                    color=INK_3,
                    line=dict(width=2, color=INK_3),
                ),
                showlegend=False,
                name="Budget",
            )
        )

        fig_bar.update_layout(
            **_plotly_defaults(),
            height=max(260, len(cats) * 36),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, autorange="reversed"),
            bargap=0.35,
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    # RIGHT: spending trend + top leak
    with col_right:
        st.markdown(
            f"""
<div class="card" style="margin-bottom:0;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
    <div class="card-title">Spending trend</div>
    <span class="tag info">Holiday peak Nov&ndash;Dec</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Scatter(
                x=months_labels,
                y=spend_trend,
                mode="lines",
                line=dict(color=WARN, width=2),
                fill="tozeroy",
                fillcolor=f"rgba({int(WARN[1:3],16)},{int(WARN[3:5],16)},{int(WARN[5:7],16)},0.12)",
                showlegend=False,
            )
        )
        fig_trend.update_layout(
            **_plotly_defaults(),
            height=200,
            xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False),
        )
        st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

        # Divider + top leak
        st.markdown(
            f"""
<div style="border-top:1px solid var(--line);margin:4px 0 10px;"></div>
<div style="display:flex;flex-direction:column;gap:8px;">
  <div style="font-size:12px;color:var(--ink-3);letter-spacing:0.06em;text-transform:uppercase;font-weight:500;">
    Top leak
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div>
      <div style="font-size:14px;font-weight:500;">Dining out</div>
      <div style="font-size:12px;color:var(--ink-3);">8 transactions on weekends</div>
    </div>
    <div class="num" style="font-size:18px;color:{NEGATIVE};">+$136</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

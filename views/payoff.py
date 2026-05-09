"""Payoff Optimizer view — ported from PayoffView in views.jsx."""

import plotly.graph_objects as go
import streamlit as st

from theme import (
    INK,
    INK_3,
    INK_4,
    NEGATIVE,
    NEGATIVE_TINT,
    PAYOFF_PALETTE,
    SURFACE,
    SURFACE_2,
)
from views.debt import view_header


# ---------------------------------------------------------------------------
# Plotly defaults helper
# ---------------------------------------------------------------------------

def _plotly_defaults() -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=20),
        font=dict(family="Geist, sans-serif", color=INK_3, size=11),
    )


# ---------------------------------------------------------------------------
# Strategy comparison data
# ---------------------------------------------------------------------------

_COMPARE = [
    {
        "key": "snowball",
        "name": "Snowball",
        "desc": "Smallest balance first — psychological wins",
        "months_to_free": 28,
        "interest": 4180,
        "recommended": False,
    },
    {
        "key": "avalanche",
        "name": "Avalanche",
        "desc": "Highest APR first — mathematical optimum",
        "months_to_free": 25,
        "interest": 3568,
        "recommended": True,
    },
    {
        "key": "min only",
        "name": "Min only",
        "desc": "Pay minimums — slowest, most expensive",
        "months_to_free": 96,
        "interest": 18420,
        "recommended": False,
    },
]


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(persona: dict) -> None:
    # Session state for strategy selection
    st.session_state.setdefault("payoff_strategy", "avalanche")
    strategy: str = st.session_state["payoff_strategy"]

    # ---------- Header ----------
    view_header(
        "payoff",
        "Payoff optimizer",
        "Compare snowball vs avalanche on your real balances. "
        "Adjust monthly extra and watch your debt-free date move.",
    )

    # ---------- 3-up strategy cards ----------
    card_cols = st.columns(3)
    for col, card in zip(card_cols, _COMPARE):
        is_active = strategy == card["key"]
        border_color = INK if is_active else "var(--line)"
        bg_color = SURFACE if is_active else SURFACE_2
        shadow = "0 2px 8px rgba(14,34,56,0.10)" if is_active else "none"
        recommended_badge = (
            '<span class="tag pos" style="margin-left:6px;">Recommended</span>'
            if card["recommended"]
            else ""
        )

        with col:
            st.markdown(
                f"""
<div style="
  padding:16px;
  border-radius:10px;
  background:{bg_color};
  border:1px solid {border_color};
  box-shadow:{shadow};
  margin-bottom:4px;
">
  <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
    <span style="font-size:15px;font-weight:500;">{card["name"]}</span>
    {recommended_badge}
  </div>
  <div style="font-size:12px;color:var(--ink-3);line-height:1.45;margin-bottom:10px;">{card["desc"]}</div>
  <div style="display:flex;justify-content:space-between;align-items:baseline;">
    <div>
      <div style="font-size:11px;color:var(--ink-3);">Debt-free in</div>
      <div class="num" style="font-size:22px;">{card["months_to_free"]}
        <span style="font-size:13px;color:var(--ink-3);">mo</span>
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:11px;color:var(--ink-3);">Total interest</div>
      <div class="num" style="font-size:18px;">${card["interest"]:,}</div>
    </div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
            if st.button(
                f"Select {card['name']}",
                key=f"btn_strategy_{card['key']}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state["payoff_strategy"] = card["key"]
                st.rerun()

    # Re-read strategy after possible rerun
    strategy = st.session_state["payoff_strategy"]

    # ---------- Build payoff series ----------
    eligible_types = {"Credit Card", "Auto", "Student"}
    cards_debts = [d for d in persona["debts"] if d["type"] in eligible_types]

    if strategy == "avalanche":
        ordered = sorted(cards_debts, key=lambda d: d["rate"], reverse=True)
    elif strategy == "snowball":
        ordered = sorted(cards_debts, key=lambda d: d["balance"])
    else:  # min only
        ordered = sorted(cards_debts, key=lambda d: d["balance"])

    month_labels = [
        "Jun '26", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        "Jan '27", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
        "Aug", "Sep", "Oct", "Nov", "Dec", "Jan '28",
    ]
    n_months = len(month_labels)

    series = []
    for i, d in enumerate(ordered):
        values = []
        for m in range(n_months):
            if strategy == "avalanche":
                decay = max(0.0, 1 - m / (8 + i * 4))
            elif strategy == "snowball":
                decay = max(0.0, 1 - m / (6 + i * 5))
            else:  # min only — very slow decay
                decay = max(0.0, 1 - m / 40)
            values.append(round(d["balance"] * decay))
        series.append({"label": d["name"], "values": values})

    # ---------- Projected balances card ----------
    strategy_label = strategy if strategy != "min only" else "min only"
    legend_swatches = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'color:var(--ink-3);font-size:11px;">'
        f'<span style="width:8px;height:8px;border-radius:2px;'
        f'background:{PAYOFF_PALETTE[i % len(PAYOFF_PALETTE)]};'
        f'display:inline-block;flex-shrink:0;"></span>'
        f'{s["label"].split(" — ")[0]}</span>'
        for i, s in enumerate(series)
    )

    st.markdown(
        f"""
<div class="card" style="margin-top:8px;margin-bottom:0;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">
    <div>
      <div class="card-title">Projected balances &middot; {strategy_label}</div>
      <div class="card-sub">+$350/mo on top of minimums</div>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">{legend_swatches}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    fig_payoff = go.Figure()
    for i, s in enumerate(series):
        color = PAYOFF_PALETTE[i % len(PAYOFF_PALETTE)]
        fig_payoff.add_trace(
            go.Scatter(
                x=month_labels,
                y=s["values"],
                name=s["label"].split(" — ")[0],
                mode="lines",
                stackgroup="one",
                line=dict(width=0.5, color=color),
                fillcolor=color,
                showlegend=False,
            )
        )
    fig_payoff.update_layout(
        **_plotly_defaults(),
        height=240,
        xaxis=dict(showgrid=False, zeroline=False, tickangle=-30, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False),
    )
    st.plotly_chart(fig_payoff, use_container_width=True, config={"displayModeBar": False})

    # ---------- Payoff order card ----------
    if strategy == "avalanche":
        order_sub = "By APR (descending)"
    elif strategy == "snowball":
        order_sub = "By balance (ascending)"
    else:
        order_sub = "Minimums only"

    st.markdown(
        f"""
<div class="card" style="margin-top:8px;margin-bottom:0;">
  <div style="margin-bottom:12px;">
    <div class="card-title">Payoff order</div>
    <div class="card-sub">{order_sub}</div>
  </div>
""",
        unsafe_allow_html=True,
    )

    for i, d in enumerate(ordered):
        is_first = i == 0
        row_bg = NEGATIVE_TINT if is_first else SURFACE_2
        circle_bg = NEGATIVE if is_first else INK_4
        pay_first_badge = '<span class="tag neg" style="margin-left:8px;">Pay first</span>' if is_first else ""

        st.markdown(
            f"""
<div class="row-card {'first' if is_first else ''}" style="
  display:flex;align-items:center;gap:14px;
  padding:12px 14px;
  background:{row_bg};
">
  <div class="num" style="
    width:24px;height:24px;
    display:grid;place-items:center;
    font-size:14px;
    background:{circle_bg};
    color:{SURFACE};
    border-radius:999px;
    flex-shrink:0;
  ">{i + 1}</div>
  <div style="flex:1;">
    <div style="font-size:13.5px;font-weight:500;">{d["name"]}</div>
    <div style="font-size:11.5px;color:var(--ink-3);">{d["lender"]} &middot; {d["rate"]:.2f}% APR</div>
  </div>
  <div class="num" style="font-size:16px;">${d["balance"]:,}</div>
  {pay_first_badge}
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

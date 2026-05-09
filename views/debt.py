"""Debt Analyzer view — ported from DebtView in views.jsx."""

import plotly.graph_objects as go
import streamlit as st

from data import AGENT_META
from theme import (
    DEBT_PALETTE,
    INK,
    INK_3,
    NEGATIVE,
    SURFACE,
)

# ---------------------------------------------------------------------------
# Shared header helper (used by all view modules)
# ---------------------------------------------------------------------------

def view_header(agent: str, title: str, sub: str) -> None:
    meta = AGENT_META.get(agent, {})
    color = meta.get("color", "#5C6B82")
    label = meta.get("label", agent.title())
    st.markdown(
        f"""
<div style="margin-bottom:18px;">
  <div class="eyebrow" style="margin-bottom:6px;display:flex;align-items:center;gap:6px;">
    <span class="dot" style="display:inline-block;width:7px;height:7px;border-radius:50%;
      background:{color};margin-right:2px;vertical-align:middle;flex-shrink:0;"></span>
    {label}
  </div>
  <h1 style="margin:0 0 4px 0;">{title}</h1>
  <div style="font-size:13.5px;color:var(--ink-3);max-width:720px;margin-top:4px;">{sub}</div>
</div>
""",
        unsafe_allow_html=True,
    )


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
# Main render
# ---------------------------------------------------------------------------

def render(persona: dict) -> None:
    debts = persona["debts"]

    total = sum(d["balance"] for d in debts)
    min_pay = sum(d["min"] for d in debts)
    yearly_interest = sum(d["balance"] * d["rate"] / 100 for d in debts)
    w_avg_rate = sum(d["rate"] * d["balance"] for d in debts) / total if total else 0

    # ---------- Header ----------
    view_header(
        "debt",
        "Debt analyzer",
        "Rates, balances, and risk across every liability. "
        "The agent flags compounding traps and recommends payoff order.",
    )

    # ---------- 4-up stats ----------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total balance", f"${total:,}")
    c2.metric("Weighted avg rate", f"{w_avg_rate:.2f}%")
    c3.metric("Annual interest", f"${round(yearly_interest):,}")
    c4.metric("Min payments", f"${min_pay:,}")

    # ---------- Build 12-month series ----------
    months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May"]
    series = []
    for i, d in enumerate(debts):
        values = [
            round(d["balance"] * (1 + (11 - m) * 0.005 - i * 0.001))
            for m in range(12)
        ]
        series.append({"label": d["name"], "values": values})

    # ---------- Split row ----------
    col_left, col_right = st.columns([1.6, 1])

    # LEFT: stacked area chart
    with col_left:
        legend_swatches = "".join(
            f'<span style="display:inline-flex;align-items:center;gap:5px;color:var(--ink-3);font-size:11px;">'
            f'<span style="width:8px;height:8px;border-radius:2px;background:{DEBT_PALETTE[i % len(DEBT_PALETTE)]};'
            f'display:inline-block;flex-shrink:0;"></span>'
            f'{s["label"].split(" — ")[0]}</span>'
            for i, s in enumerate(series)
        )
        st.markdown(
            f"""
<div class="card" style="margin-bottom:0;">
  <div style="margin-bottom:10px;">
    <div class="card-title">Balance trajectory &middot; 12 months</div>
    <div class="card-sub">Stacked by liability</div>
  </div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">{legend_swatches}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        fig_area = go.Figure()
        for i, s in enumerate(series):
            color = DEBT_PALETTE[i % len(DEBT_PALETTE)]
            fig_area.add_trace(
                go.Scatter(
                    x=months,
                    y=s["values"],
                    name=s["label"].split(" — ")[0],
                    mode="lines",
                    stackgroup="one",
                    line=dict(width=0.5, color=color),
                    fillcolor=color,
                    showlegend=False,
                )
            )
        fig_area.update_layout(
            **_plotly_defaults(),
            height=220,
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False),
        )
        st.plotly_chart(fig_area, use_container_width=True, config={"displayModeBar": False})

    # RIGHT: donut
    with col_right:
        total_yearly = round(yearly_interest)
        donut_labels = [d["name"].split(" — ")[0] for d in debts]
        donut_values = [round(d["balance"] * d["rate"] / 100) for d in debts]
        donut_colors = [DEBT_PALETTE[i % len(DEBT_PALETTE)] for i in range(len(debts))]

        center_label = f"${round(yearly_interest / 1000)}k"

        st.markdown(
            """
<div class="card" style="margin-bottom:0;">
  <div style="margin-bottom:10px;">
    <div class="card-title">Interest cost mix</div>
    <div class="card-sub">Yearly</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        fig_donut = go.Figure(
            go.Pie(
                labels=donut_labels,
                values=donut_values,
                hole=0.65,
                marker=dict(colors=donut_colors),
                textinfo="none",
                showlegend=True,
            )
        )
        fig_donut.update_layout(
            **_plotly_defaults(),
            height=230,
            annotations=[
                dict(
                    text=f'<b>{center_label}</b><br><span style="font-size:9px;">'
                         f'PER YEAR</span>',
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=16, color=INK, family="Newsreader, Georgia, serif"),
                    align="center",
                )
            ],
            legend=dict(
                font=dict(size=10, color=INK_3),
                orientation="v",
                x=1.02,
                y=0.5,
            ),
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    # ---------- All debts table ----------
    sorted_debts = sorted(debts, key=lambda d: d["rate"], reverse=True)

    def _risk_badge(risk: str) -> str:
        risk_map = {
            "low": ("pos", "Low risk"),
            "medium": ("warn", "Watch"),
            "high": ("neg", "High rate"),
        }
        cls, label = risk_map.get(risk, ("warn", "Watch"))
        return f'<span class="tag {cls}">{label}</span>'

    rows_html = ""
    for d in sorted_debts:
        apr_color = NEGATIVE if d["rate"] >= 18 else INK
        rows_html += (
            f"<tr>"
            f'<td style="font-weight:500;">{d["name"]}</td>'
            f'<td style="color:var(--ink-3);">{d["lender"]}</td>'
            f'<td><span class="tag">{d["type"]}</span></td>'
            f'<td class="num" style="text-align:right;">${d["balance"]:,}</td>'
            f'<td class="num" style="text-align:right;color:{apr_color};">{d["rate"]:.2f}%</td>'
            f'<td class="num" style="text-align:right;">${d["min"]}</td>'
            f'<td>{_risk_badge(d["risk"])}</td>'
            f"</tr>"
        )

    table_html = f"""
<div class="card" style="margin-top:0;">
  <div style="margin-bottom:12px;">
    <div class="card-title">All debts</div>
    <div class="card-sub">Sorted by APR (avalanche order)</div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <thead>
      <tr style="border-bottom:1px solid var(--line);">
        <th style="text-align:left;padding:6px 8px 8px 0;font-size:11px;font-weight:500;color:var(--ink-3);">Liability</th>
        <th style="text-align:left;padding:6px 8px 8px 0;font-size:11px;font-weight:500;color:var(--ink-3);">Lender</th>
        <th style="text-align:left;padding:6px 8px 8px 0;font-size:11px;font-weight:500;color:var(--ink-3);">Type</th>
        <th style="text-align:right;padding:6px 0 8px 8px;font-size:11px;font-weight:500;color:var(--ink-3);">Balance</th>
        <th style="text-align:right;padding:6px 0 8px 8px;font-size:11px;font-weight:500;color:var(--ink-3);">APR</th>
        <th style="text-align:right;padding:6px 0 8px 8px;font-size:11px;font-weight:500;color:var(--ink-3);">Min</th>
        <th style="text-align:left;padding:6px 0 8px 12px;font-size:11px;font-weight:500;color:var(--ink-3);">Risk</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>
"""
    st.markdown(table_html, unsafe_allow_html=True)

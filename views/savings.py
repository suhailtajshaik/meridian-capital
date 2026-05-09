"""Savings view — ported from SavingsView in views.jsx."""

import streamlit as st
import plotly.graph_objects as go

from data import AGENT_META
from theme import (
    POSITIVE, POSITIVE_TINT, INFO,
    WARN, INK, INK_2, INK_3, INK_4,
    LINE, SURFACE_2,
)


def view_header(
    agent: str = "savings",
    title: str = "Savings strategy",
    sub: str = (
        "Goals, timelines, and contribution recommendations. "
        "The agent simulates your savings rate against income and surplus "
        "to project realistic ETAs."
    ),
) -> None:
    meta = AGENT_META.get(agent) if agent else None
    eyebrow_html = ""
    if meta:
        eyebrow_html = (
            f'<div class="eyebrow" style="margin-bottom:6px;display:flex;'
            f'align-items:center;gap:6px;">'
            f'<span class="dot" style="background:{meta["color"]};width:7px;'
            f'height:7px;border-radius:50%;display:inline-block;"></span>'
            f'{meta["label"]}</div>'
        )
    st.markdown(
        f"""
        <div style="margin-bottom:18px;">
          {eyebrow_html}
          <h1 style="font-size:26px;font-weight:500;letter-spacing:-0.01em;
                     color:{INK};margin:0 0 4px 0;">{title}</h1>
          <div style="font-size:13.5px;color:{INK_3};max-width:720px;">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(persona: dict) -> None:
    savings = persona["savings"]

    total = sum(g["balance"] for g in savings)
    target_total = sum(g["target"] for g in savings)
    monthly_contrib = sum(g["monthly"] for g in savings)

    view_header()

    # ---- 3-up stats ----
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="stat"><div class="stat-label">Total saved</div>'
            f'<div class="stat-value">${total:,}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat"><div class="stat-label">Across goals</div>'
            f'<div class="stat-value">${target_total:,}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="stat"><div class="stat-label">Auto-contribute / mo</div>'
            f'<div class="stat-value">${monthly_contrib:,}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ---- Split layout ----
    left, right = st.columns([1.6, 1])

    with left:
        # Savings growth card
        months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
                  "Dec", "Jan", "Feb", "Mar", "Apr", "May"]
        trend = [round(total * (0.7 + i * 0.027)) for i in range(12)]

        st.markdown(
            f"""
            <div class="card" style="margin-bottom:0;">
              <div style="display:flex;justify-content:space-between;
                          align-items:flex-start;margin-bottom:8px;">
                <div>
                  <div class="card-title">Savings growth · 12 months</div>
                  <div class="num" style="font-size:24px;margin-top:2px;">
                    ${total:,}
                  </div>
                </div>
                <span class="tag pos">&#8593; +43% YoY</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=months,
            y=trend,
            mode="lines",
            fill="tozeroy",
            line=dict(color=POSITIVE, width=2),
            fillcolor=POSITIVE_TINT,
            hovertemplate="%{x}: $%{y:,}<extra></extra>",
        ))
        fig.update_layout(
            height=240,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Geist, sans-serif", color=INK_3, size=11),
            margin=dict(l=10, r=10, t=10, b=20),
            xaxis=dict(
                showgrid=False,
                showline=False,
                tickfont=dict(size=10, color=INK_4),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(0,0,0,0.05)",
                showline=False,
                tickprefix="$",
                tickfont=dict(size=10, color=INK_4),
            ),
            showlegend=False,
        )
        # Close off the card div that was opened above
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        # Surplus allocation card
        surplus_rows = [
            {"label": "Emergency fund", "value": 35, "color": POSITIVE},
            {"label": "Roth IRA",        "value": 30, "color": INFO},
            {"label": "Kitchen reno",    "value": 20, "color": INK_2},
            {"label": "Vacation — Japan","value": 10, "color": WARN},
            {"label": "Buffer",          "value":  5, "color": INK_3},
        ]

        bars_html = ""
        for row in surplus_rows:
            bars_html += f"""
            <div style="margin-bottom:10px;">
              <div style="display:flex;justify-content:space-between;
                          align-items:center;margin-bottom:4px;">
                <span style="font-size:12.5px;color:{INK_2};">{row["label"]}</span>
                <span style="font-size:12px;color:{INK_3};font-weight:500;">
                  {row["value"]}%
                </span>
              </div>
              <div class="bar-track">
                <div style="width:{row['value']}%;height:100%;
                             background:{row['color']};border-radius:999px;"></div>
              </div>
            </div>
            """

        st.markdown(
            f"""
            <div class="card" style="margin-bottom:0;">
              <div style="margin-bottom:12px;">
                <div class="card-title">Surplus allocation</div>
                <div class="card-sub">Where each $100 of surplus goes</div>
              </div>
              {bars_html}
              <div style="border-top:1px solid var(--line);margin:12px 0 10px;"></div>
              <div style="font-size:12.5px;color:{INK_3};line-height:1.55;">
                Recommended: shift <strong style="color:{INK};">+10%</strong>
                into emergency fund until 6-month target is reached,
                then rebalance.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ---- Goals card ----
    # Build all goal cards as one HTML block
    goal_cards_html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">'
    for g in savings:
        pct = (g["balance"] / g["target"]) * 100
        pct_int = round(pct)
        bar_width = min(100, pct)
        goal_cards_html += f"""
        <div style="padding:16px;border:1px solid var(--line);border-radius:10px;
                    background:{SURFACE_2};">
          <div style="display:flex;justify-content:space-between;
                      align-items:flex-start;">
            <div>
              <div style="font-size:14.5px;font-weight:500;color:{INK};">
                {g["name"]}
              </div>
              <div style="font-size:11.5px;color:{INK_3};margin-top:2px;">
                {g["category"]} · ${g["monthly"]}/mo auto
              </div>
            </div>
            <span class="tag info">ETA {g["eta"]}</span>
          </div>
          <div style="display:flex;align-items:baseline;gap:6px;margin-top:10px;">
            <span class="num" style="font-size:22px;">${g["balance"]:,}</span>
            <span style="font-size:12px;color:{INK_3};">of ${g["target"]:,}</span>
            <span class="tag pos" style="margin-left:auto;">{pct_int}%</span>
          </div>
          <div class="bar-track" style="margin-top:8px;">
            <div class="bar-fill pos" style="width:{bar_width:.1f}%;"></div>
          </div>
        </div>
        """
    goal_cards_html += "</div>"

    st.markdown(
        f'<div class="card" style="margin-bottom:16px;">'
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:center;margin-bottom:14px;">'
        f'<div class="card-title" style="margin-bottom:0;">Goals</div>'
        f'<span class="tag">Sort by ETA</span></div>'
        f'{goal_cards_html}</div>',
        unsafe_allow_html=True,
    )

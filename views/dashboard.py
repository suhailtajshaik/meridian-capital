"""Dashboard view — hero stats, net worth chart, agent insights, transactions, goals."""

import streamlit as st
import plotly.graph_objects as go

from theme import (
    INK, INK_2, INK_3, INK_4,
    LINE,
    POSITIVE,
    NEGATIVE,
    DONUT_PALETTE,
)
from data import AGENT_META


# ---------------------------------------------------------------------------
# Helper: Plotly base layout defaults
# ---------------------------------------------------------------------------

def _base_layout(**overrides):
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Geist, sans-serif", color=INK_3, size=11),
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
    )
    layout.update(overrides)
    return layout


def _hidden_axes():
    return dict(
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        showline=False,
    )


# ---------------------------------------------------------------------------
# Sparkline chart
# ---------------------------------------------------------------------------

def _hex_to_rgba(color: str, alpha: float) -> str:
    """Plotly only accepts 6-char hex or rgba(); convert if needed."""
    if color.startswith("#") and len(color) == 7:
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
    if color.startswith("rgb(") and not color.startswith("rgba("):
        return color.replace("rgb(", "rgba(").replace(")", f", {alpha})")
    return color


def _sparkline(data, color, height=50):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=data,
        mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=_hex_to_rgba(color, 0.10),
        hoverinfo="skip",
    ))
    fig.update_layout(
        **_base_layout(height=height),
        xaxis=_hidden_axes(),
        yaxis=_hidden_axes(),
    )
    return fig


# ---------------------------------------------------------------------------
# Net worth area chart
# ---------------------------------------------------------------------------

def _net_worth_chart(data, labels, height=280):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels,
        y=data,
        mode="lines",
        line=dict(color=INK, width=2),
        fill="tozeroy",
        fillcolor="rgba(14, 34, 56, 0.07)",
        hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(height=height),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(size=10, color=INK_4),
            tickvals=list(range(len(labels))),
            ticktext=labels,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(230, 226, 216, 0.6)",
            zeroline=False,
            showline=False,
            tickfont=dict(size=10, color=INK_4),
            tickformat="$,.0f",
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Donut chart
# ---------------------------------------------------------------------------

def _donut_chart(slices, labels, pct_label, height=200):
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels,
        values=slices,
        hole=0.72,
        marker=dict(colors=DONUT_PALETTE[:len(slices)], line=dict(color="rgba(0,0,0,0)", width=0)),
        textinfo="none",
        hovertemplate="%{label}: $%{value:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(
            height=height,
            showlegend=True,
            legend=dict(
                orientation="v",
                font=dict(size=10, color=INK_3),
                x=1.02, y=0.5,
            ),
        ),
        annotations=[
            dict(
                text=f"<b>{pct_label}%</b><br><span style='font-size:9px'> OF BUDGET</span>",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(family="Newsreader, Georgia, serif", size=20, color=INK),
                align="center",
            )
        ],
    )
    return fig


# ---------------------------------------------------------------------------
# Agent insight card (pure HTML)
# ---------------------------------------------------------------------------

def _agent_insight_card_html(agent, headline, body, metric, metric_sub, action):
    meta = AGENT_META[agent]
    color = meta["color"]
    label = meta["label"].upper()
    return f"""
<div class="card" style="display:flex;flex-direction:column;gap:10px;height:100%;">
  <div style="display:flex;align-items:center;gap:8px;">
    <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0;"></span>
    <span style="font-size:11px;color:{INK_3};letter-spacing:0.06em;text-transform:uppercase;font-weight:500;">{label}</span>
    <span style="margin-left:auto;font-size:10.5px;color:{INK_4};">just now</span>
  </div>
  <div style="font-size:15px;font-weight:500;line-height:1.35;color:{INK};">{headline}</div>
  <div style="font-size:12.5px;color:{INK_3};line-height:1.5;">{body}</div>
  <div style="display:flex;align-items:baseline;gap:8px;padding-top:4px;">
    <span class="num" style="font-size:22px;color:{color};">{metric}</span>
    <span style="font-size:11px;color:{INK_3};">{metric_sub}</span>
  </div>
  <div style="font-size:12px;color:{INK_2};padding-top:2px;">{action} →</div>
</div>
"""


# ---------------------------------------------------------------------------
# Transaction table (HTML)
# ---------------------------------------------------------------------------

def _transactions_table_html(transactions):
    rows = []
    for t in transactions:
        amount = t["amount"]
        if amount > 0:
            amount_str = f'+${abs(amount):,.2f}'
            amount_color = POSITIVE
        else:
            amount_str = f'−${abs(amount):,.2f}'
            amount_color = INK

        rows.append(f"""
  <tr>
    <td style="font-size:12px;color:{INK_3};white-space:nowrap;">{t['date']}</td>
    <td style="font-size:13px;">{t['merchant']}</td>
    <td><span class="tag">{t['cat']}</span></td>
    <td style="font-size:12px;color:{INK_3};">{t['source']}</td>
    <td class="num" style="text-align:right;font-size:13px;color:{amount_color};">{amount_str}</td>
  </tr>""")

    return f"""
<table style="width:100%;border-collapse:collapse;font-family:Geist,sans-serif;">
  <thead>
    <tr style="border-bottom:1px solid {LINE};">
      <th style="text-align:left;font-size:11px;font-weight:500;color:{INK_3};padding:0 8px 8px 0;width:70px;">Date</th>
      <th style="text-align:left;font-size:11px;font-weight:500;color:{INK_3};padding:0 8px 8px 0;">Merchant</th>
      <th style="text-align:left;font-size:11px;font-weight:500;color:{INK_3};padding:0 8px 8px 0;">Category</th>
      <th style="text-align:left;font-size:11px;font-weight:500;color:{INK_3};padding:0 8px 8px 0;">Source</th>
      <th style="text-align:right;font-size:11px;font-weight:500;color:{INK_3};padding:0 0 8px 0;">Amount</th>
    </tr>
  </thead>
  <tbody>
    {''.join(rows)}
  </tbody>
</table>
"""


# ---------------------------------------------------------------------------
# Savings goal row (HTML)
# ---------------------------------------------------------------------------

def _goal_row_html(goal):
    pct = min(100, round((goal["balance"] / goal["target"]) * 100))
    return f"""
<div style="padding:12px 0;border-bottom:1px solid {LINE};">
  <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">
    <div>
      <div style="font-size:13.5px;font-weight:500;">{goal['name']}</div>
      <div style="font-size:11px;color:{INK_3};">{goal['category']} · ETA {goal['eta']}</div>
    </div>
    <div style="text-align:right;">
      <div class="num" style="font-size:15px;">${goal['balance']:,}</div>
      <div style="font-size:11px;color:{INK_3};">of ${goal['target']:,}</div>
    </div>
  </div>
  <div class="bar-track">
    <div class="bar-fill pos" style="width:{pct}%;"></div>
  </div>
</div>
"""


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render(persona):
    months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May"]

    total_debt = sum(d["balance"] for d in persona["debts"])
    total_savings = sum(g["balance"] for g in persona["savings"])
    total_spent = sum(b["spent"] for b in persona["budget"])
    total_budget = sum(b["budget"] for b in persona["budget"])
    pct_of_budget = round((total_spent / total_budget) * 100)

    # -----------------------------------------------------------------------
    # 1. Greeting row
    # -----------------------------------------------------------------------
    st.markdown(
        f"""
<div class="eyebrow">Friday · May 9</div>
<h1 class="hero-title" style="font-family:var(--font-num);font-size:30px;font-weight:400;letter-spacing:-0.02em;">
  Good morning, <em style="font-style:italic;color:{INK_2};">Maya</em>.
</h1>
<div class="hero-sub">
  Your finances are <span class="pos" style="color:{POSITIVE};font-weight:500;">on track</span>
  &mdash; net worth up $4.3k since last month.
</div>
""",
        unsafe_allow_html=True,
    )

    # Buttons row
    btn_col_spacer, btn_col_ask, btn_col_add = st.columns([5, 2, 2])
    with btn_col_ask:
        if st.button("Ask advisor", key="dash_ask_advisor", use_container_width=True):
            st.session_state.view = "chat"
            st.rerun()
    with btn_col_add:
        if st.button("Add document", key="dash_add_document", type="primary", use_container_width=True):
            st.session_state.view = "documents"
            st.rerun()

    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 2. 4-up hero stats
    # -----------------------------------------------------------------------
    debt_spark = [355000, 354000, 352000, 351200, 350800, 351400,
                  351900, 351500, 350500, 350800, 350400, total_debt]
    savings_spark = [16000, 16800, 17400, 18200, 19000, 19500,
                     20100, 20800, 21100, 21600, 21900, total_savings]
    cashflow_spark = [3100, 2800, 3200, 2900, 2750, 2400, 2840]

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            label="Net worth",
            value=f"${persona['net_worth']:,}.40",
            delta=f"+${persona['net_worth_delta']:,} this month",
        )
        st.plotly_chart(
            _sparkline(persona["net_worth_series"], INK),
            config={"displayModeBar": False},
            use_container_width=True,
            key="spark_networth",
        )

    with c2:
        st.metric(
            label="Total debt",
            value=f"${total_debt:,}",
            delta=f"−$1,240 this month",
            delta_color="inverse",
        )
        st.plotly_chart(
            _sparkline(debt_spark, NEGATIVE),
            config={"displayModeBar": False},
            use_container_width=True,
            key="spark_debt",
        )

    with c3:
        st.metric(
            label="Total savings",
            value=f"${total_savings:,}",
            delta=f"+$1,933 this month",
        )
        st.plotly_chart(
            _sparkline(savings_spark, POSITIVE),
            config={"displayModeBar": False},
            use_container_width=True,
            key="spark_savings",
        )

    with c4:
        st.metric(
            label="Cash flow",
            value=f"${persona['cash_flow']:,}",
            delta=f"−${abs(persona['cash_flow_delta']):,} vs last month",
            delta_color="inverse",
        )
        st.plotly_chart(
            _sparkline(cashflow_spark, INK_2),
            config={"displayModeBar": False},
            use_container_width=True,
            key="spark_cashflow",
        )

    # -----------------------------------------------------------------------
    # 3. Split row: Net worth chart (left) + May spending donut (right)
    # -----------------------------------------------------------------------
    left_col, right_col = st.columns([1.6, 1])

    with left_col:
        # Period selector buttons (visual only)
        period_html = " ".join(
            f'<button style="padding:3px 8px;font-size:11.5px;border-radius:6px;'
            f'background:{"var(--bg)" if p == "1Y" else "transparent"};'
            f'border:{"1px solid var(--line)" if p == "1Y" else "none"};'
            f'color:var(--ink);cursor:default;font-family:var(--font-ui);">{p}</button>'
            for p in ["1M", "3M", "6M", "1Y", "All"]
        )
        st.markdown(
            f"""
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
    <div>
      <div class="card-title">Net worth · 12 months</div>
      <div class="num" style="font-size:26px;margin-top:2px;">${persona['net_worth']:,}</div>
    </div>
    <div style="display:flex;gap:4px;">{period_html}</div>
  </div>
""",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            _net_worth_chart(persona["net_worth_series"], months, height=280),
            config={"displayModeBar": False},
            use_container_width=True,
            key="chart_networth",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        tag_cls = "warn" if total_spent > total_budget else "pos"
        if total_spent > total_budget:
            tag_text = f"{round(((total_spent - total_budget) / total_budget) * 100)}% over"
        else:
            tag_text = f"{round(((total_budget - total_spent) / total_budget) * 100)}% under"

        budget_cats = [b["cat"] for b in persona["budget"][:6]]
        budget_vals = [b["spent"] for b in persona["budget"][:6]]

        st.markdown(
            f"""
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
    <div>
      <div class="card-title">May spending</div>
      <div class="num" style="font-size:26px;margin-top:2px;">
        ${total_spent:,}
        <span style="font-size:14px;color:{INK_3};font-family:var(--font-ui);margin-left:4px;">/ ${total_budget:,}</span>
      </div>
    </div>
    <span class="tag {tag_cls}">{tag_text}</span>
  </div>
""",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            _donut_chart(budget_vals, budget_cats, pct_of_budget, height=220),
            config={"displayModeBar": False},
            use_container_width=True,
            key="chart_donut",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 4. Agent insights
    # -----------------------------------------------------------------------
    st.markdown(
        f"""
<div style="margin-top:24px;margin-bottom:12px;">
  <h2 style="margin-bottom:2px;">What your advisors noticed</h2>
  <div style="font-size:12.5px;color:{INK_3};">Updated automatically as new transactions are ingested</div>
</div>
""",
        unsafe_allow_html=True,
    )

    insights = [
        dict(
            agent="debt",
            headline="Two cards above 19% APR",
            body="Sapphire &amp; Quicksilver are accruing $122/mo in interest combined. Together they're 1.9% of your debt but 18% of your interest cost.",
            metric="$122/mo",
            metric_sub="interest leak",
            action="See debt analysis",
        ),
        dict(
            agent="payoff",
            headline="Avalanche saves $612",
            body="Switch from snowball to avalanche on your two cards &mdash; same monthly outlay, debt-free 3 months sooner.",
            metric="−3 mo",
            metric_sub="time to debt-free",
            action="Compare strategies",
        ),
        dict(
            agent="savings",
            headline="Emergency fund at 51%",
            body="You're $8.8k away from a 6-month buffer. Auto-saving $400/mo gets you there by Mar 2028.",
            metric="51%",
            metric_sub="of 6-month target",
            action="Adjust goal",
        ),
        dict(
            agent="budget",
            headline="Dining $136 over budget",
            body="Your dining spend is on track to exceed budget by $190 if the trend holds. 8 transactions on weekends.",
            metric="+39%",
            metric_sub="vs your budget",
            action="See breakdown",
        ),
    ]

    ins_cols = st.columns(4)
    for col, ins in zip(ins_cols, insights):
        with col:
            st.markdown(
                _agent_insight_card_html(
                    ins["agent"],
                    ins["headline"],
                    ins["body"],
                    ins["metric"],
                    ins["metric_sub"],
                    ins["action"],
                ),
                unsafe_allow_html=True,
            )

    # -----------------------------------------------------------------------
    # 5. Recent activity (left) + Savings goals (right)
    # -----------------------------------------------------------------------
    act_col, goal_col = st.columns([1.6, 1])

    with act_col:
        st.markdown(
            f"""
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;">
    <div>
      <div class="card-title">Recent activity</div>
      <div class="card-sub">Across 4 connected accounts</div>
    </div>
    <span style="font-size:12px;color:{INK_3};">View all</span>
  </div>
  {_transactions_table_html(persona['transactions'])}
</div>
""",
            unsafe_allow_html=True,
        )

    with goal_col:
        goal_rows_html = "".join(_goal_row_html(g) for g in persona["savings"])
        st.markdown(
            f"""
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;">
    <div>
      <div class="card-title">Savings goals</div>
      <div class="card-sub">${total_savings:,} across {len(persona['savings'])} goals</div>
    </div>
  </div>
  {goal_rows_html}
</div>
""",
            unsafe_allow_html=True,
        )

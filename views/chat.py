"""Chat view — full-page port of ChatPanel + Trace + RoutingPill + PayoffActionCard."""

import re
import streamlit as st

from data import AGENT_META, CHAT_SEED, FOLLOWUP_RESPONSE
from theme import (
    INK, INK_2, INK_3, INK_4,
    LINE, SURFACE, SURFACE_2,
    INFO,
    AGENT_SUPERVISOR,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bold(text: str) -> str:
    """Convert **word** markdown to <strong>word</strong>."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def _agent_color(agent_key: str) -> str:
    meta = AGENT_META.get(agent_key)
    return meta["color"] if meta else INK_3


def _agent_label(agent_key: str) -> str:
    meta = AGENT_META.get(agent_key)
    return meta["label"] if meta else agent_key.title()


# ---------------------------------------------------------------------------
# Trace renderer
# ---------------------------------------------------------------------------

def render_trace(trace: dict) -> str:
    """Return inner HTML for the trace timeline."""
    steps = trace.get("steps", [])
    total_ms = trace.get("total_ms", 0)

    rows_html = ""
    for i, s in enumerate(steps):
        kind = s.get("kind", "agent")
        if kind == "supervisor":
            color = INK
            label = "Supervisor"
        elif kind == "synth":
            color = INK_2
            label = "Synthesizer"
        else:
            agent_key = s.get("agent", "")
            color = _agent_color(agent_key)
            label = _agent_label(agent_key)

        # title line
        title_html = ""
        if s.get("title"):
            title_html = (
                f'<div style="font-size:12px;color:{INK_2};margin-top:2px;">'
                f'{s["title"]}</div>'
            )

        # detail bullets
        details_html = ""
        if s.get("details"):
            bullets = "".join(
                f'<li style="font-size:11.5px;color:{INK_3};padding-left:10px;'
                f'position:relative;list-style:none;">'
                f'<span style="position:absolute;left:0;top:7px;width:4px;height:1px;'
                f'background:{INK_4};display:inline-block;"></span>{d}</li>'
                for d in s["details"]
            )
            details_html = (
                f'<ul style="margin:4px 0 0;padding:0;display:flex;'
                f'flex-direction:column;gap:2px;">{bullets}</ul>'
            )

        # route pills
        routes_html = ""
        if s.get("routes"):
            pills = "".join(
                f'<span style="display:inline-flex;align-items:center;gap:4px;'
                f'font-size:10.5px;padding:2px 6px;border-radius:4px;'
                f'background:{SURFACE};border:1px solid {LINE};color:{INK_2};">'
                f'<span style="width:5px;height:5px;border-radius:999px;'
                f'background:{_agent_color(r)};display:inline-block;"></span>'
                f'{_agent_label(r)}</span>'
                for r in s["routes"]
            )
            routes_html = (
                f'<div style="display:flex;gap:4px;margin-top:6px;flex-wrap:wrap;">'
                f'{pills}</div>'
            )

        # tool chips
        tools_html = ""
        if s.get("tools"):
            chips = "".join(
                f'<div style="font-family:var(--font-mono);font-size:10.5px;'
                f'color:{INK_2};padding:4px 8px;border-radius:4px;'
                f'background:{SURFACE};border:1px solid {LINE};'
                f'display:flex;justify-content:space-between;gap:8px;margin-top:3px;">'
                f'<span>'
                f'<span style="font-weight:500;color:{color};">{t["name"]}</span>'
                f'(<span style="color:{INK_3};">{t["args"]}</span>)'
                f'</span>'
                f'<span style="color:{INK_4};">&#8594; {t["result"]}</span>'
                f'</div>'
                for t in s["tools"]
            )
            tools_html = (
                f'<div style="display:flex;flex-direction:column;gap:0;'
                f'margin-top:6px;">{chips}</div>'
            )

        # conclusion
        conclusion_html = ""
        if s.get("conclusion"):
            conclusion_html = (
                f'<div style="font-size:11.5px;color:{INK_2};margin-top:6px;'
                f'font-style:italic;">"{s["conclusion"]}"</div>'
            )

        # summary
        summary_html = ""
        if s.get("summary"):
            summary_html = (
                f'<div style="font-size:11.5px;color:{INK_2};margin-top:2px;">'
                f'{s["summary"]}</div>'
            )

        ms = s.get("ms", "")
        rows_html += f"""
        <div style="display:grid;grid-template-columns:16px 1fr auto;gap:10px;
                    padding:10px 12px;border-bottom:1px solid {LINE};">
          <div style="padding-top:4px;">
            <span style="width:8px;height:8px;border-radius:999px;
                         background:{color};display:block;"></span>
          </div>
          <div>
            <div style="font-size:12px;font-weight:500;color:{INK};">{label}</div>
            {title_html}
            {details_html}
            {routes_html}
            {tools_html}
            {conclusion_html}
            {summary_html}
          </div>
          <div style="font-family:var(--font-mono);font-size:10px;
                      color:{INK_4};padding-top:4px;white-space:nowrap;">{ms}ms</div>
        </div>
        """

    header_html = (
        f'<div style="padding:8px 12px;border-bottom:1px solid {LINE};'
        f'font-size:10.5px;color:{INK_3};letter-spacing:0.06em;'
        f'text-transform:uppercase;display:flex;justify-content:space-between;">'
        f'<span>Orchestration trace</span>'
        f'<span style="font-family:var(--font-mono);font-size:10px;">'
        f'{total_ms / 1000:.2f}s total</span></div>'
    )

    return (
        f'<div style="border:1px solid {LINE};border-radius:8px;'
        f'background:{SURFACE_2};margin-top:8px;overflow:hidden;">'
        f'{header_html}{rows_html}'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Message renderers
# ---------------------------------------------------------------------------

def _render_user_msg(text: str) -> None:
    st.markdown(
        f'<div style="text-align:right;margin:8px 0;">'
        f'<span class="msg-user">{text}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_routing_pill(routing: list) -> None:
    agents_html = ""
    for i, a in enumerate(routing):
        dot = (
            f'<span class="dot" style="background:{_agent_color(a)};"></span>'
        )
        sep = (
            f'<span style="color:{INK_3};margin-left:4px;margin-right:2px;">·</span>'
            if i < len(routing) - 1
            else ""
        )
        agents_html += (
            f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'margin-right:4px;">'
            f'{dot}'
            f'<strong style="font-weight:500;">{_agent_label(a)}</strong>'
            f'{sep}</span>'
        )

    st.markdown(
        f'<div style="display:flex;justify-content:center;margin:8px 0;">'
        f'<div class="routing-pill">'
        f'<strong>Supervisor routed to</strong> {agents_html}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _render_payoff_card(structured: dict) -> str:
    target = structured.get("target", "")
    amount = structured.get("amount", 0)
    interest_saved = structured.get("interest_saved", 0)
    return (
        f'<div class="payoff-card">'
        f'<div class="eyebrow-sm">RECOMMENDED ACTION</div>'
        f'<div style="display:flex;align-items:baseline;'
        f'justify-content:space-between;gap:12px;">'
        f'<div>'
        f'<div style="font-size:13px;color:{INK_3};">Pay toward</div>'
        f'<div class="target">{target}</div>'
        f'</div>'
        f'<div style="text-align:right;">'
        f'<div class="amount num">${amount:,}</div>'
        f'<div class="saved">&#8722;${interest_saved} interest</div>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex;gap:6px;margin-top:10px;">'
        f'<button style="padding:5px 10px;font-size:12px;border-radius:7px;'
        f'background:{INK};color:{SURFACE};border:none;cursor:pointer;'
        f'font-family:var(--font-ui);font-weight:500;">Schedule transfer</button>'
        f'<button style="padding:5px 10px;font-size:12px;border-radius:7px;'
        f'background:transparent;color:{INK};border:1px solid {LINE};cursor:pointer;'
        f'font-family:var(--font-ui);">See full plan</button>'
        f'</div>'
        f'</div>'
    )


def _render_agent_msg(m: dict, msg_idx: int) -> None:
    agent_key = m.get("agent", "supervisor")
    color = _agent_color(agent_key)
    label = _agent_label(agent_key)

    chip_html = (
        f'<div class="agent-chip">'
        f'<span class="dot" style="background:{color};"></span>'
        f'{label}</div>'
    )

    body_text = _bold(m.get("text", ""))

    payoff_html = ""
    structured = m.get("structured", {})
    if structured.get("kind") == "recommend-payoff":
        payoff_html = _render_payoff_card(structured)

    st.markdown(
        f'<div style="margin:8px 0;">'
        f'{chip_html}'
        f'<div class="msg-agent-body">'
        f'{body_text}'
        f'{payoff_html}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Action suggestion pills (interactive — must use st.button)
    actions = m.get("actions", [])
    if actions:
        cols = st.columns(len(actions))
        for j, (col, action) in enumerate(zip(cols, actions)):
            with col:
                if st.button(action, key=f"action_{msg_idx}_{j}"):
                    send(action)

    # Trace expander
    trace = m.get("trace")
    if trace:
        n_agents = len({
            s["agent"]
            for s in trace.get("steps", [])
            if s.get("kind") == "agent"
        })
        total_s = trace.get("total_ms", 0) / 1000
        n_tools = trace.get("tool_count", 0)
        expander_label = (
            f"⚡ {n_agents} agent{'s' if n_agents != 1 else ''} · "
            f"{total_s:.1f}s · {n_tools} tool call{'s' if n_tools != 1 else ''} "
            f"— How I answered this"
        )
        with st.expander(expander_label, expanded=False):
            st.markdown(render_trace(trace), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# send helper
# ---------------------------------------------------------------------------

def send(text: str) -> None:
    """Append user message + canned response, then rerun."""
    thread: list = st.session_state["thread"]
    thread.append({"role": "user", "text": text})
    for msg in FOLLOWUP_RESPONSE:
        thread.append(msg)
    st.session_state["thread"] = thread
    st.rerun()


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(persona: dict) -> None:
    # Initialise thread once
    if "thread" not in st.session_state:
        st.session_state["thread"] = list(CHAT_SEED)

    # ---- Header bar ----
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
          <div style="width:38px;height:38px;border-radius:50%;flex-shrink:0;
                      background:linear-gradient(135deg, {AGENT_SUPERVISOR}, {INFO});
                      "></div>
          <div>
            <div style="font-size:15px;font-weight:500;color:{INK};">Advisor</div>
            <div style="font-size:12px;color:{INK_3};">
              Supervisor + 4 specialists · context: 6 docs
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Privacy banner ----
    st.markdown(
        f'<div style="text-align:center;margin-bottom:14px;">'
        f'<span style="font-size:10.5px;color:{INK_4};letter-spacing:0.06em;">'
        f'🔒 ON-DEVICE · NOTHING LEAVES THIS MACHINE</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ---- Message stream ----
    thread: list = st.session_state["thread"]
    for i, m in enumerate(thread):
        role = m.get("role")
        if role == "user":
            _render_user_msg(m.get("text", ""))
        elif role == "supervisor" and m.get("routing"):
            _render_routing_pill(m["routing"])
        else:
            _render_agent_msg(m, i)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ---- Suggestion chips ----
    suggestions = [
        "How am I doing this month?",
        "When can I afford the kitchen reno?",
        "What if I lose my job?",
        "Show me my biggest leak",
    ]
    s_cols = st.columns(len(suggestions))
    for j, (col, text) in enumerate(zip(s_cols, suggestions)):
        with col:
            if st.button(text, key=f"sugg_{j}"):
                send(text)

    # ---- Chat input ----
    user_input = st.chat_input("Ask anything about your money…")
    if user_input:
        send(user_input)

    # ---- PII notice ----
    st.markdown(
        f'<div style="text-align:center;margin-top:6px;">'
        f'<span style="font-size:10.5px;color:{INK_4};">'
        f'🛡 Account numbers redacted before retrieval · No PII leaves your vault'
        f'</span></div>',
        unsafe_allow_html=True,
    )

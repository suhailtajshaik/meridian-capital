"""Meridian — Personal finance advisor (Streamlit hackathon demo).

Multi-agent financial advisor: supervisor + Debt / Savings / Budget / Payoff
sub-agents over a local-first document vault. This file is the shell:
sidebar nav, view routing, and the top vault-status pill. View modules in
`views/` do the heavy lifting.
"""
import streamlit as st

from data import PERSONA, AGENT_META
from theme import apply_theme, INK, INK_3, POSITIVE, AGENT_DEBT, AGENT_SAVINGS, AGENT_BUDGET, AGENT_PAYOFF

from views import dashboard, documents, debt, savings, budget, payoff, settings, chat

st.set_page_config(
    page_title="Meridian — Personal Finance Advisor",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

# ---- Routing state ----
if "view" not in st.session_state:
    st.session_state.view = "dashboard"


def _nav(view_id: str):
    st.session_state.view = view_id


# ---- Sidebar ----
def sidebar():
    p = PERSONA
    n_docs = len(p["documents"])

    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
              <div class="brand-mark">m</div>
              <div>
                <div class="brand-name">Meridian</div>
                <div class="brand-sub">Personal finance · v0.4</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_items = [
            ("Overview", [
                ("dashboard", "Dashboard", None),
                ("documents", f"Documents", str(n_docs)),
                ("chat",      "Advisor chat", None),
            ]),
            ("Advisors", [
                ("debt",    "Debt Analyzer",    AGENT_DEBT),
                ("savings", "Savings Strategy", AGENT_SAVINGS),
                ("budget",  "Budget Advisor",   AGENT_BUDGET),
                ("payoff",  "Payoff Optimizer", AGENT_PAYOFF),
            ]),
            ("System", [
                ("settings", "Settings & security", None),
            ]),
        ]

        for section, items in nav_items:
            st.markdown(f'<div class="nav-section-label">{section}</div>',
                        unsafe_allow_html=True)
            for view_id, label, hint in items:
                is_active = st.session_state.view == view_id
                # Decorate label with a colored dot for advisors
                if section == "Advisors" and hint:
                    icon = f"●"
                    btn_label = f"{icon}  {label}"
                elif section == "Overview" and view_id == "documents" and hint:
                    btn_label = f"{label}   ({hint})"
                else:
                    btn_label = label

                clicked = st.button(
                    btn_label,
                    key=f"nav_{view_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                )
                if clicked and not is_active:
                    _nav(view_id)
                    st.rerun()

        # Vault status pill
        st.markdown(
            f"""
            <div style="margin-top: 18px;">
              <span class="vault-pill"><span class="dot"></span>Local vault</span>
            </div>
            <div class="user-card">
              <div class="avatar">{p["initials"]}</div>
              <div style="flex:1; min-width:0;">
                <div class="user-name">{p["name"]}</div>
                <div class="user-meta">🔒 Local vault · on-device</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---- Main router ----
sidebar()

VIEWS = {
    "dashboard": dashboard.render,
    "documents": documents.render,
    "chat":      chat.render,
    "debt":      debt.render,
    "savings":   savings.render,
    "budget":    budget.render,
    "payoff":    payoff.render,
    "settings":  settings.render,
}

view_fn = VIEWS.get(st.session_state.view, dashboard.render)
view_fn(PERSONA)

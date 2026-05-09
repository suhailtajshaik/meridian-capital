"""Streamlit theming — bank-grade aesthetic ported from the design's tokens.css.

Inject `apply_theme()` at the top of streamlit_app.py. CSS classes/colors
referenced here are used by every view module.
"""
import streamlit as st

# ---- Color tokens (mirrors css/tokens.css) ----
BG          = "#F6F4EF"
SURFACE     = "#FFFFFF"
SURFACE_2   = "#FBFAF6"
LINE        = "#E6E2D8"
LINE_STRONG = "#D7D2C3"

INK   = "#0E2238"
INK_2 = "#2A3B53"
INK_3 = "#5C6B82"
INK_4 = "#8E99AC"

POSITIVE      = "#1E6B52"
POSITIVE_TINT = "#E5EFEA"
NEGATIVE      = "#9E3A37"
NEGATIVE_TINT = "#F2E4E2"
WARN          = "#B27A1E"
WARN_TINT     = "#F4ECDB"
INFO          = "#2C4F7C"
INFO_TINT     = "#E4ECF6"

AGENT_DEBT       = "#9E3A37"
AGENT_SAVINGS    = "#1E6B52"
AGENT_BUDGET     = "#B27A1E"
AGENT_PAYOFF     = "#2C4F7C"
AGENT_SUPERVISOR = "#4A3B6B"

PAYOFF_PALETTE = ["#9E3A37", "#B27A1E", "#2C4F7C", "#1E6B52", "#0E2238"]
DEBT_PALETTE   = ["#0E2238", "#9E3A37", "#B27A1E", "#2C4F7C", "#1E6B52"]
DONUT_PALETTE  = ["#0E2238", "#2C4F7C", "#1E6B52", "#B27A1E", "#9E3A37", "#5C6B82"]


def apply_theme() -> None:
    """Inject Google Fonts + custom CSS to approximate the design's look."""
    st.markdown(
        f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;1,6..72,300;1,6..72,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
:root {{
  --bg: {BG};
  --surface: {SURFACE};
  --surface-2: {SURFACE_2};
  --line: {LINE};
  --line-strong: {LINE_STRONG};
  --ink: {INK};
  --ink-2: {INK_2};
  --ink-3: {INK_3};
  --ink-4: {INK_4};
  --positive: {POSITIVE};
  --positive-tint: {POSITIVE_TINT};
  --negative: {NEGATIVE};
  --negative-tint: {NEGATIVE_TINT};
  --warn: {WARN};
  --warn-tint: {WARN_TINT};
  --info: {INFO};
  --info-tint: {INFO_TINT};
  --font-ui: "Geist", -apple-system, BlinkMacSystemFont, sans-serif;
  --font-num: "Newsreader", Georgia, serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
  --radius: 10px;
}}

html, body, .stApp {{
  font-family: var(--font-ui);
  color: var(--ink);
}}
/* Scope to text-bearing widgets but leave icon spans alone */
.stMarkdown, .stText, .stButton, .stMetric, .stTextInput, .stTextArea,
.stSelectbox, .stDataFrame, .stTable {{
  font-family: var(--font-ui);
}}
/* Streamlit's Material icons must keep their own font */
[data-testid="stIconMaterial"], .material-symbols-rounded,
[class*="material-symbols"] {{
  font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important;
  font-feature-settings: normal !important;
}}

/* Page surface */
.stApp {{ background: var(--bg); }}
section.main > div {{ padding-top: 0 !important; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 4rem; max-width: 1280px; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
  background: var(--surface);
  border-right: 1px solid var(--line);
}}
section[data-testid="stSidebar"] .block-container {{ padding-top: 1rem; }}

/* Headings */
h1, h2, h3, h4 {{ color: var(--ink); letter-spacing: -0.01em; font-weight: 500; }}
h1 {{ font-size: 26px !important; }}
h2 {{ font-size: 18px !important; }}

/* Native Streamlit metric — soften it to match stat blocks */
[data-testid="stMetric"] {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px 18px;
}}
[data-testid="stMetricLabel"] {{
  font-size: 11.5px !important;
  color: var(--ink-3) !important;
  font-weight: 500 !important;
}}
[data-testid="stMetricValue"] {{
  font-family: var(--font-num) !important;
  font-feature-settings: "tnum" 1, "lnum" 1;
  font-size: 20px !important;
  font-weight: 400 !important;
  color: var(--ink) !important;
  letter-spacing: -0.02em;
}}
[data-testid="stMetric"] {{ padding: 14px 14px; }}
[data-testid="stMetricDelta"] {{ font-size: 11.5px !important; white-space: normal !important; }}
[data-testid="stMetricValue"] > div {{ overflow: visible !important; text-overflow: initial !important; }}

/* Buttons */
.stButton > button {{
  border-radius: 7px;
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--ink);
  font-weight: 500;
  padding: 6px 12px;
  font-size: 13px;
  transition: background 120ms;
}}
.stButton > button:hover {{ background: var(--surface-2); border-color: var(--line-strong); }}
.stButton > button:focus {{ box-shadow: none; }}
.stButton > button[kind="primary"] {{
  background: var(--ink);
  color: var(--surface);
  border-color: var(--ink);
}}
.stButton > button[kind="primary"]:hover {{ background: var(--ink-2); }}

/* Tables */
[data-testid="stDataFrame"] {{
  border: 1px solid var(--line);
  border-radius: var(--radius);
}}

/* Chat-like containers (st.chat_message) */
[data-testid="stChatMessage"] {{
  background: transparent;
  padding: 0;
}}

/* Expander */
[data-testid="stExpander"] {{
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-2);
}}

/* ---------- Custom helper classes ---------- */
.eyebrow {{
  font-size: 11.5px;
  color: var(--ink-3);
  font-weight: 500;
  letter-spacing: 0.02em;
  margin-bottom: 4px;
}}
.eyebrow .dot {{
  display: inline-block;
  width: 7px; height: 7px; border-radius: 50%;
  margin-right: 6px; vertical-align: middle;
}}

.hero-title {{
  font-family: var(--font-num);
  font-size: 30px;
  font-weight: 400;
  letter-spacing: -0.02em;
  color: var(--ink);
  margin: 0 0 4px 0;
}}
.hero-title em {{ font-style: italic; color: var(--ink-2); }}
.hero-sub {{ color: var(--ink-3); font-size: 13.5px; margin-bottom: 18px; }}
.hero-sub .pos {{ color: var(--positive); font-weight: 500; }}

.card {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 18px;
  margin-bottom: 16px;
}}
.card-title {{
  font-size: 12.5px;
  color: var(--ink-3);
  font-weight: 500;
  margin-bottom: 4px;
}}
.card-sub {{ font-size: 12px; color: var(--ink-3); }}

.num {{
  font-family: var(--font-num);
  font-feature-settings: "tnum" 1, "lnum" 1;
  font-weight: 400;
  letter-spacing: -0.01em;
}}
.mono {{ font-family: var(--font-mono); font-size: 12px; }}

.tag {{
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  background: var(--surface-2);
  color: var(--ink-2);
  border: 1px solid var(--line);
}}
.tag.pos  {{ background: var(--positive-tint); color: var(--positive); border-color: transparent; }}
.tag.neg  {{ background: var(--negative-tint); color: var(--negative); border-color: transparent; }}
.tag.warn {{ background: var(--warn-tint); color: var(--warn); border-color: transparent; }}
.tag.info {{ background: var(--info-tint); color: var(--info); border-color: transparent; }}

.brand {{
  display: flex; align-items: center; gap: 10px;
  padding: 4px 0 12px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 14px;
}}
.brand-mark {{
  width: 28px; height: 28px;
  background: var(--ink);
  color: var(--surface);
  border-radius: 7px;
  display: grid; place-items: center;
  font-family: var(--font-num);
  font-style: italic;
  font-size: 18px;
}}
.brand-name {{ font-weight: 500; font-size: 15px; }}
.brand-sub {{ font-size: 11px; color: var(--ink-3); }}

.nav-section-label {{
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.10em;
  color: var(--ink-4);
  text-transform: uppercase;
  padding: 14px 0 4px;
}}

.vault-pill {{
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--positive-tint);
  color: var(--positive);
  font-size: 11.5px;
  font-weight: 500;
}}
.vault-pill .dot {{
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--positive);
  box-shadow: 0 0 0 3px rgba(30, 107, 82, 0.25);
}}

.user-card {{
  margin-top: 18px; padding-top: 12px;
  border-top: 1px solid var(--line);
  display: flex; align-items: center; gap: 10px;
}}
.avatar {{
  width: 30px; height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--info), var(--ink));
  color: var(--surface);
  display: grid; place-items: center;
  font-size: 12px; font-weight: 500;
}}
.user-name {{ font-size: 13px; font-weight: 500; }}
.user-meta {{ font-size: 11px; color: var(--ink-3); }}

/* Stat block (for use alongside st.metric or as alternative) */
.stat {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px 18px;
}}
.stat-label {{ font-size: 11.5px; color: var(--ink-3); font-weight: 500; }}
.stat-value {{
  font-family: var(--font-num);
  font-feature-settings: "tnum" 1;
  font-size: 26px; font-weight: 400;
  letter-spacing: -0.02em;
  color: var(--ink);
  margin: 6px 0 4px;
  line-height: 1.05;
}}
.stat-delta {{ font-size: 12px; color: var(--ink-3); }}
.stat-delta.pos {{ color: var(--positive); }}
.stat-delta.neg {{ color: var(--negative); }}

/* Bar */
.bar-track {{
  height: 6px; border-radius: 999px;
  background: var(--surface-2); border: 1px solid var(--line);
  overflow: hidden;
}}
.bar-fill {{ height: 100%; background: var(--ink); border-radius: 999px; }}
.bar-fill.pos  {{ background: var(--positive); }}
.bar-fill.neg  {{ background: var(--negative); }}
.bar-fill.warn {{ background: var(--warn); }}

/* Trace timeline */
.trace-wrap {{
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-2);
  margin-top: 8px;
  overflow: hidden;
}}
.trace-head {{
  padding: 8px 12px;
  border-bottom: 1px solid var(--line);
  font-size: 10.5px;
  color: var(--ink-3);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  display: flex; justify-content: space-between;
}}
.trace-step {{
  display: grid; grid-template-columns: 16px 1fr auto; gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
}}
.trace-step:last-child {{ border-bottom: 0; }}
.trace-step .dot {{
  width: 8px; height: 8px; border-radius: 999px; margin-top: 5px;
}}
.trace-step .label {{ font-size: 12px; font-weight: 500; color: var(--ink); }}
.trace-step .title {{ font-size: 12px; color: var(--ink-2); margin-top: 2px; }}
.trace-step .ms    {{ font-family: var(--font-mono); font-size: 10px; color: var(--ink-4); padding-top: 4px; }}
.trace-tool {{
  font-family: var(--font-mono);
  font-size: 10.5px;
  padding: 4px 8px;
  border-radius: 4px;
  background: var(--surface);
  border: 1px solid var(--line);
  margin-top: 4px;
  display: flex; justify-content: space-between; gap: 8px;
}}
.trace-tool .name {{ font-weight: 500; }}
.trace-tool .args {{ color: var(--ink-3); }}
.trace-tool .arrow {{ color: var(--ink-4); }}
.trace-conclusion {{
  font-size: 11.5px; color: var(--ink-2);
  margin-top: 6px; font-style: italic;
}}
.trace-routes {{ display: flex; gap: 4px; margin-top: 6px; flex-wrap: wrap; }}
.trace-routes .pill {{
  font-size: 10.5px; padding: 2px 6px; border-radius: 4px;
  background: var(--surface); border: 1px solid var(--line);
  color: var(--ink-2);
}}

/* Chat */
.msg-user {{
  background: var(--ink);
  color: var(--surface);
  padding: 10px 14px;
  border-radius: 14px 14px 4px 14px;
  font-size: 13.5px;
  display: inline-block;
  max-width: 80%;
  margin-left: auto;
}}
.msg-agent-body {{
  background: var(--surface-2);
  border: 1px solid var(--line);
  padding: 12px 14px;
  border-radius: 14px 14px 14px 4px;
  font-size: 13.5px;
  line-height: 1.55;
}}
.agent-chip {{
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; color: var(--ink-3); font-weight: 500;
  margin-bottom: 4px;
}}
.agent-chip .dot {{ width: 7px; height: 7px; border-radius: 50%; display: inline-block; }}

.routing-pill {{
  padding: 8px 12px;
  background: var(--info-tint);
  border-radius: 8px;
  color: var(--info);
  font-size: 11.5px;
  display: inline-block;
}}
.routing-pill strong {{ font-weight: 500; }}
.routing-pill .dot {{
  display: inline-block;
  width: 7px; height: 7px; border-radius: 50%;
  margin: 0 4px 1px 8px; vertical-align: middle;
}}

.payoff-card {{
  margin-top: 8px; padding: 12px;
  border: 1px solid var(--line); border-radius: 8px;
  background: var(--surface);
}}
.payoff-card .eyebrow-sm {{
  font-size: 11px; color: var(--ink-3);
  letter-spacing: 0.06em; text-transform: uppercase;
  margin-bottom: 6px;
}}
.payoff-card .target {{ font-size: 14px; font-weight: 500; }}
.payoff-card .amount {{ font-family: var(--font-num); font-size: 22px; }}
.payoff-card .saved {{ font-size: 11px; color: var(--positive); }}

/* Pipeline / steps */
.step-row {{
  display: flex; gap: 10px; align-items: flex-start;
  padding: 8px 0;
}}
.step-num {{
  width: 22px; height: 22px; border-radius: 999px;
  display: grid; place-items: center;
  font-size: 11px; font-weight: 600;
  background: var(--ink); color: var(--surface);
  flex-shrink: 0;
}}
.step-num.ok   {{ background: var(--positive-tint); color: var(--positive); }}
.step-num.run  {{ background: var(--info-tint); color: var(--info); }}
.step-num.idle {{ background: var(--surface-2); color: var(--ink-4); border: 1px solid var(--line); }}
.step-title {{ font-size: 13px; font-weight: 500; }}
.step-desc  {{ font-size: 12px; color: var(--ink-3); }}

/* Goal / payoff row card */
.row-card {{
  padding: 12px 14px;
  border: 1px solid var(--line); border-radius: 8px;
  background: var(--surface-2);
  margin-bottom: 8px;
}}
.row-card.first {{ background: var(--negative-tint); }}

.checklist-item {{
  display: flex; gap: 14px; align-items: flex-start;
  padding: 14px 0; border-top: 1px solid var(--line);
}}
.checklist-item:first-child {{ border-top: 0; }}
.check-icon {{
  width: 22px; height: 22px; border-radius: 999px;
  display: grid; place-items: center;
  background: var(--positive-tint); color: var(--positive);
  font-weight: 700; font-size: 12px;
  flex-shrink: 0;
}}
.check-icon.warn {{ background: var(--warn-tint); color: var(--warn); }}

/* Hide Streamlit chrome */
#MainMenu, footer, [data-testid="stToolbar"] {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
</style>
        """,
        unsafe_allow_html=True,
    )

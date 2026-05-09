"""Documents / ingestion view — file upload, pipeline, sources table."""

import streamlit as st

from theme import (
    INK, INK_2, INK_3, INK_4,
    SURFACE_2, LINE,
    POSITIVE, POSITIVE_TINT,
    INFO, INFO_TINT,
)


# ---------------------------------------------------------------------------
# Helper: infer source from filename (mirrors JSX sourceFromName)
# ---------------------------------------------------------------------------

def _source_from_name(name: str) -> str:
    s = name.lower()
    if "chase" in s:
        return "Chase"
    if "capital" in s:
        return "Capital One"
    if "wells" in s:
        return "Wells Fargo"
    if "sofi" in s:
        return "SoFi"
    if "schwab" in s:
        return "Schwab"
    if "honda" in s:
        return "Honda Financial"
    return "Uploaded"


# ---------------------------------------------------------------------------
# Helper: format file size
# ---------------------------------------------------------------------------

def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{round(size_bytes / 1024)} KB"
    return f"{size_bytes / 1024 / 1024:.1f} MB"


# ---------------------------------------------------------------------------
# Pipeline step HTML
# ---------------------------------------------------------------------------

_PIPELINE = [
    {"step": "Parse",     "desc": "CSV / PDF / OFX → typed rows",             "status": "active"},
    {"step": "Normalize", "desc": "Dates, currencies, merchant cleanup",       "status": "active"},
    {"step": "Redact",    "desc": "PII & account numbers stripped",            "status": "active"},
    {"step": "Embed",     "desc": "Per-row vectors → tabular RAG store",       "status": "running"},
    {"step": "Index",     "desc": "Available to all advisor agents",           "status": "queued"},
]


def _pipeline_html() -> str:
    rows = []
    for i, p in enumerate(_PIPELINE, start=1):
        if p["status"] == "active":
            num_bg = POSITIVE_TINT
            num_color = POSITIVE
            num_content = "✓"
        elif p["status"] == "running":
            num_bg = INFO_TINT
            num_color = INFO
            num_content = "⏳"
        else:
            num_bg = SURFACE_2
            num_color = INK_4
            num_content = str(i)

        border_style = f"border:1px solid {LINE};" if p["status"] == "queued" else "border:none;"

        rows.append(f"""
<div class="step-row">
  <div class="step-num" style="background:{num_bg};color:{num_color};{border_style}">
    {num_content}
  </div>
  <div>
    <div class="step-title">{p['step']}</div>
    <div class="step-desc">{p['desc']}</div>
  </div>
</div>""")

    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Status pill HTML
# ---------------------------------------------------------------------------

def _status_pill(status: str) -> str:
    if status == "ready":
        return f'<span class="tag pos">✓ Indexed</span>'
    if status == "embedding":
        return f'<span class="tag info">⏳ Embedding</span>'
    if status == "parsing":
        return f'<span class="tag warn">Parsing</span>'
    return f'<span class="tag">{status}</span>'


# ---------------------------------------------------------------------------
# Sources table HTML
# ---------------------------------------------------------------------------

def _sources_table_html(all_docs: list) -> str:
    rows = []
    for d in all_docs:
        rows.append(f"""
  <tr>
    <td>
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:28px;height:28px;border-radius:6px;background:{SURFACE_2};
                    border:1px solid {LINE};display:grid;place-items:center;
                    color:{INK_3};font-size:11px;flex-shrink:0;">📄</div>
        <span class="mono" style="font-size:12.5px;">{d['name']}</span>
      </div>
    </td>
    <td style="font-size:12.5px;">{d['source']}</td>
    <td style="font-size:12px;color:{INK_3};white-space:nowrap;">{d['added']}</td>
    <td class="num" style="text-align:right;font-size:13.5px;">{d['rows']:,}</td>
    <td style="font-size:12px;color:{INK_3};">{d['size']}</td>
    <td>{_status_pill(d['status'])}</td>
  </tr>""")

    return f"""
<table style="width:100%;border-collapse:collapse;font-family:Geist,sans-serif;">
  <thead>
    <tr style="border-bottom:1px solid {LINE};">
      <th style="text-align:left;font-size:11px;font-weight:500;color:{INK_3};padding:0 8px 8px 0;">Document</th>
      <th style="text-align:left;font-size:11px;font-weight:500;color:{INK_3};padding:0 8px 8px 0;">Source</th>
      <th style="text-align:left;font-size:11px;font-weight:500;color:{INK_3};padding:0 8px 8px 0;">Added</th>
      <th style="text-align:right;font-size:11px;font-weight:500;color:{INK_3};padding:0 8px 8px 0;">Rows</th>
      <th style="text-align:left;font-size:11px;font-weight:500;color:{INK_3};padding:0 8px 8px 0;">Size</th>
      <th style="text-align:left;font-size:11px;font-weight:500;color:{INK_3};padding:0 0 8px 0;">Status</th>
    </tr>
  </thead>
  <tbody>
    {''.join(rows)}
  </tbody>
</table>
"""


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render(persona):
    # Persist extra_docs across reruns
    st.session_state.setdefault("extra_docs", [])

    # -----------------------------------------------------------------------
    # 1. Page header
    # -----------------------------------------------------------------------
    st.markdown(
        f"""
<div class="eyebrow" style="margin-bottom:6px;">Ingestion</div>
<h1 style="margin-bottom:4px;">Documents</h1>
<div style="font-size:13.5px;color:{INK_3};margin-bottom:18px;">
  Drop bank exports, statements, receipts. Everything is parsed, redacted, and embedded
  into a private vector store before any advisor sees it.
</div>
""",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # 2. Split: dropzone (left) + pipeline (right)
    # -----------------------------------------------------------------------
    drop_col, pipe_col = st.columns([1.6, 1])

    with drop_col:
        st.markdown(
            f"""
<div class="card" style="text-align:center;padding:32px 24px;">
  <div style="font-size:32px;margin-bottom:8px;">⬆</div>
  <div style="font-size:15px;font-weight:500;margin-bottom:6px;">Drop files or click to browse</div>
  <div style="font-size:12.5px;color:{INK_3};max-width:380px;margin:0 auto 12px;">
    Supported: CSV, OFX, QFX, PDF statements from Chase, Wells Fargo, Capital One, SoFi, Schwab, and 60+ others.
  </div>
""",
            unsafe_allow_html=True,
        )

        uploaded = st.file_uploader(
            "Upload financial documents",
            accept_multiple_files=True,
            type=["csv", "pdf", "ofx", "qfx", "tsv", "txt"],
            label_visibility="collapsed",
            key="doc_uploader",
        )

        st.markdown(
            f"""
  <div style="font-size:11px;color:{INK_3};margin-top:8px;display:flex;align-items:center;justify-content:center;gap:6px;">
    🔒 Files are stored &amp; embedded locally on this device
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        # Process newly uploaded files
        if uploaded:
            existing_names = {d["name"] for d in st.session_state.extra_docs}
            new_docs = []
            for f in uploaded:
                if f.name not in existing_names:
                    size_kb = max(1, f.size // 1024)
                    rows = max(1, f.size // 600)
                    new_docs.append({
                        "name": f.name,
                        "size": _format_size(f.size),
                        "added": "May 9",
                        "status": "ready",
                        "rows": rows,
                        "source": _source_from_name(f.name),
                    })
            if new_docs:
                st.session_state.extra_docs = new_docs + st.session_state.extra_docs

    with pipe_col:
        st.markdown(
            f"""
<div class="card">
  <div class="card-title" style="margin-bottom:12px;">Pipeline</div>
  {_pipeline_html()}
</div>
""",
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------------
    # 3. "What happens next" — 3-column grid
    # -----------------------------------------------------------------------
    st.markdown(
        f"""
<div class="card" style="margin-top:16px;">
  <div style="margin-bottom:14px;">
    <div class="card-title">What happens next</div>
    <div class="card-sub">Three steps after your documents are indexed</div>
  </div>
""",
        unsafe_allow_html=True,
    )

    next_col1, next_col2, next_col3 = st.columns(3)

    with next_col1:
        st.markdown(
            f"""
<div style="padding:16px;border-radius:10px;border:1px solid {LINE};background:{SURFACE_2};
            display:flex;flex-direction:column;gap:8px;">
  <div style="width:22px;height:22px;border-radius:999px;background:{INK};color:white;
              display:grid;place-items:center;font-size:12px;font-weight:500;">1</div>
  <div style="font-size:14.5px;font-weight:500;">Review your dashboard</div>
  <div style="font-size:12.5px;color:{INK_3};line-height:1.5;">
    See net worth, debts, savings, and budget &mdash; all derived from the documents you just uploaded.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button("Open dashboard →", key="next_dashboard", use_container_width=True):
            st.session_state.view = "dashboard"
            st.rerun()

    with next_col2:
        st.markdown(
            f"""
<div style="padding:16px;border-radius:10px;border:1px solid {LINE};background:{SURFACE_2};
            display:flex;flex-direction:column;gap:8px;">
  <div style="width:22px;height:22px;border-radius:999px;background:{INK};color:white;
              display:grid;place-items:center;font-size:12px;font-weight:500;">2</div>
  <div style="font-size:14.5px;font-weight:500;">Ask the advisor</div>
  <div style="font-size:12.5px;color:{INK_3};line-height:1.5;">
    Type any question. The supervisor routes it to the right specialist agent and returns a synthesis.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button("Open advisor →", key="next_chat", use_container_width=True):
            st.session_state.view = "chat"
            st.rerun()

    with next_col3:
        st.markdown(
            f"""
<div style="padding:16px;border-radius:10px;border:1px solid {LINE};background:{SURFACE_2};
            display:flex;flex-direction:column;gap:8px;">
  <div style="width:22px;height:22px;border-radius:999px;background:{INK};color:white;
              display:grid;place-items:center;font-size:12px;font-weight:500;">3</div>
  <div style="font-size:14.5px;font-weight:500;">Apply a recommendation</div>
  <div style="font-size:12.5px;color:{INK_3};line-height:1.5;">
    Each agent suggests concrete next moves &mdash; payoff order, savings shifts, budget cuts. Apply with one click.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button("See payoff plan →", key="next_payoff", use_container_width=True):
            st.session_state.view = "payoff"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 4. Sources table
    # -----------------------------------------------------------------------
    all_docs = st.session_state.extra_docs + persona["documents"]
    total_rows = sum(d["rows"] for d in all_docs)
    n_sources = len({d["source"] for d in all_docs})
    count = len(all_docs)

    st.markdown(
        f"""
<div class="card" style="margin-top:16px;">
  <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;">
    <div>
      <div class="card-title">Sources · {count}</div>
      <div class="card-sub">{total_rows:,} rows indexed across {n_sources} sources</div>
    </div>
  </div>
  {_sources_table_html(all_docs)}
</div>
""",
        unsafe_allow_html=True,
    )

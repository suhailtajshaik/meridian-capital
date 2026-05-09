"""Settings & security view — ported from SettingsView in views.jsx."""

import streamlit as st

from theme import (
    INK, INK_2, INK_3, INK_4,
    LINE,
    POSITIVE, POSITIVE_TINT,
    WARN, WARN_TINT,
    SURFACE,
)


_SECURITY_CHECKS = [
    {
        "label": "Local-first storage",
        "desc": "Documents and embeddings live on this device only — no cloud sync, no remote server",
        "status": "ok",
    },
    {
        "label": "On-device embedding model",
        "desc": "Vectors generated locally via a quantized model. Statement contents never leave your machine",
        "status": "ok",
    },
    {
        "label": "At-rest encryption",
        "desc": "AES-256-GCM on the local vault · keys derived from your passphrase, stored only in OS keychain",
        "status": "ok",
    },
    {
        "label": "PII redaction before LLM",
        "desc": "Account numbers, SSN, names stripped before any prompt is sent to the language model",
        "status": "ok",
    },
    {
        "label": "Read-only ingestion",
        "desc": "No agent can move money. We only read the statements you upload",
        "status": "ok",
    },
    {
        "label": "Recovery passphrase",
        "desc": "Generate an offline backup phrase — without it, the local vault cannot be recovered",
        "status": "warn",
    },
]


def render(persona: dict) -> None:
    docs = persona["documents"]

    # ---- Session state ----
    st.session_state.setdefault("removed_docs", [])
    st.session_state.setdefault("confirm_remove_all", False)

    removed: list = st.session_state["removed_docs"]
    visible = [d for d in docs if d["name"] not in removed]
    row_total = sum(d["rows"] for d in visible)

    # ---- Header ----
    st.markdown(
        f"""
        <div style="margin-bottom:18px;">
          <h1 style="font-size:26px;font-weight:500;letter-spacing:-0.01em;
                     color:{INK};margin:0 0 4px 0;">Settings &amp; security</h1>
          <div style="font-size:13.5px;color:{INK_3};max-width:720px;">
            Everything runs locally on this device. No cloud sync, no remote server.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Top 2-up cards ----
    col1, col2 = st.columns(2)

    with col1:
        n_docs = len(visible)
        doc_word = "document" if n_docs == 1 else "documents"
        st.markdown(
            f"""
            <div class="card" style="background:{POSITIVE_TINT};border-color:transparent;
                                     margin-bottom:0;">
              <div style="display:flex;align-items:center;gap:8px;color:{POSITIVE};">
                <span style="font-size:16px;">🛡️</span>
                <div style="font-size:11.5px;font-weight:600;letter-spacing:0.08em;
                            text-transform:uppercase;">Vault status</div>
              </div>
              <div style="font-size:18px;font-weight:500;color:{POSITIVE};margin-top:8px;">
                Local &amp; encrypted
              </div>
              <div style="font-size:12.5px;color:{INK_2};margin-top:4px;">
                {n_docs} {doc_word} · {row_total:,} rows on disk
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="card" style="margin-bottom:0;">
              <div class="card-title">Agent permissions</div>
              <div class="num" style="font-size:18px;margin-top:8px;">Read-only</div>
              <div style="font-size:12px;color:{INK_3};margin-top:4px;">
                No agent can initiate transfers — statements are read-only
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ---- Security checklist card ----
    n_ok = sum(1 for s in _SECURITY_CHECKS if s["status"] == "ok")
    n_total = len(_SECURITY_CHECKS)

    items_html = ""
    for i, s in enumerate(_SECURITY_CHECKS):
        border_top = f"border-top:1px solid {LINE};" if i > 0 else ""
        if s["status"] == "ok":
            icon_html = (
                f'<div style="width:22px;height:22px;border-radius:999px;'
                f'background:{POSITIVE_TINT};color:{POSITIVE};'
                f'display:grid;place-items:center;flex-shrink:0;'
                f'font-weight:700;font-size:12px;">&#10003;</div>'
            )
            tag_html = f'<span class="tag pos">Active</span>'
        else:
            icon_html = (
                f'<div style="width:22px;height:22px;border-radius:999px;'
                f'background:{WARN_TINT};color:{WARN};'
                f'display:grid;place-items:center;flex-shrink:0;'
                f'font-weight:700;font-size:12px;">&#9888;</div>'
            )
            tag_html = f'<span class="tag warn">Action needed</span>'

        items_html += f"""
        <div style="display:flex;gap:14px;align-items:flex-start;
                    padding:14px 0;{border_top}">
          {icon_html}
          <div style="flex:1;">
            <div style="font-size:13.5px;font-weight:500;color:{INK};">
              {s["label"]}
            </div>
            <div style="font-size:12px;color:{INK_3};margin-top:2px;">
              {s["desc"]}
            </div>
          </div>
          {tag_html}
        </div>
        """

    st.markdown(
        f"""
        <div class="card">
          <div style="margin-bottom:4px;">
            <div class="card-title">Security checklist</div>
            <div class="card-sub">{n_ok} of {n_total} complete</div>
          </div>
          {items_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Uploaded documents card ----
    st.markdown(
        f"""
        <div class="card" style="margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;
                      align-items:center;margin-bottom:14px;">
            <div>
              <div class="card-title" style="margin-bottom:0;">
                Uploaded documents · {len(visible)}
              </div>
              <div class="card-sub">Read-only · remove any source instantly</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Remove-all confirmation lives outside the HTML block so buttons work
    if len(visible) > 0:
        if st.session_state.get("confirm_remove_all"):
            msg_col, cancel_col, confirm_col = st.columns([4, 1, 1])
            with msg_col:
                st.markdown(
                    f'<span style="font-size:12px;color:{INK_2};">'
                    f'Remove all {len(visible)}?</span>',
                    unsafe_allow_html=True,
                )
            with cancel_col:
                if st.button("Cancel", key="cancel_remove_all"):
                    st.session_state["confirm_remove_all"] = False
                    st.rerun()
            with confirm_col:
                if st.button("Confirm", key="confirm_remove_all_btn"):
                    st.session_state["removed_docs"] = [d["name"] for d in docs]
                    st.session_state["confirm_remove_all"] = False
                    st.rerun()
        else:
            _, btn_col = st.columns([5, 1])
            with btn_col:
                if st.button("Remove all", key="remove_all_btn"):
                    st.session_state["confirm_remove_all"] = True
                    st.rerun()

    # Column headers
    h1, h2, h3, h4, h5 = st.columns([3, 1.5, 1, 1.2, 1.2])
    with h1:
        st.markdown(
            f'<div style="font-size:11px;color:{INK_4};font-weight:600;'
            f'letter-spacing:0.06em;text-transform:uppercase;padding-bottom:4px;">'
            f'File</div>',
            unsafe_allow_html=True,
        )
    with h2:
        st.markdown(
            f'<div style="font-size:11px;color:{INK_4};font-weight:600;'
            f'letter-spacing:0.06em;text-transform:uppercase;padding-bottom:4px;">'
            f'Source</div>',
            unsafe_allow_html=True,
        )
    with h3:
        st.markdown(
            f'<div style="font-size:11px;color:{INK_4};font-weight:600;'
            f'letter-spacing:0.06em;text-transform:uppercase;padding-bottom:4px;">'
            f'Rows</div>',
            unsafe_allow_html=True,
        )
    with h4:
        st.markdown(
            f'<div style="font-size:11px;color:{INK_4};font-weight:600;'
            f'letter-spacing:0.06em;text-transform:uppercase;padding-bottom:4px;">'
            f'Added</div>',
            unsafe_allow_html=True,
        )
    with h5:
        st.markdown("&nbsp;", unsafe_allow_html=True)

    st.markdown(
        f'<div style="border-top:1px solid {LINE};margin-bottom:4px;"></div>',
        unsafe_allow_html=True,
    )

    if not visible:
        st.markdown(
            f'<div style="text-align:center;padding:24px;font-size:13px;'
            f'color:{INK_3};">No documents in vault. Upload from the Documents page '
            f'to get started.</div>',
            unsafe_allow_html=True,
        )
    else:
        for d in visible:
            r1, r2, r3, r4, r5 = st.columns([3, 1.5, 1, 1.2, 1.2])
            with r1:
                st.markdown(
                    f'<div style="font-family:var(--font-mono);font-size:12px;'
                    f'font-weight:500;color:{INK};padding:6px 0;">{d["name"]}</div>',
                    unsafe_allow_html=True,
                )
            with r2:
                st.markdown(
                    f'<div style="padding:6px 0;">'
                    f'<span class="tag">{d["source"]}</span></div>',
                    unsafe_allow_html=True,
                )
            with r3:
                st.markdown(
                    f'<div style="font-family:var(--font-mono);font-size:12px;'
                    f'color:{INK_3};padding:6px 0;">{d["rows"]}</div>',
                    unsafe_allow_html=True,
                )
            with r4:
                st.markdown(
                    f'<div style="font-size:12px;color:{INK_3};padding:6px 0;">'
                    f'{d["added"]}</div>',
                    unsafe_allow_html=True,
                )
            with r5:
                if st.button("Remove", key=f"remove_{d['name']}"):
                    st.session_state["removed_docs"].append(d["name"])
                    st.rerun()

            st.markdown(
                f'<div style="border-top:1px solid {LINE};"></div>',
                unsafe_allow_html=True,
            )

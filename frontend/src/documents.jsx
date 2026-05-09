import React from 'react';
import { I } from './icons.jsx';

/* Documents / ingestion view */

export function StatusPill({ status }) {
  if (status === "ready") return <span className="tag pos"><I.check size={10}/> Indexed</span>;
  if (status === "embedding") return <span className="tag info"><span className="spinner" style={{ borderColor: "currentColor", borderTopColor: "transparent", width: 9, height: 9 }}/> Embedding</span>;
  if (status === "parsing") return <span className="tag warn">Parsing</span>;
  return <span className="tag">{status}</span>;
}

export function Documents({ persona, onNav }) {
  const [drag, setDrag] = React.useState(false);
  const [extra, setExtra] = React.useState([]);
  const fileRef = React.useRef(null);

  const addFiles = (fileList) => {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    const today = new Date().toLocaleDateString(undefined, { month: "short", day: "numeric" });
    const formatSize = (b) => b < 1024 ? b + " B" : b < 1024*1024 ? Math.round(b/1024) + " KB" : (b/1024/1024).toFixed(1) + " MB";
    const sourceFromName = (n) => {
      const s = n.toLowerCase();
      if (s.includes("chase")) return "Chase";
      if (s.includes("capital")) return "Capital One";
      if (s.includes("wells")) return "Wells Fargo";
      if (s.includes("sofi")) return "SoFi";
      if (s.includes("schwab")) return "Schwab";
      if (s.includes("honda")) return "Honda Financial";
      return "Uploaded";
    };
    const newDocs = files.map((f) => ({
      name: f.name, size: formatSize(f.size), added: today,
      status: "parsing", rows: Math.max(1, Math.round(f.size / 600)),
      source: sourceFromName(f.name),
    }));
    setExtra((cur) => [...newDocs, ...cur]);
    // Simulate pipeline progression
    newDocs.forEach((doc, i) => {
      setTimeout(() => setExtra((cur) => cur.map((d) => d.name === doc.name && d.added === doc.added ? { ...d, status: "embedding" } : d)), 700 + i*120);
      setTimeout(() => setExtra((cur) => cur.map((d) => d.name === doc.name && d.added === doc.added ? { ...d, status: "ready" } : d)), 1800 + i*120);
    });
  };
  const ingestPipeline = [
    { step: "Parse", desc: "CSV / PDF / OFX → typed rows", status: "active" },
    { step: "Normalize", desc: "Dates, currencies, merchant cleanup", status: "active" },
    { step: "Redact", desc: "PII & account numbers stripped", status: "active" },
    { step: "Embed", desc: "Per-row vectors → tabular RAG store", status: "running" },
    { step: "Index", desc: "Available to all advisor agents", status: "queued" },
  ];

  return (
    <div className="scroll" data-screen-label="02 Documents">
      <div style={{ marginBottom: 18 }}>
        <div className="eyebrow" style={{ marginBottom: 6 }}>Ingestion</div>
        <h1 className="h1">Documents</h1>
        <div className="muted" style={{ fontSize: 13.5, marginTop: 4 }}>
          Drop bank exports, statements, receipts. Everything is parsed, redacted, and embedded into a private vector store before any advisor sees it.
        </div>
      </div>

      <div className="split-main">
        <div className={`dropzone ${drag ? "dragging" : ""}`}
             onClick={() => fileRef.current?.click()}
             onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
             onDragLeave={() => setDrag(false)}
             onDrop={(e) => { e.preventDefault(); setDrag(false); addFiles(e.dataTransfer.files); }}
             style={{ cursor: "pointer" }}>
          <input ref={fileRef} type="file" multiple
            accept=".csv,.pdf,.ofx,.qfx,.tsv,.txt"
            onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }}
            style={{ display: "none" }}/>
          <I.upload className="icon" size={32} sw={1.25}/>
          <div style={{ fontSize: 15, fontWeight: 500 }}>Drop files or click to browse</div>
          <div className="muted" style={{ fontSize: 12.5, maxWidth: 380 }}>
            Supported: CSV, OFX, QFX, PDF statements from Chase, Wells Fargo, Capital One, SoFi, Schwab, and 60+ others.
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
            <button className="btn primary" onClick={(e) => { e.stopPropagation(); fileRef.current?.click(); }}><I.upload size={13}/> Choose files</button>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 8, fontSize: 11, color: "var(--ink-3)" }}>
            <I.lock size={11}/> Files are stored & embedded locally on this device
          </div>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>Pipeline</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {ingestPipeline.map((p, i) => (
              <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                <div style={{
                  width: 22, height: 22, borderRadius: 999,
                  background: p.status === "running" ? "var(--info-tint)" : p.status === "active" ? "var(--positive-tint)" : "var(--surface-2)",
                  color: p.status === "running" ? "var(--info)" : p.status === "active" ? "var(--positive)" : "var(--ink-4)",
                  border: "1px solid var(--line)",
                  display: "grid", placeItems: "center", fontSize: 10, fontWeight: 600,
                  flexShrink: 0,
                }}>
                  {p.status === "running" ? <span className="spinner" style={{ width: 9, height: 9, borderColor: "currentColor", borderTopColor: "transparent" }}/> :
                   p.status === "active" ? <I.check size={11}/> : i + 1}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{p.step}</div>
                  <div style={{ fontSize: 12, color: "var(--ink-3)" }}>{p.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-head">
          <div>
            <div className="card-title">What happens next</div>
            <div className="card-sub">Three steps after your documents are indexed</div>
          </div>
        </div>
        <div className="grid-3" style={{ marginTop: 4 }}>
          {[
            { n: "1", title: "Review your dashboard", desc: "See net worth, debts, savings, and budget — all derived from the documents you just uploaded.", cta: "Open dashboard", to: "dashboard" },
            { n: "2", title: "Ask the advisor", desc: "Type any question. The supervisor routes it to the right specialist agent and returns a synthesis.", cta: "Open advisor", to: "chat" },
            { n: "3", title: "Apply a recommendation", desc: "Each agent suggests concrete next moves — payoff order, savings shifts, budget cuts. Apply with one click.", cta: "See payoff plan", to: "payoff" },
          ].map((s) => (
            <button key={s.n} onClick={() => onNav?.(s.to)}
              style={{
                all: "unset", cursor: "pointer",
                padding: 16, borderRadius: 10,
                border: "1px solid var(--line)",
                background: "var(--surface-2)",
                display: "flex", flexDirection: "column", gap: 8,
              }}>
              <div style={{
                width: 22, height: 22, borderRadius: 999,
                background: "var(--ink)", color: "var(--surface)",
                display: "grid", placeItems: "center",
                fontSize: 12, fontWeight: 500,
              }}>{s.n}</div>
              <div style={{ fontSize: 14.5, fontWeight: 500 }}>{s.title}</div>
              <div className="muted" style={{ fontSize: 12.5, lineHeight: 1.5 }}>{s.desc}</div>
              <div style={{ fontSize: 12.5, color: "var(--ink)", fontWeight: 500, marginTop: 4, display: "inline-flex", alignItems: "center", gap: 4 }}>
                {s.cta} →
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-head">
          <div>
            <div className="card-title">Sources · {persona.documents.length + extra.length}</div>
            <div className="card-sub">{(persona.documents.reduce((s, d) => s + d.rows, 0) + extra.reduce((s, d) => s + d.rows, 0)).toLocaleString()} rows indexed across {new Set([...persona.documents, ...extra].map(d => d.source)).size} sources</div>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <button className="btn ghost" style={{ fontSize: 12 }}><I.filter size={12}/> Filter</button>
            <button className="btn ghost" style={{ fontSize: 12 }}><I.refresh size={12}/> Re-sync all</button>
          </div>
        </div>
        <table className="table documents-table">
          <thead>
            <tr>
              <th>Document</th>
              <th className="col-source">Source</th>
              <th className="col-added">Added</th>
              <th className="col-rows">Rows</th>
              <th className="col-size">Size</th>
              <th>Status</th>
              <th style={{ width: 32 }}></th>
            </tr>
          </thead>
          <tbody>
            {[...extra, ...persona.documents].map((d, i) => (
              <tr key={i}>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: 6,
                      background: "var(--surface-2)", border: "1px solid var(--line)",
                      display: "grid", placeItems: "center", color: "var(--ink-3)",
                    }}>
                      <I.doc size={14}/>
                    </div>
                    <div>
                      <div className="mono" style={{ fontSize: 12.5 }}>{d.name}</div>
                    </div>
                  </div>
                </td>
                <td className="col-source">{d.source}</td>
                <td className="col-added muted" style={{ fontSize: 12 }}>{d.added}</td>
                <td className="col-rows num tnum" style={{ fontSize: 13.5 }}>{d.rows.toLocaleString()}</td>
                <td className="col-size muted" style={{ fontSize: 12 }}>{d.size}</td>
                <td><StatusPill status={d.status}/></td>
                <td><button className="icon-btn" style={{ width: 26, height: 26 }}><I.more size={14}/></button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}


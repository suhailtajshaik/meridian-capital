import React from 'react';
import { I } from './icons.jsx';
import { streamUpload } from './lib/api.js';
import { getSessionId } from './lib/session.js';

/* Documents / ingestion view */

export function StatusPill({ status }) {
  if (status === "ready") return <span className="tag pos"><I.check size={10}/> Indexed</span>;
  if (status === "embedding") return <span className="tag info"><span className="spinner" style={{ borderColor: "currentColor", borderTopColor: "transparent", width: 9, height: 9 }}/> Embedding</span>;
  if (status === "parsing") return <span className="tag warn">Parsing</span>;
  if (status === "normalizing") return <span className="tag warn">Normalizing</span>;
  if (status === "redacting") return <span className="tag warn">Redacting</span>;
  if (status === "indexing") return <span className="tag info"><span className="spinner" style={{ borderColor: "currentColor", borderTopColor: "transparent", width: 9, height: 9 }}/> Indexing</span>;
  if (status === "error") return <span className="tag neg">Error</span>;
  return <span className="tag">{status}</span>;
}

/* Pipeline step labels — match the SSE stages emitted by /api/upload */
const PIPELINE_STEPS = [
  { key: "parse",     step: "Parse",     desc: "CSV / PDF / XLSX → typed rows" },
  { key: "normalize", step: "Normalize", desc: "Snake-case columns, parsed dates" },
  { key: "redact",    step: "Redact",    desc: "Merchant names + account numbers stripped" },
  { key: "index",     step: "Index",     desc: "Per-session SQLite + raw file saved" },
  { key: "analyze",   step: "Analyze",   desc: "4 advisor agents reason over your data" },
];

const STAGE_INDEX = Object.fromEntries(PIPELINE_STEPS.map((s, i) => [s.key, i]));

/**
 * Returns pipeline step state for each step index.
 * activeStep: 0-4 (index of the in-progress step), or -1 (idle), or 5 (done).
 */
function getPipelineStatus(activeStep) {
  return PIPELINE_STEPS.map((p, i) => {
    if (activeStep < 0) return { ...p, status: "idle" };
    if (i < activeStep) return { ...p, status: "active" };   // completed
    if (i === activeStep) return { ...p, status: "running" }; // in progress
    return { ...p, status: "queued" };
  });
}

export function Documents({ online, onNav, uploadFile: apiUpload, uploading, uploadError, refresh }) {

  const [drag, setDrag] = React.useState(false);
  // `docs` tracks all uploads made in this session in-memory.
  // There is no backend endpoint to list previously uploaded documents,
  // so this list resets when the tab is closed.
  const [docs, setDocs] = React.useState([]);
  const [activeStep, setActiveStep] = React.useState(-1); // -1 = idle
  const fileRef = React.useRef(null);

  const ingestPipeline = getPipelineStatus(activeStep);

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

  const formatSize = (b) =>
    b < 1024 ? b + " B"
    : b < 1024 * 1024 ? Math.round(b / 1024) + " KB"
    : (b / 1024 / 1024).toFixed(1) + " MB";

  /* Track the current agent that's running during the analyze stage */
  const [activeAgent, setActiveAgent] = React.useState(null);

  const addFiles = async (fileList) => {
    if (!online) return;
    const files = Array.from(fileList || []);
    if (!files.length) return;

    const today = new Date().toLocaleDateString(undefined, { month: "short", day: "numeric" });

    for (const file of files) {
      const doc = {
        name: file.name,
        size: formatSize(file.size),
        added: today,
        status: "parsing",
        rows: 0,
        source: sourceFromName(file.name),
      };
      setDocs((cur) => [doc, ...cur]);
      setActiveStep(0);
      setActiveAgent(null);

      try {
        const sessionId = getSessionId();
        await streamUpload({
          file,
          sessionId,
          onEvent: (event) => {
            if (event.type === 'stage' && event.stage in STAGE_INDEX) {
              setActiveStep(STAGE_INDEX[event.stage]);
              if (event.stage !== 'analyze') setActiveAgent(null);
            } else if (event.type === 'ingest_complete') {
              setDocs((cur) =>
                cur.map((d) =>
                  d.name === doc.name && d.added === doc.added
                    ? { ...d, rows: event.rows ?? d.rows, table_name: event.table_name, status: "indexing" }
                    : d
                )
              );
            } else if (event.type === 'trace') {
              const agent = event.event?.agent;
              const t = event.event?.type;
              if (agent && (t === 'agent_start' || t === 'tool_call')) {
                setActiveAgent(agent);
              }
            } else if (event.type === 'snapshot') {
              setActiveStep(PIPELINE_STEPS.length); // all done
              setActiveAgent(null);
              setDocs((cur) =>
                cur.map((d) =>
                  d.name === doc.name && d.added === doc.added ? { ...d, status: "ready" } : d
                )
              );
              // Tell parent to refresh its snapshot state
              refresh().catch(() => {});
            } else if (event.type === 'error') {
              setDocs((cur) =>
                cur.map((d) =>
                  d.name === doc.name && d.added === doc.added ? { ...d, status: "error" } : d
                )
              );
            }
          },
        });
      } catch (err) {
        setActiveStep(-1);
        setActiveAgent(null);
        setDocs((cur) =>
          cur.map((d) =>
            d.name === doc.name && d.added === doc.added ? { ...d, status: "error" } : d
          )
        );
      }

      // Brief pause then reset
      setTimeout(() => { setActiveStep(-1); setActiveAgent(null); }, 1200);
    }
  };

  const totalRows = docs.reduce((s, d) => s + (d.rows ?? 0), 0);
  const uniqueSources = new Set(docs.map(d => d.source)).size;

  return (
    <div className="scroll" data-screen-label="02 Documents">
      <div style={{ marginBottom: 18 }}>
        <div className="eyebrow" style={{ marginBottom: 6 }}>Ingestion</div>
        <h1 className="h1">Documents</h1>
        <div className="muted" style={{ fontSize: 13.5, marginTop: 4 }}>
          Drop bank exports, statements, receipts. Everything is parsed, redacted, and embedded into a private vector store before any advisor sees it.
        </div>
      </div>

      {uploadError && (
        <div style={{
          marginBottom: 12, padding: "8px 12px",
          borderRadius: 8, background: "var(--negative-tint)",
          border: "1px solid var(--negative)",
          fontSize: 12.5, color: "var(--ink-2)",
          display: "flex", gap: 8, alignItems: "center",
        }}>
          <I.alert size={13} style={{ color: "var(--negative)", flexShrink: 0 }}/>
          Upload failed: {uploadError.message}
        </div>
      )}

      {!online && (
        <div style={{
          marginBottom: 12, padding: "10px 14px",
          borderRadius: 8, background: "var(--negative-tint)",
          border: "1px solid var(--negative)",
          fontSize: 12.5, color: "var(--ink-2)",
          display: "flex", gap: 8, alignItems: "center",
        }}>
          <I.alert size={13} style={{ color: "var(--negative)", flexShrink: 0 }}/>
          Backend is offline — uploads are disabled. Start the server to ingest documents.
        </div>
      )}

      <div className="split-main">
        <div
          className={`dropzone ${drag ? "dragging" : ""} ${!online ? "disabled" : ""}`}
          onClick={() => { if (online) fileRef.current?.click(); }}
          onDragOver={(e) => { if (online) { e.preventDefault(); setDrag(true); } }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); if (online) addFiles(e.dataTransfer.files); }}
          style={{
            cursor: !online ? "not-allowed" : uploading ? "default" : "pointer",
            opacity: !online || uploading ? 0.6 : 1,
          }}>
          <input ref={fileRef} type="file" multiple
            accept=".csv,.pdf,.ofx,.qfx,.tsv,.txt"
            onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }}
            style={{ display: "none" }}
            disabled={uploading || !online}/>
          {uploading ? (
            <span className="spinner" style={{ width: 28, height: 28, borderWidth: 2.5, borderColor: "var(--ink-3)", borderTopColor: "transparent" }}/>
          ) : (
            <I.upload className="icon" size={32} sw={1.25}/>
          )}
          <div style={{ fontSize: 15, fontWeight: 500 }}>
            {!online ? "Backend offline — uploads disabled" : uploading ? "Uploading…" : "Drop files or click to browse"}
          </div>
          <div className="muted" style={{ fontSize: 12.5, maxWidth: 380 }}>
            Supported: CSV, OFX, QFX, PDF statements from Chase, Wells Fargo, Capital One, SoFi, Schwab, and 60+ others.
          </div>
          {online && !uploading && (
            <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
              <button className="btn primary" onClick={(e) => { e.stopPropagation(); fileRef.current?.click(); }}><I.upload size={13}/> Choose files</button>
            </div>
          )}
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 8, fontSize: 11, color: "var(--ink-3)" }}>
            <I.lock size={11}/>
            {online ? "Files sent to local backend · not stored in cloud" : "Start the backend to enable uploads"}
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
                  <div style={{ fontSize: 12, color: "var(--ink-3)" }}>
                    {p.key === "analyze" && p.status === "running" && activeAgent
                      ? <>Running <strong style={{ color: "var(--info)" }}>{activeAgent.replace(/_/g, ' ')}</strong> …</>
                      : p.desc}
                  </div>
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
            <div className="card-title">Sources · {docs.length}</div>
            <div className="card-sub">
              {docs.length > 0
                ? `${totalRows.toLocaleString()} rows indexed across ${uniqueSources} source${uniqueSources !== 1 ? "s" : ""}`
                : "No documents uploaded this session"}
            </div>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <button className="btn ghost" style={{ fontSize: 12 }}><I.filter size={12}/> Filter</button>
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
            {docs.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", padding: "40px 24px", color: "var(--ink-4)" }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
                    <I.upload size={24} style={{ color: "var(--ink-4)" }}/>
                    <div style={{ fontSize: 13 }}>
                      {online
                        ? "No documents uploaded yet. Drop a statement above to get started."
                        : "Backend offline — start the server, then upload documents."}
                    </div>
                  </div>
                </td>
              </tr>
            ) : (
              docs.map((d, i) => (
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
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

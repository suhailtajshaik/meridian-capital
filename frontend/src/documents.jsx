import React from 'react';
import { I } from './icons.jsx';
import { streamUpload, listDocuments, deleteDocument } from './lib/api.js';
import { getSessionId } from './lib/session.js';

/* Documents / ingestion view */

export function StatusPill({ status }) {
  if (status === "uploaded") return <span className="tag"><I.check size={10}/> Uploaded</span>;
  if (status === "ready") return <span className="tag pos"><I.check size={10}/> Analyzed</span>;
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
  { key: "parse",     step: "Uploading",   desc: "Reading your file" },
  { key: "normalize", step: "Processing",  desc: "Organizing your data" },
  { key: "redact",    step: "Securing",    desc: "Protecting your privacy" },
  { key: "index",     step: "Saving",      desc: "Saving to your device" },
  { key: "analyze",   step: "Reviewing",   desc: "Reviewing your finances" },
];

const STAGE_INDEX = Object.fromEntries(PIPELINE_STEPS.map((s, i) => [s.key, i]));

function getPipelineStatus(activeStep) {
  return PIPELINE_STEPS.map((p, i) => {
    if (activeStep < 0) return { ...p, status: "idle" };
    if (i < activeStep) return { ...p, status: "active" };
    if (i === activeStep) return { ...p, status: "running" };
    return { ...p, status: "queued" };
  });
}

function sourceFromName(n) {
  const s = n.toLowerCase();
  if (s.includes("chase")) return "Chase";
  if (s.includes("capital")) return "Capital One";
  if (s.includes("wells")) return "Wells Fargo";
  if (s.includes("sofi")) return "SoFi";
  if (s.includes("schwab")) return "Schwab";
  if (s.includes("honda")) return "Honda Financial";
  return "Uploaded";
}

function formatSize(b) {
  if (b < 1024) return b + " B";
  if (b < 1024 * 1024) return Math.round(b / 1024) + " KB";
  return (b / 1024 / 1024).toFixed(1) + " MB";
}

export function Documents({ online, onNav, uploadFile: apiUpload, uploading, uploadError, refresh, snapshotStatus, startPolling }) {

  const [drag, setDrag] = React.useState(false);
  const [docs, setDocs] = React.useState([]);
  const fileRef = React.useRef(null);

  // stepByDoc: Map<docKey, number> — per-file pipeline step (-1=idle, 0-4=stage, 5=done)
  const [stepByDoc, setStepByDoc] = React.useState({});
  const [agentByDoc, setAgentByDoc] = React.useState({});

  const sessionId = getSessionId();

  const loadDocs = React.useCallback(async () => {
    try {
      const data = await listDocuments(sessionId);
      const today = new Date().toLocaleDateString(undefined, { month: "short", day: "numeric" });
      const serverDocs = (data.documents ?? []).map((d) => ({
        name: d.name,
        size: formatSize(d.size ?? 0),
        added: d.uploaded_at
          ? new Date(d.uploaded_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })
          : today,
        status: 'ready',
        rows: d.rows ?? 0,
        source: sourceFromName(d.name),
        table_name: d.table_name,
        sha256: d.sha256,
      }));
      setDocs((prev) => {
        const inFlight = prev.filter((d) => !d.sha256 && d._key);
        const serverWithKeys = serverDocs.map((d) => {
          const optimistic = prev.find((p) => p.sha256 === d.sha256);
          if (!optimistic) return d;
          const merged = { ...d };
          if (optimistic._key) merged._key = optimistic._key;
          if (optimistic.status === 'uploaded') merged.status = 'uploaded';
          return merged;
        });
        return [...inFlight, ...serverWithKeys];
      });
    } catch {
      // backend offline — leave docs as-is
    }
  }, [sessionId]);

  React.useEffect(() => { loadDocs(); }, [loadDocs]);

  // When snapshot finishes computing (views refreshed), promote 'uploaded' docs to 'indexed'.
  React.useEffect(() => {
    if (snapshotStatus !== 'computing' && snapshotStatus !== null) {
      setDocs(prev => {
        if (!prev.some(d => d.status === 'uploaded')) return prev;
        return prev.map(d => d.status === 'uploaded' ? { ...d, status: 'ready' } : d);
      });
    }
  }, [snapshotStatus]);

  // Derive the "most recent active step" across all in-flight uploads for the Pipeline panel.
  // Falls back to the "analyze" step while the background snapshot is computing so the
  // pipeline never goes idle during the ~30-second AI analysis window.
  const globalActiveStep = React.useMemo(() => {
    const steps = Object.values(stepByDoc);
    const inFlight = steps.filter(s => s >= 0 && s < PIPELINE_STEPS.length);
    if (inFlight.length) return Math.max(...inFlight);
    if (snapshotStatus === 'computing') return PIPELINE_STEPS.length - 1;
    return -1;
  }, [stepByDoc, snapshotStatus]);

  const globalActiveAgent = React.useMemo(() => {
    const agents = Object.values(agentByDoc).filter(Boolean);
    return agents[agents.length - 1] ?? null;
  }, [agentByDoc]);

  const ingestPipeline = getPipelineStatus(globalActiveStep);

  const addFiles = async (fileList) => {
    if (!online) return;
    const files = Array.from(fileList || []);
    if (!files.length) return;

    // Add optimistic in-progress rows immediately so the table shows each file.
    const docKeys = files.map((f) => `${f.name}__${Date.now()}__${Math.random()}`);

    setDocs((prev) => {
      const incoming = files.map((f, idx) => ({
        name: f.name,
        size: formatSize(f.size ?? 0),
        added: new Date().toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        status: 'parsing',
        rows: 0,
        source: sourceFromName(f.name),
        table_name: null,
        sha256: null,
        _key: docKeys[idx],
      }));
      return [...incoming, ...prev];
    });

    setStepByDoc((prev) => {
      const next = { ...prev };
      docKeys.forEach((k) => { next[k] = 0; });
      return next;
    });

    // Upload all files concurrently; errors are isolated per file.
    await Promise.all(files.map(async (file, idx) => {
      const docKey = docKeys[idx];

      const updateStep = (step) =>
        setStepByDoc((prev) => ({ ...prev, [docKey]: step }));

      const updateStatus = (status) =>
        setDocs((prev) => prev.map((d) => d._key === docKey ? { ...d, status } : d));

      const updateAgent = (agent) =>
        setAgentByDoc((prev) => ({ ...prev, [docKey]: agent }));

      try {
        await streamUpload({
          file,
          sessionId,
          onEvent: (event) => {
            if (event.type === 'stage' && event.stage in STAGE_INDEX) {
              updateStep(STAGE_INDEX[event.stage]);
              const statusMap = { parse: 'parsing', normalize: 'normalizing', redact: 'redacting', index: 'indexing', analyze: 'indexing' };
              if (statusMap[event.stage]) updateStatus(statusMap[event.stage]);
              if (event.stage !== 'analyze') updateAgent(null);
            } else if (event.type === 'trace') {
              const agent = event.event?.agent;
              const t = event.event?.type;
              if (agent && (t === 'agent_start' || t === 'tool_call')) updateAgent(agent);
            } else if (event.type === 'ingest_complete') {
              const doc = event.document || {};
              setDocs((prev) => prev.map((d) => d._key === docKey ? {
                ...d,
                rows: doc.rows ?? event.rows ?? d.rows,
                table_name: doc.table_name ?? event.table_name ?? d.table_name,
                sha256: doc.sha256 ?? d.sha256,
                size: doc.size != null ? formatSize(doc.size) : d.size,
                status: 'uploaded',
              } : d));
              updateStep(STAGE_INDEX["analyze"]);
              updateAgent(null);
              loadDocs().catch(() => {});
              startPolling?.();
            } else if (event.type === 'snapshot_pending') {
              startPolling?.();
            } else if (event.type === 'snapshot') {
              updateStep(PIPELINE_STEPS.length);
              updateAgent(null);
              updateStatus('ready');
              loadDocs().catch(() => {});
              refresh().catch(() => {});
            }
          },
        });
      } catch {
        updateStep(-1);
        updateStatus('error');
        updateAgent(null);
      } finally {
        loadDocs().catch(() => {});
      }

      setTimeout(() => {
        updateStep(-1);
        updateAgent(null);
        setStepByDoc((prev) => {
          const next = { ...prev };
          delete next[docKey];
          return next;
        });
        setAgentByDoc((prev) => {
          const next = { ...prev };
          delete next[docKey];
          return next;
        });
      }, 1200);
    }));
  };

  const handleDelete = async (doc) => {
    if (!doc.sha256) {
      if (doc._key) setDocs((prev) => prev.filter((d) => d._key !== doc._key));
      return;
    }
    setDocs((prev) => prev.filter((d) => d.sha256 !== doc.sha256));
    try {
      await deleteDocument(sessionId, doc.sha256);
    } catch { /* fall through — we'll reconcile via loadDocs */ }
    await loadDocs();
    refresh().catch(() => {});
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

      <div style={{ fontSize: 12, color: "var(--ink-4)", marginBottom: 10, letterSpacing: "0.02em" }}>
        One upload powers all 4 advisors.
      </div>

      <div className="split-main">
        <div
          className={`dropzone ${drag ? "dragging" : ""} ${!online ? "disabled" : ""}`}
          onClick={() => { if (online) fileRef.current?.click(); }}
          onDragOver={(e) => { if (online) { e.preventDefault(); setDrag(true); } }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); if (online) addFiles(e.dataTransfer.files); }}
          style={{
            cursor: !online ? "not-allowed" : "pointer",
            opacity: !online ? 0.6 : 1,
          }}>
          <input ref={fileRef} type="file" multiple
            accept=".csv,.pdf,.ofx,.qfx,.tsv,.txt"
            onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }}
            style={{ display: "none" }}
            disabled={!online}/>
          <I.upload className="icon" size={32} sw={1.25}/>
          <div style={{ fontSize: 15, fontWeight: 500 }}>
            {!online ? "Backend offline — uploads disabled" : "Drop files or click to browse"}
          </div>
          <div className="muted" style={{ fontSize: 12.5, maxWidth: 380 }}>
            Supported: CSV, OFX, QFX, PDF statements from Chase, Wells Fargo, Capital One, SoFi, Schwab, and 60+ others.
          </div>
          {online && (
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
                    {p.key === "analyze" && p.status === "running"
                      ? globalActiveAgent
                        ? <>Running <strong style={{ color: "var(--info)" }}>{globalActiveAgent.replace(/_/g, ' ')}</strong> …</>
                        : <>Advisors analyzing your finances<span style={{ color: "var(--ink-4)" }}> (~30s)</span></>
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
                : "Documents persist across sessions"}
            </div>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <button className="btn ghost" style={{ fontSize: 12 }}><I.filter size={12}/> Filter</button>
          </div>
        </div>

        {snapshotStatus === "computing" && (
          <div style={{
            marginBottom: 12, padding: "8px 12px",
            borderRadius: 8, background: "var(--info-tint)",
            border: "1px solid var(--info)",
            fontSize: 12.5, color: "var(--ink-2)",
            display: "flex", gap: 8, alignItems: "center",
          }}>
            <span className="spinner" style={{ width: 11, height: 11, borderColor: "var(--info)", borderTopColor: "transparent", flexShrink: 0 }}/>
            Advisors re-analyzing your data… (this takes ~30s)
          </div>
        )}

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
                <tr key={d._key ?? d.sha256 ?? i}>
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
                  <td>
                    <button
                      className="icon-btn"
                      style={{ width: 26, height: 26 }}
                      title="Delete document"
                      onClick={() => handleDelete(d)}
                    >
                      <I.x size={13}/>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

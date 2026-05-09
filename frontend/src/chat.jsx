import React from 'react';
import { I } from './icons.jsx';
import { AGENT_META, CHAT_SEED } from './data.js';

/* Chat panel — supervisor + sub-agent threading, agent attribution chips */

export function AgentChip({ agent, prominent }) {
  const meta = AGENT_META[agent];
  if (!meta) return null;
  if (prominent) {
    return (
      <span style={{
        display: "inline-flex", alignItems: "center", gap: 6,
        padding: "3px 8px", borderRadius: 6,
        background: "var(--surface-2)", border: "1px solid var(--line)",
        fontSize: 11, color: "var(--ink-2)", fontWeight: 500,
      }}>
        <span className="agent-dot" style={{ background: meta.color }}/> {meta.label}
      </span>
    );
  }
  return (
    <span className="agent-chip">
      <span className="agent-dot" style={{ background: meta.color }}/> {meta.label}
    </span>
  );
}

export function RoutingPill({ agents }) {
  return (
    <div className="routing">
      <I.sparkle size={12}/>
      <span style={{ marginRight: 6 }}>Supervisor routed to</span>
      {agents.map((a, i) => (
        <span key={a} style={{ display: "inline-flex", alignItems: "center", gap: 4, marginRight: 4 }}>
          <span className="agent-dot" style={{ background: AGENT_META[a].color }}/>
          <strong style={{ fontWeight: 500 }}>{AGENT_META[a].label}</strong>
          {i < agents.length - 1 && <span style={{ color: "var(--ink-3)" }}>·</span>}
        </span>
      ))}
    </div>
  );
}

export function MD({ text }) {
  // tiny **bold** parser
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return <>{parts.map((p, i) => p.startsWith("**") ? <strong key={i}>{p.slice(2, -2)}</strong> : <span key={i}>{p}</span>)}</>;
}

export function AgentDots({ trace, onClick }) {
  if (!trace) return null;
  const agents = [...new Set(trace.steps.filter(s => s.kind === "agent").map(s => s.agent))];
  return (
    <button onClick={onClick} style={{
      all: "unset", cursor: "pointer",
      display: "inline-flex", alignItems: "center", gap: 6,
      fontSize: 10.5, color: "var(--ink-4)", marginTop: 6,
    }}>
      <I.sparkle size={10}/>
      <span>{agents.length} agent{agents.length===1?"":"s"} · {(trace.totalMs/1000).toFixed(1)}s · {trace.toolCount} tool call{trace.toolCount===1?"":"s"}</span>
      <span style={{ display: "inline-flex", gap: 3, marginLeft: 2 }}>
        {agents.map((a) => (
          <span key={a} style={{ width: 6, height: 6, borderRadius: 999, background: AGENT_META[a]?.color || "var(--ink-4)" }}/>
        ))}
      </span>
      <span style={{ marginLeft: 2 }}>How I answered this ›</span>
    </button>
  );
}

export function Trace({ trace }) {
  if (!trace) return null;
  return (
    <div style={{
      marginTop: 10, borderRadius: 8,
      border: "1px solid var(--line)",
      background: "var(--surface-2)",
      overflow: "hidden",
    }}>
      <div style={{
        padding: "8px 12px", borderBottom: "1px solid var(--line)",
        fontSize: 10.5, color: "var(--ink-3)", letterSpacing: "0.06em", textTransform: "uppercase",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <span>Orchestration trace</span>
        <span className="mono" style={{ fontSize: 10 }}>{(trace.totalMs/1000).toFixed(2)}s total</span>
      </div>
      <div style={{ padding: 10, display: "flex", flexDirection: "column", gap: 0 }}>
        {trace.steps.map((s, i) => {
          const isLast = i === trace.steps.length - 1;
          const meta = s.kind === "agent" ? AGENT_META[s.agent] : null;
          const color = s.kind === "supervisor" ? "var(--ink)"
                      : s.kind === "synth" ? "var(--ink-2)"
                      : meta?.color || "var(--ink-3)";
          const label = s.kind === "supervisor" ? "Supervisor"
                      : s.kind === "synth" ? "Synthesizer"
                      : meta?.label || s.agent;
          return (
            <div key={i} style={{ display: "grid", gridTemplateColumns: "16px 1fr auto", gap: 10, position: "relative" }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", paddingTop: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: 999, background: color, flexShrink: 0 }}/>
                {!isLast && <span style={{ flex: 1, width: 1, background: "var(--line)", marginTop: 2, marginBottom: -2, minHeight: 16 }}/>}
              </div>
              <div style={{ paddingBottom: isLast ? 2 : 14 }}>
                <div style={{ fontSize: 12, fontWeight: 500, color: "var(--ink)" }}>{label}</div>
                {s.title && <div style={{ fontSize: 12, color: "var(--ink-2)", marginTop: 2 }}>{s.title}</div>}
                {s.details && (
                  <ul style={{ margin: "4px 0 0", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 2 }}>
                    {s.details.map((d, j) => (
                      <li key={j} style={{ fontSize: 11.5, color: "var(--ink-3)", paddingLeft: 10, position: "relative" }}>
                        <span style={{ position: "absolute", left: 0, top: 7, width: 4, height: 1, background: "var(--ink-4)" }}/>{d}
                      </li>
                    ))}
                  </ul>
                )}
                {s.routes && (
                  <div style={{ display: "flex", gap: 4, marginTop: 6, flexWrap: "wrap" }}>
                    {s.routes.map((r) => (
                      <span key={r} style={{
                        display: "inline-flex", alignItems: "center", gap: 4,
                        fontSize: 10.5, padding: "2px 6px", borderRadius: 4,
                        background: "var(--surface)", border: "1px solid var(--line)",
                        color: "var(--ink-2)",
                      }}>
                        <span style={{ width: 5, height: 5, borderRadius: 999, background: AGENT_META[r]?.color }}/>
                        {AGENT_META[r]?.label}
                      </span>
                    ))}
                  </div>
                )}
                {s.tools && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 3, marginTop: 6 }}>
                    {s.tools.map((t, j) => (
                      <div key={j} className="mono" style={{
                        fontSize: 10.5, color: "var(--ink-2)",
                        padding: "4px 8px", borderRadius: 4,
                        background: "var(--surface)", border: "1px solid var(--line)",
                        display: "flex", justifyContent: "space-between", gap: 8,
                      }}>
                        <span><span style={{ color: color }}>{t.name}</span>(<span style={{ color: "var(--ink-3)" }}>{t.args}</span>)</span>
                        <span style={{ color: "var(--ink-4)" }}>→ {t.result}</span>
                      </div>
                    ))}
                  </div>
                )}
                {s.conclusion && (
                  <div style={{ fontSize: 11.5, color: "var(--ink-2)", marginTop: 6, fontStyle: "italic" }}>“{s.conclusion}”</div>
                )}
                {s.summary && (
                  <div style={{ fontSize: 11.5, color: "var(--ink-2)", marginTop: 2 }}>{s.summary}</div>
                )}
              </div>
              <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)", paddingTop: 4 }}>{s.ms}ms</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function MessageWithTrace({ m, agent, prominentAgents, send }) {
  const [open, setOpen] = React.useState(false);
  return (
    <div className="msg-agent fade-in">
      <AgentChip agent={agent} prominent={prominentAgents}/>
      <div className="msg-body">
        <MD text={m.text}/>
        {m.structured?.kind === "recommend-payoff" && <PayoffActionCard data={m.structured}/>}
        {m.actions && (
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 10 }}>
            {m.actions.map((a, j) => (
              <button key={j} className="suggestion" onClick={() => send(a)}>{a}</button>
            ))}
          </div>
        )}
        {m.trace && (
          <>
            {!open && <div><AgentDots trace={m.trace} onClick={() => setOpen(true)}/></div>}
            {open && <Trace trace={m.trace}/>}
            {open && (
              <button onClick={() => setOpen(false)} style={{
                all: "unset", cursor: "pointer", marginTop: 6,
                fontSize: 10.5, color: "var(--ink-4)",
              }}>Hide trace ‹</button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export function PayoffActionCard({ data }) {
  return (
    <div style={{
      marginTop: 6, padding: 12,
      border: "1px solid var(--line)", borderRadius: 8,
      background: "var(--surface)",
    }}>
      <div style={{ fontSize: 11, color: "var(--ink-3)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6 }}>
        Recommended action
      </div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 12 }}>
        <div>
          <div style={{ fontSize: 13, color: "var(--ink-3)" }}>Pay toward</div>
          <div style={{ fontSize: 14, fontWeight: 500 }}>{data.target}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="num" style={{ fontSize: 22, lineHeight: 1 }}>${data.amount.toLocaleString()}</div>
          <div style={{ fontSize: 11, color: "var(--positive)", marginTop: 2 }}>−${data.interestSaved} interest</div>
        </div>
      </div>
      <div style={{ display: "flex", gap: 6, marginTop: 10 }}>
        <button className="btn primary" style={{ padding: "5px 10px", fontSize: 12 }}>Schedule transfer</button>
        <button className="btn ghost" style={{ padding: "5px 10px", fontSize: 12 }}>See full plan</button>
      </div>
    </div>
  );
}

export function ChatPanel({ open, onClose, prominentAgents }) {
  const [draft, setDraft] = React.useState("");
  const [thread, setThread] = React.useState(CHAT_SEED);
  const streamRef = React.useRef(null);

  React.useEffect(() => {
    if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight;
  }, [thread]);

  const send = (text) => {
    const t = (text ?? draft).trim();
    if (!t) return;
    setDraft("");
    const next = [...thread, { role: "user", text: t }];
    setThread(next);
    // Fake supervisor + agent response
    setTimeout(() => {
      setThread([...next,
        { role: "supervisor", routing: ["budget", "savings"], text: "Routing to Budget Advisor and Savings Strategy." },
      ]);
    }, 350);
    setTimeout(() => {
      setThread((cur) => [...cur,
        { role: "agent", agent: "budget",
          text: "You're **$136 over** in dining out and **$140 over** on shopping this month. Pulling those back to budget would free up about **$276** for goals.",
          trace: {
            totalMs: 980, toolCount: 4,
            steps: [
              { kind: "supervisor", title: "Decomposed into 2 sub-questions", ms: 220,
                details: ["Where is spending exceeding budget?", "How much can be redirected without lifestyle impact?"],
                routes: ["budget", "savings"] },
              { kind: "agent", agent: "budget", ms: 480,
                tools: [
                  { name: "query_transactions", args: 'month: "May 2026"', result: "127 rows" },
                  { name: "compare_to_budget", args: "by category", result: "2 categories over" },
                  { name: "rag_retrieve", args: '"recurring discretionary"', result: "rows 18, 44, 61" },
                ],
                conclusion: "Dining +$136, Shopping +$140 — both discretionary." },
              { kind: "agent", agent: "savings", ms: 200,
                tools: [{ name: "project_goal_eta", args: "extra: $276/mo", result: "−2mo to kitchen reno" }],
                conclusion: "Redirecting $276 cuts kitchen ETA by 2 months." },
              { kind: "synth", ms: 80, summary: "Merged 2 outputs · single recommendation · high confidence" },
            ],
          },
        },
        { role: "agent", agent: "supervisor",
          text: "**Synthesis** — redirect that surplus to the kitchen-reno fund to cut its ETA by 2 months.",
          actions: ["Apply", "Show alternatives"],
        },
      ]);
    }, 1100);
  };

  const suggestions = [
    "How am I doing this month?",
    "When can I afford the kitchen reno?",
    "What if I lose my job?",
    "Show me my biggest leak",
  ];

  return (
    <aside className={`chat-panel ${open ? "" : "collapsed"}`}>
      <div className="chat-head">
        <div className="chat-orb"/>
        <div style={{ flex: 1 }}>
          <div className="chat-title">Advisor</div>
          <div className="chat-sub">Supervisor + 4 specialists · context: 6 docs</div>
        </div>
        <button className="icon-btn" onClick={onClose} title="Hide chat"><I.x size={14}/></button>
      </div>

      <div className="chat-stream" ref={streamRef}>
        <div className="agent-chip" style={{ alignSelf: "center", color: "var(--ink-4)", fontSize: 10.5, letterSpacing: "0.06em" }}>
          <I.lock size={10}/> ON-DEVICE · NOTHING LEAVES THIS MACHINE
        </div>

        {thread.map((m, i) => {
          if (m.role === "user") return (
            <div key={i} className="msg-user fade-in">{m.text}</div>
          );
          if (m.role === "supervisor" && m.routing) return (
            <div key={i} className="fade-in"><RoutingPill agents={m.routing}/></div>
          );
          // agent or supervisor synthesis
          const agent = m.agent ?? "supervisor";
          return <MessageWithTrace key={i} m={m} agent={agent} prominentAgents={prominentAgents} send={send}/>;
        })}
      </div>

      <div className="chat-input-wrap">
        <div className="chat-suggestions">
          {suggestions.map((s) => (
            <button key={s} className="suggestion" onClick={() => send(s)}>{s}</button>
          ))}
        </div>
        <div className="chat-input">
          <textarea
            placeholder="Ask anything about your money…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            rows={1}
          />
          <button className="send-btn" onClick={() => send()} title="Send">
            <I.send size={14} stroke="currentColor"/>
          </button>
        </div>
        <div style={{ fontSize: 10.5, color: "var(--ink-4)", marginTop: 6, display: "flex", alignItems: "center", gap: 4 }}>
          <I.shield size={10}/> Account numbers redacted before retrieval · No PII leaves your vault
        </div>
      </div>
    </aside>
  );
}


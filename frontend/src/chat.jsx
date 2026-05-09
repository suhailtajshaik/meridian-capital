import React from 'react';
import { I } from './icons.jsx';
import { AGENT_META } from './data.js';
import { useAgentStream } from './hooks/useAgentStream.js';

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
  const validAgents = (agents || []).filter((a) => AGENT_META[a]);
  return (
    <div className="routing">
      <I.sparkle size={12}/>
      <span style={{ marginRight: 6 }}>Supervisor routed to</span>
      {validAgents.map((a, i) => (
        <span key={a} style={{ display: "inline-flex", alignItems: "center", gap: 4, marginRight: 4 }}>
          <span className="agent-dot" style={{ background: AGENT_META[a].color }}/>
          <strong style={{ fontWeight: 500 }}>{AGENT_META[a].label}</strong>
          {i < validAgents.length - 1 && <span style={{ color: "var(--ink-3)" }}>·</span>}
        </span>
      ))}
    </div>
  );
}

export function MD({ text }) {
  // tiny **bold** parser
  const parts = (text ?? '').split(/(\*\*[^*]+\*\*)/g);
  return <>{parts.map((p, i) => p.startsWith("**") ? <strong key={i}>{p.slice(2, -2)}</strong> : <span key={i}>{p}</span>)}</>;
}

/* ─── Trace renderer for live TraceEvent[] from the backend ──────────────── */
export function AgentDots({ trace, onClick }) {
  if (!trace) return null;

  // Live: trace is TraceEvent[]
  const events = trace;
  if (!Array.isArray(events) || !events.length) return null;
  const agentNames = [...new Set(events.filter(e => e.agent).map(e => e.agent))];
  const toolCalls = events.filter(e => e.type === 'tool_call').length;
  return (
    <button onClick={onClick} style={{
      all: "unset", cursor: "pointer",
      display: "inline-flex", alignItems: "center", gap: 6,
      fontSize: 10.5, color: "var(--ink-4)", marginTop: 6,
    }}>
      <I.sparkle size={10}/>
      <span>{agentNames.length} agent{agentNames.length===1?"":"s"} · {toolCalls} tool call{toolCalls===1?"":"s"}</span>
      <span style={{ display: "inline-flex", gap: 3, marginLeft: 2 }}>
        {agentNames.map((a) => (
          <span key={a} style={{ width: 6, height: 6, borderRadius: 999, background: AGENT_META[a]?.color || "var(--ink-4)" }}/>
        ))}
      </span>
      <span style={{ marginLeft: 2 }}>How I answered this ›</span>
    </button>
  );
}

/* ─── Trace renderer for live TraceEvent[] from the backend ─────────────── */
function TraceEventRow({ event, isLast }) {
  const [payloadOpen, setPayloadOpen] = React.useState(false);
  const meta = event.agent ? AGENT_META[event.agent] : null;
  const color = meta?.color || "var(--ink-3)";
  const agentLabel = meta?.label || event.agent || "System";

  const typeLabel = {
    agent_start: "Start",
    tool_call: "Tool call",
    tool_result: "Tool result",
    agent_complete: "Complete",
    synth: "Synthesizer",
  }[event.type] || event.type;

  const hasPayload = event.payload && Object.keys(event.payload).length > 0;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "16px 1fr auto", gap: 10, position: "relative" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", paddingTop: 4 }}>
        <span style={{ width: 8, height: 8, borderRadius: 999, background: color, flexShrink: 0 }}/>
        {!isLast && <span style={{ flex: 1, width: 1, background: "var(--line)", marginTop: 2, marginBottom: -2, minHeight: 16 }}/>}
      </div>
      <div style={{ paddingBottom: isLast ? 2 : 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ fontSize: 12, fontWeight: 500, color: "var(--ink)" }}>{agentLabel}</div>
          <span style={{
            fontSize: 10, padding: "1px 5px", borderRadius: 3,
            background: "var(--surface)", border: "1px solid var(--line)",
            color: "var(--ink-3)", letterSpacing: "0.04em",
          }}>{typeLabel}</span>
        </div>
        {hasPayload && (
          <button
            onClick={() => setPayloadOpen((o) => !o)}
            style={{
              all: "unset", cursor: "pointer",
              fontSize: 10.5, color: "var(--ink-4)", marginTop: 4,
              display: "inline-flex", alignItems: "center", gap: 4,
            }}
          >
            <span style={{
              display: "inline-block", width: 8, height: 8,
              borderRight: "1.5px solid currentColor", borderBottom: "1.5px solid currentColor",
              transform: payloadOpen ? "rotate(-135deg) translate(-2px,-2px)" : "rotate(45deg)",
              transition: "transform 0.15s",
            }}/>
            {payloadOpen ? "Hide payload" : "Show payload"}
          </button>
        )}
        {payloadOpen && hasPayload && (
          <pre className="mono" style={{
            margin: "6px 0 0", padding: "6px 8px",
            fontSize: 10.5, color: "var(--ink-2)",
            background: "var(--surface)", border: "1px solid var(--line)",
            borderRadius: 4, overflowX: "auto", whiteSpace: "pre-wrap",
            wordBreak: "break-word", maxHeight: 220,
          }}>
            {JSON.stringify(event.payload, null, 2)}
          </pre>
        )}
      </div>
      <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)", paddingTop: 4, whiteSpace: "nowrap" }}>
        {event.timestamp ? new Date(event.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : ""}
      </div>
    </div>
  );
}

function TraceLive({ events }) {
  const agentNames = [...new Set(events.filter(e => e.agent).map(e => e.agent))];
  const toolCalls = events.filter(e => e.type === 'tool_call').length;

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
        <span className="mono" style={{ fontSize: 10 }}>
          {agentNames.length} agent{agentNames.length !== 1 ? "s" : ""} · {toolCalls} tool call{toolCalls !== 1 ? "s" : ""}
        </span>
      </div>
      <div style={{ padding: 10, display: "flex", flexDirection: "column", gap: 0 }}>
        {events.map((event, i) => (
          <TraceEventRow key={i} event={event} isLast={i === events.length - 1}/>
        ))}
      </div>
    </div>
  );
}

/**
 * Trace component — renders live TraceEvent[] from the backend.
 */
export function Trace({ trace }) {
  if (!trace) return null;
  if (!Array.isArray(trace) || !trace.length) return null;
  return <TraceLive events={trace}/>;
}

export function MessageWithTrace({ m, agent, prominentAgents, send }) {
  const [open, setOpen] = React.useState(false);
  const content = m.content ?? m.text ?? '';
  const resolvedAgent = agent ?? m.agent;

  return (
    <div className="msg-agent fade-in">
      <AgentChip agent={resolvedAgent} prominent={prominentAgents}/>
      <div className="msg-body">
        <MD text={content}/>
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
        {/* Show streaming indicator while trace events are accumulating */}
        {m._streaming && !m.trace?.length && (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 5, marginTop: 6, fontSize: 11, color: "var(--ink-4)" }}>
            <span className="spinner" style={{ width: 9, height: 9, borderColor: "currentColor", borderTopColor: "transparent" }}/>
            Thinking…
          </span>
        )}
        {m._streaming && m.trace?.length > 0 && (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 5, marginTop: 6, fontSize: 11, color: "var(--ink-4)" }}>
            <span className="spinner" style={{ width: 9, height: 9, borderColor: "currentColor", borderTopColor: "transparent" }}/>
            {m.trace[m.trace.length - 1].agent || "Processing"}…
          </span>
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

/* ─── Prominent offline banner — shown when backend is unreachable ─────────── */
function BackendOfflineChatBanner() {
  return (
    <div style={{
      margin: "8px 12px",
      padding: "12px 14px",
      borderRadius: 8,
      background: "var(--negative-tint)",
      border: "1px solid var(--negative)",
      display: "flex", alignItems: "flex-start", gap: 10,
      fontSize: 12.5, color: "var(--ink-2)",
    }}>
      <I.alert size={14} style={{ color: "var(--negative)", flexShrink: 0, marginTop: 1 }}/>
      <div>
        <div style={{ fontWeight: 600, color: "var(--negative)", marginBottom: 4 }}>Backend unreachable</div>
        <div style={{ lineHeight: 1.5 }}>
          Cannot connect to{" "}
          <code style={{ fontFamily: "var(--font-mono)", fontSize: 11, background: "rgba(0,0,0,0.06)", padding: "1px 4px", borderRadius: 3 }}>
            http://localhost:8000
          </code>
          . Run{" "}
          <code style={{ fontFamily: "var(--font-mono)", fontSize: 11, background: "rgba(0,0,0,0.06)", padding: "1px 4px", borderRadius: 3 }}>
            docker compose up
          </code>
          {" "}from the repo root to start the backend.
        </div>
      </div>
    </div>
  );
}

/* ─── Streaming error notice ─────────────────────────────────────────────── */
function StreamError({ error, onDismiss }) {
  if (!error) return null;
  return (
    <div style={{
      margin: "8px 12px 0",
      padding: "7px 12px",
      borderRadius: 7,
      background: "var(--negative-tint)",
      border: "1px solid var(--negative)",
      display: "flex", alignItems: "center", gap: 8,
      fontSize: 11.5, color: "var(--ink-2)",
    }}>
      <I.alert size={12} style={{ color: "var(--negative)", flexShrink: 0 }}/>
      <span style={{ flex: 1 }}>Chat error: {error.message}</span>
      <button onClick={onDismiss} style={{ all: "unset", cursor: "pointer", color: "var(--ink-3)", fontSize: 13, lineHeight: 1 }}>✕</button>
    </div>
  );
}

/* ─── ChatPanel ──────────────────────────────────────────────────────────── */
export function ChatPanel({ open, onClose, prominentAgents, online, model }) {
  const { messages, sendMessage, isStreaming, activeAgent, error, clear } = useAgentStream();

  const [draft, setDraft] = React.useState("");
  const [streamError, setStreamError] = React.useState(null);
  const streamRef = React.useRef(null);

  // Propagate streaming errors from the hook into local display state
  React.useEffect(() => {
    if (error) setStreamError(error);
  }, [error]);

  // Auto-scroll on new messages
  React.useEffect(() => {
    if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight;
  }, [messages]);

  const send = (text) => {
    if (!online) return;
    const t = (text ?? draft).trim();
    if (!t || isStreaming) return;
    setDraft("");
    setStreamError(null);
    sendMessage(t);
  };

  // Thread: all messages are live
  const thread = messages.map((m) => ({
    ...m,
    text: m.text ?? m.content ?? '',
  }));

  const suggestions = [
    "How am I doing this month?",
    "What's my highest-rate debt?",
    "How long until I'm debt-free?",
    "Where can I cut spending?",
  ];

  // Sub-title reflects backend state
  const subTitle = online
    ? `Connected${model ? ` · ${model}` : ""} · Supervisor + 4 specialists`
    : "Backend offline";

  const inputDisabled = !online || isStreaming;

  return (
    <aside className={`chat-panel ${open ? "" : "collapsed"}`}>
      <div className="chat-head">
        <div className="chat-orb" style={{ background: online ? undefined : "var(--negative)" }}/>
        <div style={{ flex: 1 }}>
          <div className="chat-title">Advisor</div>
          <div className="chat-sub">{subTitle}</div>
        </div>
        {online && messages.length > 0 && (
          <button
            className="icon-btn"
            onClick={clear}
            title="Clear conversation"
            style={{ fontSize: 10, padding: "2px 6px", color: "var(--ink-4)" }}
          >
            <I.refresh size={12}/>
          </button>
        )}
        <button className="icon-btn" onClick={onClose} title="Hide chat"><I.x size={14}/></button>
      </div>

      {!online && <BackendOfflineChatBanner/>}
      <StreamError error={streamError} onDismiss={() => setStreamError(null)}/>

      {/* Active agent indicator while streaming */}
      {online && isStreaming && activeAgent && (
        <div style={{
          padding: "4px 14px",
          fontSize: 11, color: "var(--ink-4)",
          display: "flex", alignItems: "center", gap: 6,
          borderBottom: "1px solid var(--line)",
        }}>
          <span className="spinner" style={{ width: 8, height: 8, borderColor: AGENT_META[activeAgent]?.color || "currentColor", borderTopColor: "transparent" }}/>
          <span style={{ color: AGENT_META[activeAgent]?.color }}>{AGENT_META[activeAgent]?.label || activeAgent}</span>
          <span>is working…</span>
        </div>
      )}

      <div className="chat-stream" ref={streamRef}>
        <div className="agent-chip" style={{ alignSelf: "center", color: "var(--ink-4)", fontSize: 10.5, letterSpacing: "0.06em" }}>
          <I.lock size={10}/> ON-DEVICE · NOTHING LEAVES THIS MACHINE
        </div>

        {thread.length === 0 && online && (
          <div style={{
            padding: "32px 16px",
            textAlign: "center",
            color: "var(--ink-4)",
            fontSize: 13,
            lineHeight: 1.6,
          }}>
            Ask Meridian anything about your money. Upload a statement first for personalized advice.
          </div>
        )}

        {thread.map((m, i) => {
          if (m.role === "user") return (
            <div key={i} className="msg-user fade-in">{m.text ?? m.content}</div>
          );
          if ((m.role === "supervisor" && m.routing) || (m.role === "system" && m.routing)) return (
            <div key={i} className="fade-in"><RoutingPill agents={m.routing}/></div>
          );
          // agent or supervisor synthesis or assistant
          const agent = m.agent ?? (m.role === "supervisor" ? "supervisor" : m.role === "assistant" ? null : m.role);
          return <MessageWithTrace key={i} m={m} agent={agent} prominentAgents={prominentAgents} send={send}/>;
        })}
      </div>

      <div className="chat-input-wrap">
        <div className="chat-suggestions">
          {suggestions.map((s) => (
            <button key={s} className="suggestion" onClick={() => send(s)} disabled={inputDisabled}>{s}</button>
          ))}
        </div>
        <div className="chat-input">
          <textarea
            placeholder={online ? "Ask anything about your money…" : "Backend offline — start the server to chat"}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            rows={1}
            disabled={inputDisabled}
          />
          <button className="send-btn" onClick={() => send()} title="Send" disabled={inputDisabled}>
            {isStreaming
              ? <span className="spinner" style={{ width: 12, height: 12, borderColor: "currentColor", borderTopColor: "transparent" }}/>
              : <I.send size={14} stroke="currentColor"/>
            }
          </button>
        </div>
        <div style={{ fontSize: 10.5, color: "var(--ink-4)", marginTop: 6, display: "flex", alignItems: "center", gap: 4 }}>
          <I.shield size={10}/> Account numbers redacted before retrieval · No PII leaves your vault
        </div>
      </div>
    </aside>
  );
}

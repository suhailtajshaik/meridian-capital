import React from 'react';
import { I } from './icons.jsx';
import { Sidebar } from './sidebar.jsx';
import { ChatPanel } from './chat.jsx';
import { Dashboard } from './dashboard.jsx';
import { Documents } from './documents.jsx';
import { DebtView, SavingsView, BudgetView, PayoffView, SettingsView } from './views.jsx';
import { useTweaks, TweaksPanel, TweakSection, TweakToggle, TweakRadio, TweakSelect, TweakColor } from './tweaks-panel.jsx';
import { useBackendStatus } from './hooks/useBackendStatus.js';
import { useFinancialData } from './hooks/useFinancialData.js';

/* Main app shell — routes views, manages chat panel + tweaks */

/* ─── Welcome modal — shown on first visit to collect user's name ─────────── */
function WelcomeModal({ onComplete }) {
  const [name, setName] = React.useState("");
  const handleSubmit = () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    onComplete(trimmed);
  };
  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 1000,
      background: "rgba(0,0,0,0.35)",
      backdropFilter: "blur(2px)",
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <div style={{
        background: "var(--surface)",
        borderRadius: 14,
        padding: "40px 40px 32px",
        width: 380,
        maxWidth: "calc(100vw - 40px)",
        boxShadow: "0 8px 40px rgba(0,0,0,0.18)",
        display: "flex", flexDirection: "column", alignItems: "center",
        textAlign: "center",
      }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8, color: "var(--ink)" }}>Welcome!</h2>
        <p style={{ fontSize: 15, color: "var(--ink-2)", marginBottom: 24 }}>What's your first name?</p>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
          placeholder="Enter your name"
          autoFocus
          style={{
            width: "100%", padding: "12px 14px", fontSize: 15,
            border: "1.5px solid var(--line)", borderRadius: 8,
            background: "var(--surface)", color: "var(--ink)",
            outline: "none", marginBottom: 14, boxSizing: "border-box",
          }}
        />
        <button
          className="btn primary"
          onClick={handleSubmit}
          disabled={!name.trim()}
          style={{ width: "100%", padding: "12px", fontSize: 15, borderRadius: 8, marginBottom: 16 }}
        >
          Continue
        </button>
        <p style={{ fontSize: 12.5, color: "var(--ink-4)", margin: 0 }}>You can change this later in Settings.</p>
      </div>
    </div>
  );
}

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "light",
  "density": "balanced",
  "agentVisibility": "subtle",
  "accent": "navy",
  "chatOpen": true
}/*EDITMODE-END*/;

const ACCENT_MAP = {
  navy: { ink: "#0E2238", positive: "#1E6B52" },
  forest: { ink: "#13422F", positive: "#2A6F4D" },
  graphite: { ink: "#1A1A1A", positive: "#2A6F4D" },
  oxblood: { ink: "#3B1A1A", positive: "#1E6B52" },
};

/* ─── Backend-offline banner — rendered at the top of the app ─────────────── */
function BackendOfflineBanner() {
  return (
    <div style={{
      position: "fixed",
      top: 0, left: 0, right: 0,
      zIndex: 9999,
      background: "var(--negative)",
      color: "var(--surface)",
      padding: "10px 20px",
      display: "flex",
      alignItems: "center",
      gap: 10,
      fontSize: 13,
      fontWeight: 500,
      boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
    }}>
      <I.alert size={14} style={{ flexShrink: 0 }}/>
      <span>
        Backend unreachable at <code style={{ fontFamily: "var(--font-mono)", fontSize: 12, background: "rgba(255,255,255,0.15)", padding: "1px 5px", borderRadius: 4 }}>http://localhost:8000</code>.
        Run <code style={{ fontFamily: "var(--font-mono)", fontSize: 12, background: "rgba(255,255,255,0.15)", padding: "1px 5px", borderRadius: 4 }}>docker compose up</code> from the repo root.
      </span>
    </div>
  );
}

export default function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [view, setView] = React.useState("documents");
  const { online, model } = useBackendStatus();
  const financialData = useFinancialData();

  const [userName, setUserName] = React.useState(() => localStorage.getItem("meridian.user_name") || "");
  const [showWelcome, setShowWelcome] = React.useState(() => !localStorage.getItem("meridian.user_name"));

  const handleUserNameChange = (name) => {
    localStorage.setItem("meridian.user_name", name);
    setUserName(name);
  };

  const handleWelcomeComplete = (name) => {
    handleUserNameChange(name);
    setShowWelcome(false);
  };

  const handleClearAll = async () => {
    await financialData.clearAll();
    localStorage.removeItem("meridian.user_name");
    setUserName("");
    setShowWelcome(true);
  };

  React.useEffect(() => {
    document.documentElement.setAttribute("data-theme", t.theme);
    document.documentElement.setAttribute("data-density", t.density);
    const a = ACCENT_MAP[t.accent] || ACCENT_MAP.navy;
    document.documentElement.style.setProperty("--ink", a.ink);
    document.documentElement.style.setProperty("--positive", a.positive);
  }, [t.theme, t.density, t.accent]);

  // Auto-collapse chat on narrow viewports the first time we see them
  React.useEffect(() => {
    const onResize = () => {
      if (window.innerWidth < 1180 && t.chatOpen) {
        // overlay mode is fine; keep open. just ensure not blocking content
      }
    };
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const ADVISOR_SCOPE_MAP = { debt: "debt", savings: "savings", budget: "budget", payoff: "payoff" };
  const advisorScope = ADVISOR_SCOPE_MAP[view] ?? null;

  const titleFor = {
    dashboard: { crumb: "Home", title: "Dashboard" },
    documents: { crumb: "Home", title: "My Files" },
    chat: { crumb: "Home", title: "Ask Meridian" },
    debt: { crumb: "Advisors", title: "Debt Coach" },
    savings: { crumb: "Advisors", title: "Savings Guide" },
    budget: { crumb: "Advisors", title: "Budget Helper" },
    payoff: { crumb: "Advisors", title: "Payoff Planner" },
    settings: { crumb: "Settings", title: "Settings" },
  }[view];

  const renderView = () => {
    const props = {
      snapshot: financialData.snapshot,
      loading: financialData.loading,
      clearAll: handleClearAll,
      uploadFile: financialData.uploadFile,
      uploading: financialData.uploading,
      uploadError: financialData.uploadError,
      snapshotStatus: financialData.snapshotStatus,
      startPolling: financialData.startPolling,
      onSnapshotReceived: financialData.onSnapshotReceived,
      refresh: financialData.refresh,
      openChat: () => setTweak("chatOpen", true),
      onNav: setView,
      online,
      userName,
      onUserNameChange: handleUserNameChange,
    };
    switch (view) {
      case "dashboard": return <Dashboard {...props}/>;
      case "documents": return <Documents {...props}/>;
      case "debt": return <DebtView {...props}/>;
      case "savings": return <SavingsView {...props}/>;
      case "budget": return <BudgetView {...props}/>;
      case "payoff": return <PayoffView {...props}/>;
      case "settings": return <SettingsView {...props}/>;
      case "chat":
        // chat view = make sure panel is open + show dashboard underneath
        if (!t.chatOpen) setTweak("chatOpen", true);
        return <Dashboard {...props}/>;
      default: return <Dashboard {...props}/>;
    }
  };

  return (
    <div className="app" data-chat={t.chatOpen ? "open" : "closed"}>
      {!online && <BackendOfflineBanner/>}

      <Sidebar active={view} onNav={setView} userName={userName}/>
      {showWelcome && <WelcomeModal onComplete={handleWelcomeComplete}/>}

      <main className="main" style={!online ? { paddingTop: 44 } : undefined}>
        <header className="topbar">
          <span className="topbar-title">
            <span className="muted">{titleFor.crumb}</span>
            <span className="muted" style={{ margin: "0 8px" }}>/</span>
            <strong>{titleFor.title}</strong>
          </span>
          <div className="topbar-spacer"/>
          {userName && (
            <span style={{ fontSize: 13, color: "var(--ink-2)", marginRight: 8, whiteSpace: "nowrap" }}>
              Welcome, <strong style={{ color: "var(--ink)" }}>{userName}</strong>!
            </span>
          )}
          <span className="topbar-pill">
            <span className="dot"/> Private & Secure
          </span>
          <button className="icon-btn" title="Search"><I.search size={14}/></button>
          <button className="icon-btn" title="Notifications"><I.bell size={14}/></button>
          <button className="icon-btn" onClick={() => setTweak("chatOpen", !t.chatOpen)} title="Toggle advisor"
                  style={{ background: t.chatOpen ? "var(--bg)" : "var(--surface)" }}>
            <I.panel size={14}/>
          </button>
        </header>
        {financialData.snapshotStatus === "computing" && (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "0 20px",
            height: 32,
            background: "var(--surface-2)",
            borderLeft: "3px solid var(--info)",
            borderBottom: "1px solid var(--line)",
            fontSize: 12.5,
            color: "var(--ink-2)",
            flexShrink: 0,
          }}>
            <span className="spinner" style={{ width: 11, height: 11, borderColor: "var(--info)", borderTopColor: "transparent", flexShrink: 0 }}/>
            Advisors are analyzing your data… this typically takes 30–60 seconds.
          </div>
        )}
        {renderView()}
      </main>

      <ChatPanel
        open={t.chatOpen}
        onClose={() => setTweak("chatOpen", false)}
        prominentAgents={t.agentVisibility === "prominent"}
        online={online}
        model={model}
        advisorScope={advisorScope}
      />

      <Tweaks t={t} setTweak={setTweak}/>
    </div>
  );
}

const ACCENT_OPTS = [
  { value: "navy", color: "#0E2238" },
  { value: "forest", color: "#13422F" },
  { value: "graphite", color: "#1A1A1A" },
  { value: "oxblood", color: "#3B1A1A" },
];

function Tweaks({ t, setTweak }) {
  // Find the hex matching the current accent name (TweakColor stores by hex)
  const accentHex = (ACCENT_OPTS.find(a => a.value === t.accent) || ACCENT_OPTS[0]).color;
  return (
    <TweaksPanel>
      <TweakSection label="Theme"/>
      <TweakRadio label="Mode" value={t.theme}
        options={["light", "dark"]}
        onChange={(v) => setTweak("theme", v)}/>
      <TweakColor label="Accent" value={accentHex}
        options={ACCENT_OPTS.map(a => a.color)}
        onChange={(hex) => {
          const found = ACCENT_OPTS.find(a => a.color === hex) || ACCENT_OPTS[0];
          setTweak("accent", found.value);
        }}/>

      <TweakSection label="Layout"/>
      <TweakSelect label="Density" value={t.density}
        options={["compact", "balanced", "spacious"]}
        onChange={(v) => setTweak("density", v)}/>
      <TweakToggle label="Advisor panel" value={t.chatOpen}
        onChange={(v) => setTweak("chatOpen", v)}/>

      <TweakSection label="Multi-agent UX"/>
      <TweakSelect label="Agent attribution" value={t.agentVisibility}
        options={[
          { value: "hidden", label: "Hidden (one assistant)" },
          { value: "subtle", label: "Subtle (chips)" },
          { value: "prominent", label: "Prominent (badges)" },
        ]}
        onChange={(v) => setTweak("agentVisibility", v)}/>
    </TweaksPanel>
  );
}

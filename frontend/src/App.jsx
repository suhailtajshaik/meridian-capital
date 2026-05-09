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

  const titleFor = {
    dashboard: { crumb: "Overview", title: "Dashboard" },
    documents: { crumb: "Ingestion", title: "Documents" },
    chat: { crumb: "Overview", title: "Advisor chat" },
    debt: { crumb: "Advisors", title: "Debt analyzer" },
    savings: { crumb: "Advisors", title: "Savings strategy" },
    budget: { crumb: "Advisors", title: "Budget advisor" },
    payoff: { crumb: "Advisors", title: "Payoff optimizer" },
    settings: { crumb: "System", title: "Settings & security" },
  }[view];

  const renderView = () => {
    const props = {
      snapshot: financialData.snapshot,
      loading: financialData.loading,
      clearAll: financialData.clearAll,
      uploadFile: financialData.uploadFile,
      uploading: financialData.uploading,
      uploadError: financialData.uploadError,
      refresh: financialData.refresh,
      openChat: () => setTweak("chatOpen", true),
      onNav: setView,
      online,
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

      <Sidebar active={view} onNav={setView}/>

      <main className="main" style={!online ? { paddingTop: 44 } : undefined}>
        <header className="topbar">
          <span className="topbar-title">
            <span className="muted">{titleFor.crumb}</span>
            <span className="muted" style={{ margin: "0 8px" }}>/</span>
            <strong>{titleFor.title}</strong>
          </span>
          <div className="topbar-spacer"/>
          <span className="topbar-pill">
            <span className="dot"/> Local vault
          </span>
          <button className="icon-btn" title="Search"><I.search size={14}/></button>
          <button className="icon-btn" title="Notifications"><I.bell size={14}/></button>
          <button className="icon-btn" onClick={() => setTweak("chatOpen", !t.chatOpen)} title="Toggle advisor"
                  style={{ background: t.chatOpen ? "var(--bg)" : "var(--surface)" }}>
            <I.panel size={14}/>
          </button>
        </header>
        {renderView()}
      </main>

      <ChatPanel
        open={t.chatOpen}
        onClose={() => setTweak("chatOpen", false)}
        prominentAgents={t.agentVisibility === "prominent"}
        online={online}
        model={model}
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

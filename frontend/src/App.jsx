import React from 'react';
import { I } from './icons.jsx';
import { PERSONAS } from './data.js';
import { Sidebar } from './sidebar.jsx';
import { ChatPanel } from './chat.jsx';
import { Dashboard } from './dashboard.jsx';
import { Documents } from './documents.jsx';
import { DebtView, SavingsView, BudgetView, PayoffView, SettingsView } from './views.jsx';
import { useTweaks, TweaksPanel, TweakSection, TweakToggle, TweakRadio, TweakSelect, TweakColor } from './tweaks-panel.jsx';

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

export default function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [view, setView] = React.useState("documents");
  const persona = PERSONAS.midcareer;

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
    const props = { persona, openChat: () => setTweak("chatOpen", true), onNav: setView };
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
      <Sidebar active={view} onNav={setView} persona={persona}/>

      <main className="main">
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


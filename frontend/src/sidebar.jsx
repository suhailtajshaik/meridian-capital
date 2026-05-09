import React from 'react';
import { I } from './icons.jsx';

/* Sidebar navigation */

export function Sidebar({ active, onNav, persona }) {
  const items = [
    { id: "dashboard", label: "Dashboard", icon: I.dashboard },
    { id: "documents", label: "Documents", icon: I.doc, badge: "6" },
    { id: "chat", label: "Advisor chat", icon: I.chat },
  ];
  const advisors = [
    { id: "debt", label: "Debt Analyzer", icon: I.debt, dot: "var(--agent-debt)" },
    { id: "savings", label: "Savings Strategy", icon: I.savings, dot: "var(--agent-savings)" },
    { id: "budget", label: "Budget Advisor", icon: I.budget, dot: "var(--agent-budget)" },
    { id: "payoff", label: "Payoff Optimizer", icon: I.payoff, dot: "var(--agent-payoff)" },
  ];
  const system = [
    { id: "settings", label: "Settings & security", icon: I.shield },
  ];
  const renderItem = (it) => (
    <button key={it.id} className={`nav-item ${active === it.id ? "active" : ""}`} onClick={() => onNav(it.id)}>
      {it.dot ? (
        <span className="nav-icon" style={{ display: "grid", placeItems: "center" }}>
          <span style={{ width: 7, height: 7, borderRadius: 999, background: it.dot }}/>
        </span>
      ) : <it.icon className="nav-icon"/>}
      <span>{it.label}</span>
      {it.badge && <span className="nav-badge">{it.badge}</span>}
    </button>
  );
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">m</div>
        <div>
          <div className="brand-name">Meridian</div>
          <div className="brand-sub">Personal finance · v0.4</div>
        </div>
      </div>

      <div className="nav-section-label">Overview</div>
      {items.map(renderItem)}

      <div className="nav-section-label">Advisors</div>
      {advisors.map(renderItem)}

      <div className="nav-section-label">System</div>
      {system.map(renderItem)}

      <div className="user-card">
        <div className="avatar">{persona.initials}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="user-name">{persona.name}</div>
          <div className="user-meta">
            <I.lock size={10}/> Local vault · on-device
          </div>
        </div>
      </div>
    </aside>
  );
}


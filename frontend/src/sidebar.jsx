import React from 'react';
import { I } from './icons.jsx';

/* Sidebar navigation */

export function Sidebar({ active, onNav, userName }) {
  const items = [
    { id: "dashboard", label: "Home", icon: I.dashboard },
    { id: "documents", label: "My Files", icon: I.doc },
    { id: "chat", label: "Ask Meridian", icon: I.chat },
  ];
  const advisors = [
    { id: "debt", label: "Debt Coach", icon: I.debt, dot: "var(--agent-debt)" },
    { id: "savings", label: "Savings Guide", icon: I.savings, dot: "var(--agent-savings)" },
    { id: "budget", label: "Budget Helper", icon: I.budget, dot: "var(--agent-budget)" },
    { id: "payoff", label: "Payoff Planner", icon: I.payoff, dot: "var(--agent-payoff)" },
  ];
  const system = [
    { id: "settings", label: "Settings", icon: I.shield },
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

  const displayName = userName || "Guest";
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">m</div>
        <div>
          <div className="brand-name">Meridian</div>
          <div className="brand-sub">Your Money, Made Simple</div>
        </div>
      </div>

      {items.map(renderItem)}

      <div style={{ height: 8 }}/>
      {advisors.map(renderItem)}

      <div style={{ height: 8 }}/>
      {system.map(renderItem)}

      <div className="user-card">
        <div className="avatar">{initial}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="user-name">{displayName}</div>
          <div className="user-meta">
            <I.lock size={10}/> Private & Secure
          </div>
        </div>
      </div>
    </aside>
  );
}

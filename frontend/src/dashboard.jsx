import React from 'react';
import { I } from './icons.jsx';
import { AGENT_META } from './data.js';
import { Sparkline, Donut, LineArea } from './charts.jsx';

/* Dashboard view — hero stats, net worth chart, agent insights, transactions */

export function StatCard({ label, value, cents, delta, deltaLabel, sparkData, sparkColor, accent, icon: Ico }) {
  const positive = (delta ?? 0) >= 0;
  return (
    <div className="stat">
      <div className="stat-label">
        {Ico && <Ico size={12}/>}
        {label}
      </div>
      <div className="stat-value">
        ${Math.abs(value).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
        {cents != null && <span className="cents">.{cents}</span>}
      </div>
      {delta != null && (
        <div className={`stat-delta ${positive ? "pos" : "neg"}`}>
          {positive ? <I.trend_up size={12}/> : <I.trend_dn size={12}/>}
          {positive ? "+" : "−"}${Math.abs(delta).toLocaleString()}
          <span className="muted" style={{ marginLeft: 4 }}>{deltaLabel}</span>
        </div>
      )}
      {sparkData && (
        <div className="stat-spark">
          <Sparkline data={sparkData} width={120} height={28} color={sparkColor || accent || "var(--ink-3)"} fill={true}/>
        </div>
      )}
    </div>
  );
}

export function AgentInsightCard({ agent, headline, body, metric, metricSub, action }) {
  const meta = AGENT_META[agent];
  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span className="agent-dot" style={{ background: meta.color, width: 8, height: 8 }}/>
        <span style={{ fontSize: 11, color: "var(--ink-3)", letterSpacing: "0.06em", textTransform: "uppercase", fontWeight: 500 }}>
          {meta.label}
        </span>
        <span style={{ marginLeft: "auto", fontSize: 10.5, color: "var(--ink-4)" }}>just now</span>
      </div>
      <div style={{ fontSize: 15, fontWeight: 500, lineHeight: 1.35, color: "var(--ink)" }}>{headline}</div>
      <div style={{ fontSize: 12.5, color: "var(--ink-3)", lineHeight: 1.5 }}>{body}</div>
      {metric != null && (
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, paddingTop: 4 }}>
          <span className="num" style={{ fontSize: 22, color: meta.color }}>{metric}</span>
          <span style={{ fontSize: 11, color: "var(--ink-3)" }}>{metricSub}</span>
        </div>
      )}
      <button className="btn ghost" style={{ alignSelf: "flex-start", padding: "4px 0", fontSize: 12, color: "var(--ink-2)" }}>
        {action} <I.arrow_up size={12} style={{ transform: "rotate(45deg)" }}/>
      </button>
    </div>
  );
}

export function GoalRow({ g }) {
  const pct = (g.balance / g.target) * 100;
  return (
    <div style={{ padding: "12px 0", borderBottom: "1px solid var(--line)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
        <div>
          <div style={{ fontSize: 13.5, fontWeight: 500 }}>{g.name}</div>
          <div style={{ fontSize: 11, color: "var(--ink-3)" }}>{g.category} · ETA {g.eta}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="num tnum" style={{ fontSize: 15 }}>${g.balance.toLocaleString()}</div>
          <div style={{ fontSize: 11, color: "var(--ink-3)" }}>of ${g.target.toLocaleString()}</div>
        </div>
      </div>
      <div className="bar-track">
        <div className="bar-fill pos" style={{ width: `${Math.min(100, pct)}%` }}/>
      </div>
    </div>
  );
}

export function Dashboard({ persona, openChat }) {
  const months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May"];
  const totalDebt = persona.debts.reduce((s, d) => s + d.balance, 0);
  const totalSavings = persona.savings.reduce((s, d) => s + d.balance, 0);
  const totalSpent = persona.budget.reduce((s, d) => s + d.spent, 0);
  const totalBudget = persona.budget.reduce((s, d) => s + d.budget, 0);

  const debtSpark = [355000, 354000, 352000, 351200, 350800, 351400, 351900, 351500, 350500, 350800, 350400, totalDebt];
  const savingsSpark = [16000, 16800, 17400, 18200, 19000, 19500, 20100, 20800, 21100, 21600, 21900, totalSavings];

  return (
    <div className="scroll" data-screen-label="01 Dashboard">
      {/* Greeting row */}
      <div className="hero-row" style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 18, gap: 16 }}>
        <div>
          <div className="eyebrow" style={{ marginBottom: 6 }}>Friday · May 9</div>
          <h1 className="h1" style={{ fontFamily: "var(--font-num)", fontWeight: 400, fontSize: 30, letterSpacing: "-0.02em" }}>
            Good morning, <em style={{ fontStyle: "italic", color: "var(--ink-2)" }}>{persona.name.split(" ")[0]}</em>.
          </h1>
          <div className="muted" style={{ fontSize: 13.5, marginTop: 4 }}>
            Your finances are <span style={{ color: "var(--positive)", fontWeight: 500 }}>on track</span> — net worth up $4.3k since last month.
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn" onClick={openChat}><I.chat size={13}/> Ask advisor</button>
          <button className="btn primary"><I.upload size={13}/> Add document</button>
        </div>
      </div>

      {/* Hero stats */}
      <div className="grid-4">
        <StatCard label="Net worth" value={persona.netWorth} cents="40"
          delta={persona.netWorthDelta} deltaLabel="this month"
          sparkData={persona.netWorthSeries} sparkColor="var(--ink)"
          icon={I.trend_up}/>
        <StatCard label="Total debt" value={totalDebt}
          delta={-1240} deltaLabel="this month"
          sparkData={debtSpark} sparkColor="var(--negative)"
          icon={I.debt}/>
        <StatCard label="Total savings" value={totalSavings}
          delta={1933} deltaLabel="this month"
          sparkData={savingsSpark} sparkColor="var(--positive)"
          icon={I.savings}/>
        <StatCard label="Cash flow" value={persona.cashFlow}
          delta={persona.cashFlowDelta} deltaLabel="vs last month"
          sparkData={[3100, 2800, 3200, 2900, 2750, 2400, 2840]} sparkColor="var(--ink-2)"
          icon={I.spark}/>
      </div>

      {/* Net worth chart + budget snapshot */}
      <div className="split-main" style={{ marginTop: 16 }}>
        <div className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Net worth · 12 months</div>
              <div className="num" style={{ fontSize: 26, marginTop: 2 }}>${persona.netWorth.toLocaleString()}</div>
            </div>
            <div style={{ display: "flex", gap: 4 }}>
              {["1M", "3M", "6M", "1Y", "All"].map((p) => (
                <button key={p} className="btn ghost" style={{
                  padding: "3px 8px", fontSize: 11.5,
                  background: p === "1Y" ? "var(--bg)" : "transparent",
                  boxShadow: p === "1Y" ? "inset 0 0 0 1px var(--line)" : "none",
                }}>{p}</button>
              ))}
            </div>
          </div>
          <LineArea data={persona.netWorthSeries} labels={months} accent="var(--ink)" height={240}/>
        </div>

        <div className="card">
          <div className="card-head">
            <div>
              <div className="card-title">May spending</div>
              <div className="num" style={{ fontSize: 26, marginTop: 2 }}>
                ${totalSpent.toLocaleString()}
                <span style={{ fontSize: 14, color: "var(--ink-3)", fontFamily: "var(--font-ui)", marginLeft: 4 }}>
                  / ${totalBudget.toLocaleString()}
                </span>
              </div>
            </div>
            <span className={`tag ${totalSpent > totalBudget ? "warn" : "pos"}`}>
              {totalSpent > totalBudget
                ? `${Math.round(((totalSpent - totalBudget) / totalBudget) * 100)}% over`
                : `${Math.round(((totalBudget - totalSpent) / totalBudget) * 100)}% under`}
            </span>
          </div>
          <Donut
            slices={persona.budget.slice(0, 6).map((b) => ({
              label: b.cat, value: b.spent,
              color: ["#0E2238", "#2C4F7C", "#1E6B52", "#B27A1E", "#9E3A37", "#5C6B82"][persona.budget.indexOf(b) % 6],
            }))}
            size={140}
            thickness={20}
            centerLabel={`${Math.round((totalSpent / totalBudget) * 100)}%`}
            centerSub="OF BUDGET"
          />
        </div>
      </div>

      {/* Agent insights */}
      <div style={{ marginTop: 24 }}>
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 12 }}>
          <div>
            <h2 className="h2">What your advisors noticed</h2>
            <div className="muted" style={{ fontSize: 12.5 }}>Updated automatically as new transactions are ingested</div>
          </div>
          <button className="btn ghost" style={{ fontSize: 12 }}><I.refresh size={12}/> Re-analyze</button>
        </div>
        <div className="grid-4">
          <AgentInsightCard
            agent="debt"
            headline="Two cards above 19% APR"
            body="Sapphire & Quicksilver are accruing $122/mo in interest combined. Together they're 1.9% of your debt but 18% of your interest cost."
            metric="$122/mo"
            metricSub="interest leak"
            action="See debt analysis"
          />
          <AgentInsightCard
            agent="payoff"
            headline="Avalanche saves $612"
            body="Switch from snowball to avalanche on your two cards — same monthly outlay, debt-free 3 months sooner."
            metric="−3 mo"
            metricSub="time to debt-free"
            action="Compare strategies"
          />
          <AgentInsightCard
            agent="savings"
            headline="Emergency fund at 51%"
            body="You're $8.8k away from a 6-month buffer. Auto-saving $400/mo gets you there by Mar 2028."
            metric="51%"
            metricSub="of 6-month target"
            action="Adjust goal"
          />
          <AgentInsightCard
            agent="budget"
            headline="Dining $136 over budget"
            body="Your dining spend is on track to exceed budget by $190 if the trend holds. 8 transactions on weekends."
            metric="+39%"
            metricSub="vs your budget"
            action="See breakdown"
          />
        </div>
      </div>

      {/* Activity + Goals */}
      <div className="split-main" style={{ marginTop: 24 }}>
        <div className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Recent activity</div>
              <div className="card-sub">Across 4 connected accounts</div>
            </div>
            <button className="btn ghost" style={{ fontSize: 12 }}>View all</button>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: 70 }}>Date</th>
                <th>Merchant</th>
                <th>Category</th>
                <th>Source</th>
                <th style={{ textAlign: "right" }}>Amount</th>
              </tr>
            </thead>
            <tbody>
              {persona.transactions.map((t, i) => (
                <tr key={i}>
                  <td className="muted" style={{ fontSize: 12 }}>{t.date}</td>
                  <td>{t.merchant}</td>
                  <td><span className="tag">{t.cat}</span></td>
                  <td className="muted" style={{ fontSize: 12 }}>{t.source}</td>
                  <td className="num tnum" style={{ textAlign: "right", color: t.amount < 0 ? "var(--ink)" : "var(--positive)" }}>
                    {t.amount > 0 ? "+" : "−"}${Math.abs(t.amount).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Savings goals</div>
              <div className="card-sub">${totalSavings.toLocaleString()} across {persona.savings.length} goals</div>
            </div>
            <button className="icon-btn"><I.plus size={14}/></button>
          </div>
          <div>
            {persona.savings.map((g, i) => <GoalRow key={i} g={g}/>)}
          </div>
        </div>
      </div>
    </div>
  );
}


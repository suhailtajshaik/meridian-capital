import React from 'react';
import { I } from './icons.jsx';
import { AGENT_META } from './data.js';
import { Donut, HBar, LineArea, StackedTimeline } from './charts.jsx';
import { StatCard } from './dashboard.jsx';

/* Agent views — Debt, Savings, Budget, Payoff, Settings */

export function ViewHeader({ agent, title, sub, action }) {
  const meta = agent ? AGENT_META[agent] : null;
  return (
    <div style={{ marginBottom: 18, display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16 }}>
      <div>
        {meta && (
          <div className="eyebrow" style={{ marginBottom: 6, display: "flex", alignItems: "center", gap: 6 }}>
            <span className="agent-dot" style={{ background: meta.color }}/>
            {meta.label}
          </div>
        )}
        <h1 className="h1">{title}</h1>
        {sub && <div className="muted" style={{ fontSize: 13.5, marginTop: 4, maxWidth: 720 }}>{sub}</div>}
      </div>
      {action}
    </div>
  );
}

export function RiskBadge({ risk }) {
  const map = {
    low: { cls: "pos", label: "Low risk" },
    medium: { cls: "warn", label: "Watch" },
    high: { cls: "neg", label: "High rate" },
  };
  const m = map[risk] || map.medium;
  return <span className={`tag ${m.cls}`}>{m.label}</span>;
}

/* ---------------- Debt Analyzer ---------------- */
export function DebtView({ persona }) {
  const total = persona.debts.reduce((s, d) => s + d.balance, 0);
  const minPay = persona.debts.reduce((s, d) => s + d.min, 0);
  const yearlyInterest = persona.debts.reduce((s, d) => s + d.balance * (d.rate / 100), 0);
  const wAvgRate = persona.debts.reduce((s, d) => s + d.rate * d.balance, 0) / total;

  // Build a synthetic 12-month projection (current + 11 prior) per debt
  const months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May"];
  const series = persona.debts.map((d, i) => ({
    label: d.name,
    values: months.map((_, m) => Math.round(d.balance * (1 + (11 - m) * 0.005 - i * 0.001))),
  }));
  const palette = ["#0E2238", "#9E3A37", "#B27A1E", "#2C4F7C", "#1E6B52"];

  return (
    <div className="scroll" data-screen-label="03 Debt">
      <ViewHeader agent="debt" title="Debt analyzer"
        sub="Rates, balances, and risk across every liability. The agent flags compounding traps and recommends payoff order."/>

      <div className="grid-4">
        <StatCard label="Total balance" value={total} icon={I.debt}/>
        <StatCard label="Weighted avg rate" value={Number(wAvgRate.toFixed(2))} icon={I.spark}/>
        <StatCard label="Annual interest" value={Math.round(yearlyInterest)} icon={I.alert}/>
        <StatCard label="Min payments" value={minPay} icon={I.refresh}/>
      </div>

      <div className="split-main" style={{ marginTop: 16 }}>
        <div className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Balance trajectory · 12 months</div>
              <div className="card-sub">Stacked by liability</div>
            </div>
            <div style={{ display: "flex", gap: 10, fontSize: 11, flexWrap: "wrap" }}>
              {series.map((s, i) => (
                <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 5, color: "var(--ink-3)" }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: palette[i % palette.length] }}/> {s.label.split(" — ")[0]}
                </span>
              ))}
            </div>
          </div>
          <StackedTimeline months={months} series={series} palette={palette} height={220}/>
        </div>

        <div className="card">
          <div className="card-head">
            <div className="card-title">Interest cost mix</div>
            <span className="card-sub">Yearly</span>
          </div>
          <Donut
            slices={persona.debts.map((d, i) => ({
              label: d.name.split(" — ")[0],
              value: Math.round(d.balance * (d.rate / 100)),
              color: palette[i % palette.length],
            }))}
            size={140} thickness={20}
            centerLabel={`$${Math.round(yearlyInterest / 1000)}k`}
            centerSub="PER YEAR"
          />
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-head">
          <div className="card-title">All debts</div>
          <div className="card-sub">Sorted by APR (avalanche order)</div>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Liability</th>
              <th>Lender</th>
              <th>Type</th>
              <th style={{ textAlign: "right" }}>Balance</th>
              <th style={{ textAlign: "right" }}>APR</th>
              <th style={{ textAlign: "right" }}>Min</th>
              <th>Risk</th>
            </tr>
          </thead>
          <tbody>
            {[...persona.debts].sort((a, b) => b.rate - a.rate).map((d, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 500 }}>{d.name}</td>
                <td className="muted">{d.lender}</td>
                <td><span className="tag">{d.type}</span></td>
                <td className="num tnum" style={{ textAlign: "right" }}>${d.balance.toLocaleString()}</td>
                <td className="num tnum" style={{ textAlign: "right", color: d.rate >= 18 ? "var(--negative)" : "var(--ink)" }}>
                  {d.rate.toFixed(2)}%
                </td>
                <td className="num tnum" style={{ textAlign: "right" }}>${d.min}</td>
                <td><RiskBadge risk={d.risk}/></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ---------------- Savings ---------------- */
export function SavingsView({ persona }) {
  const total = persona.savings.reduce((s, d) => s + d.balance, 0);
  const targetTotal = persona.savings.reduce((s, d) => s + d.target, 0);
  const monthlyContrib = persona.savings.reduce((s, d) => s + d.monthly, 0);
  const months = ["Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May"];
  const trend = months.map((_, i) => Math.round(total * (0.7 + i * 0.027)));

  return (
    <div className="scroll" data-screen-label="04 Savings">
      <ViewHeader agent="savings" title="Savings strategy"
        sub="Goals, timelines, and contribution recommendations. The agent simulates your savings rate against income and surplus to project realistic ETAs."/>

      <div className="grid-3">
        <StatCard label="Total saved" value={total} icon={I.savings}/>
        <StatCard label="Across goals" value={targetTotal} icon={I.spark}/>
        <StatCard label="Auto-contribute / mo" value={monthlyContrib} icon={I.refresh}/>
      </div>

      <div className="split-main" style={{ marginTop: 16 }}>
        <div className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Savings growth · 12 months</div>
              <div className="num" style={{ fontSize: 24, marginTop: 2 }}>${total.toLocaleString()}</div>
            </div>
            <span className="tag pos"><I.trend_up size={10}/> +43% YoY</span>
          </div>
          <LineArea data={trend} labels={months} accent="var(--positive)" height={220}/>
        </div>

        <div className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Surplus allocation</div>
              <div className="card-sub">Where each $100 of surplus goes</div>
            </div>
          </div>
          <HBar
            valueFmt={(v) => `${v}%`}
            max={100}
            rows={[
              { label: "Emergency fund", value: 35, color: "var(--positive)" },
              { label: "Roth IRA", value: 30, color: "var(--info)" },
              { label: "Kitchen reno", value: 20, color: "var(--ink-2)" },
              { label: "Vacation — Japan", value: 10, color: "var(--warn)" },
              { label: "Buffer", value: 5, color: "var(--ink-3)" },
            ]}
          />
          <div className="divider"/>
          <div style={{ fontSize: 12.5, color: "var(--ink-3)", lineHeight: 1.55 }}>
            Recommended: shift <strong style={{ color: "var(--ink)" }}>+10%</strong> into emergency fund until 6-month target is reached, then rebalance.
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-head">
          <div className="card-title">Goals</div>
          <button className="btn ghost" style={{ fontSize: 12 }}><I.filter size={12}/> Sort by ETA</button>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {persona.savings.map((g, i) => {
            const pct = (g.balance / g.target) * 100;
            return (
              <div key={i} style={{ padding: 16, border: "1px solid var(--line)", borderRadius: 10, background: "var(--surface-2)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontSize: 14.5, fontWeight: 500 }}>{g.name}</div>
                    <div style={{ fontSize: 11.5, color: "var(--ink-3)", marginTop: 2 }}>{g.category} · ${g.monthly}/mo auto</div>
                  </div>
                  <span className="tag info">ETA {g.eta}</span>
                </div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginTop: 10 }}>
                  <span className="num" style={{ fontSize: 22 }}>${g.balance.toLocaleString()}</span>
                  <span className="muted" style={{ fontSize: 12 }}>of ${g.target.toLocaleString()}</span>
                  <span className="tag pos" style={{ marginLeft: "auto" }}>{Math.round(pct)}%</span>
                </div>
                <div className="bar-track" style={{ marginTop: 8 }}>
                  <div className="bar-fill pos" style={{ width: `${Math.min(100, pct)}%` }}/>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ---------------- Budget ---------------- */
export function BudgetView({ persona }) {
  const totalSpent = persona.budget.reduce((s, d) => s + d.spent, 0);
  const totalBudget = persona.budget.reduce((s, d) => s + d.budget, 0);
  const overCats = persona.budget.filter(c => c.spent > c.budget);

  const months = ["Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May"];
  const spendTrend = [6800, 7100, 6500, 6900, 7200, 7800, 8200, 7100, 6700, 6500, 6800, totalSpent];

  return (
    <div className="scroll" data-screen-label="05 Budget">
      <ViewHeader agent="budget" title="Budget advisor"
        sub="Spending categorized from transactions. The agent flags categories trending over budget and suggests reallocations."/>

      <div className="grid-4">
        <StatCard label="Spent · May" value={totalSpent} icon={I.spark}/>
        <StatCard label="Budget · May" value={totalBudget} icon={I.budget}/>
        <StatCard label="Categories over" value={overCats.length} icon={I.alert}/>
        <StatCard label="Monthly avg · 12mo" value={Math.round(spendTrend.reduce((a,b) => a+b, 0) / 12)} icon={I.refresh}/>
      </div>

      <div className="split-main" style={{ marginTop: 16 }}>
        <div className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Category breakdown · May</div>
              <div className="card-sub">Spent vs budgeted · markers show targets</div>
            </div>
          </div>
          <HBar rows={persona.budget.map(b => ({
            label: b.cat, value: b.spent, target: b.budget, color: b.color,
          }))}/>
        </div>

        <div className="card">
          <div className="card-head">
            <div className="card-title">Spending trend</div>
            <span className="tag info">Holiday peak Nov–Dec</span>
          </div>
          <LineArea data={spendTrend} labels={months} accent="var(--warn)" height={200}/>
          <div className="divider"/>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 12, color: "var(--ink-3)", letterSpacing: "0.06em", textTransform: "uppercase", fontWeight: 500 }}>
              Top leak
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 500 }}>Dining out</div>
                <div className="muted" style={{ fontSize: 12 }}>8 transactions on weekends</div>
              </div>
              <div className="num tnum" style={{ fontSize: 18, color: "var(--negative)" }}>+$136</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------------- Payoff Optimizer ---------------- */
export function PayoffView({ persona }) {
  const [strategy, setStrategy] = React.useState("avalanche");
  const cards = persona.debts.filter(d => d.type === "Credit Card" || d.type === "Auto" || d.type === "Student");
  const ordered = strategy === "avalanche"
    ? [...cards].sort((a, b) => b.rate - a.rate)
    : [...cards].sort((a, b) => a.balance - b.balance);

  // crude payoff ETA calc
  const extra = 350;
  const months = ["Jun '26","Jul","Aug","Sep","Oct","Nov","Dec","Jan '27","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan '28"];
  const series = ordered.map((d, i) => ({
    label: d.name,
    values: months.map((_, m) => {
      const decay = strategy === "avalanche" ? Math.max(0, 1 - m / (8 + i * 4)) : Math.max(0, 1 - m / (6 + i * 5));
      return Math.round(d.balance * decay);
    }),
  }));
  const palette = ["#9E3A37", "#B27A1E", "#2C4F7C", "#1E6B52", "#0E2238"];

  const compare = [
    { name: "Snowball", desc: "Smallest balance first — psychological wins", monthsToFree: 28, interest: 4180, kept: false },
    { name: "Avalanche", desc: "Highest APR first — mathematical optimum", monthsToFree: 25, interest: 3568, kept: true },
    { name: "Min only", desc: "Pay minimums — slowest, most expensive", monthsToFree: 96, interest: 18420, kept: false },
  ];

  return (
    <div className="scroll" data-screen-label="06 Payoff">
      <ViewHeader agent="payoff" title="Payoff optimizer"
        sub="Compare snowball vs avalanche on your real balances. Adjust monthly extra and watch your debt-free date move."/>

      <div className="grid-3">
        {compare.map((c) => (
          <button key={c.name}
            onClick={() => setStrategy(c.name.toLowerCase())}
            style={{
              all: "unset", cursor: "pointer",
              padding: 16,
              borderRadius: 10,
              background: strategy === c.name.toLowerCase() ? "var(--surface)" : "var(--surface-2)",
              border: `1px solid ${strategy === c.name.toLowerCase() ? "var(--ink)" : "var(--line)"}`,
              boxShadow: strategy === c.name.toLowerCase() ? "var(--shadow-2)" : "none",
              display: "flex", flexDirection: "column", gap: 8,
            }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ fontSize: 15, fontWeight: 500 }}>{c.name}</div>
              {c.kept && <span className="tag pos">Recommended</span>}
            </div>
            <div className="muted" style={{ fontSize: 12, lineHeight: 1.45 }}>{c.desc}</div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginTop: 6 }}>
              <div>
                <div className="muted" style={{ fontSize: 11 }}>Debt-free in</div>
                <div className="num" style={{ fontSize: 22 }}>{c.monthsToFree} <span style={{ fontSize: 13, color: "var(--ink-3)" }}>mo</span></div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div className="muted" style={{ fontSize: 11 }}>Total interest</div>
                <div className="num" style={{ fontSize: 18 }}>${c.interest.toLocaleString()}</div>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-head">
          <div>
            <div className="card-title">Projected balances · {strategy === "avalanche" ? "avalanche" : "snowball"}</div>
            <div className="card-sub">+${extra}/mo on top of minimums</div>
          </div>
          <div style={{ display: "flex", gap: 10, fontSize: 11, flexWrap: "wrap" }}>
            {series.map((s, i) => (
              <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 5, color: "var(--ink-3)" }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: palette[i % palette.length] }}/> {s.label.split(" — ")[0]}
              </span>
            ))}
          </div>
        </div>
        <StackedTimeline months={months} series={series} palette={palette} height={240}/>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-head">
          <div className="card-title">Payoff order</div>
          <div className="card-sub">{strategy === "avalanche" ? "By APR (descending)" : "By balance (ascending)"}</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {ordered.map((d, i) => (
            <div key={i} style={{
              display: "flex", alignItems: "center", gap: 14,
              padding: "12px 14px",
              border: "1px solid var(--line)", borderRadius: 8,
              background: i === 0 ? "var(--negative-tint)" : "var(--surface-2)",
            }}>
              <div className="num" style={{
                width: 24, height: 24, display: "grid", placeItems: "center",
                fontSize: 14,
                background: i === 0 ? "var(--negative)" : "var(--ink-3)",
                color: "var(--surface)", borderRadius: 999,
              }}>{i + 1}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13.5, fontWeight: 500 }}>{d.name}</div>
                <div className="muted" style={{ fontSize: 11.5 }}>{d.lender} · {d.rate.toFixed(2)}% APR</div>
              </div>
              <div className="num tnum" style={{ fontSize: 16 }}>${d.balance.toLocaleString()}</div>
              {i === 0 && <span className="tag neg">Pay first</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------------- Settings & Security ---------------- */
export function SettingsView({ persona }) {
  const securityChecks = [
    { label: "Local-first storage", desc: "Documents and embeddings live on this device only — no cloud sync, no remote server", status: "ok" },
    { label: "On-device embedding model", desc: "Vectors generated locally via a quantized model. Statement contents never leave your machine", status: "ok" },
    { label: "At-rest encryption", desc: "AES-256-GCM on the local vault · keys derived from your passphrase, stored only in OS keychain", status: "ok" },
    { label: "PII redaction before LLM", desc: "Account numbers, SSN, names stripped before any prompt is sent to the language model", status: "ok" },
    { label: "Read-only ingestion", desc: "No agent can move money. We only read the statements you upload", status: "ok" },
    { label: "Recovery passphrase", desc: "Generate an offline backup phrase — without it, the local vault cannot be recovered", status: "warn" },
  ];

  const docs = persona.documents;
  const [removed, setRemoved] = React.useState([]);
  const [confirmAll, setConfirmAll] = React.useState(false);
  const visible = docs.filter((d) => !removed.includes(d.name));

  return (
    <div className="scroll" data-screen-label="07 Settings">
      <ViewHeader title="Settings & security"
        sub="Everything runs locally on this device. No cloud sync, no remote server."/>

      <div className="grid-2">
        <div className="card" style={{ background: "var(--positive-tint)", borderColor: "transparent" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--positive)" }}>
            <I.shield size={16}/>
            <div style={{ fontSize: 11.5, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase" }}>Vault status</div>
          </div>
          <div style={{ fontSize: 18, fontWeight: 500, color: "var(--positive)", marginTop: 8 }}>Local & encrypted</div>
          <div style={{ fontSize: 12.5, color: "var(--ink-2)", marginTop: 4 }}>{visible.length} document{visible.length===1?"":"s"} · {visible.reduce((s, d) => s + d.rows, 0).toLocaleString()} rows on disk</div>
        </div>
        <div className="card">
          <div className="card-title">Agent permissions</div>
          <div className="num" style={{ fontSize: 18, marginTop: 8 }}>Read-only</div>
          <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>No agent can initiate transfers — statements are read-only</div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-head">
          <div>
            <div className="card-title">Security checklist</div>
            <div className="card-sub">{securityChecks.filter(s => s.status === "ok").length} of {securityChecks.length} complete</div>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {securityChecks.map((s, i) => (
            <div key={i} style={{
              display: "flex", gap: 14, alignItems: "flex-start",
              padding: "14px 0",
              borderTop: i ? "1px solid var(--line)" : "none",
            }}>
              <div style={{
                width: 22, height: 22, borderRadius: 999,
                background: s.status === "ok" ? "var(--positive-tint)" : "var(--warn-tint)",
                color: s.status === "ok" ? "var(--positive)" : "var(--warn)",
                display: "grid", placeItems: "center",
                flexShrink: 0,
              }}>
                {s.status === "ok" ? <I.check size={12}/> : <I.alert size={12}/>}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13.5, fontWeight: 500 }}>{s.label}</div>
                <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>{s.desc}</div>
              </div>
              <span className="tag" style={{
                fontSize: 11,
                background: s.status === "ok" ? "var(--positive-tint)" : "var(--warn-tint)",
                color: s.status === "ok" ? "var(--positive)" : "var(--warn)",
                border: "none",
              }}>{s.status === "ok" ? "Active" : "Action needed"}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-head">
          <div>
            <div className="card-title">Uploaded documents · {visible.length}</div>
            <div className="card-sub">Read-only · remove any source instantly</div>
          </div>
          {visible.length > 0 && (
            confirmAll ? (
              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <span style={{ fontSize: 12, color: "var(--ink-2)" }}>Remove all {visible.length}?</span>
                <button className="btn ghost" style={{ fontSize: 12 }} onClick={() => setConfirmAll(false)}>Cancel</button>
                <button className="btn" style={{ fontSize: 12, color: "var(--surface)", background: "var(--negative)", borderColor: "var(--negative)" }}
                  onClick={() => { setRemoved(docs.map(d => d.name)); setConfirmAll(false); }}>Confirm</button>
              </div>
            ) : (
              <button className="btn ghost" style={{ fontSize: 12, color: "var(--negative)" }}
                onClick={() => setConfirmAll(true)}>
                <I.x size={12}/> Remove all
              </button>
            )
          )}

        </div>
        <table className="table">
          <thead>
            <tr>
              <th>File</th>
              <th>Source</th>
              <th>Rows</th>
              <th>Added</th>
              <th style={{ width: 90 }}></th>
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 ? (
              <tr><td colSpan={5} className="muted" style={{ textAlign: "center", padding: 24, fontSize: 13 }}>No documents in vault. Upload from the Documents page to get started.</td></tr>
            ) : visible.map((d, i) => (
              <tr key={i}>
                <td className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{d.name}</td>
                <td><span className="tag">{d.source}</span></td>
                <td className="mono muted" style={{ fontSize: 12 }}>{d.rows}</td>
                <td className="muted" style={{ fontSize: 12 }}>{d.added}</td>
                <td><button className="btn ghost" style={{ fontSize: 12, color: "var(--negative)" }}
                  onClick={() => setRemoved((r) => [...r, d.name])}>Remove</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}


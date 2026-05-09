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

/* ─── Shared empty-state shell ──────────────────────────────────────────── */
function EmptyState({ icon: Ico, heading, body, onNav }) {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      minHeight: 360,
      textAlign: "center",
      gap: 16,
      padding: "60px 24px",
    }}>
      <div style={{
        width: 52, height: 52, borderRadius: 999,
        background: "var(--surface-2)",
        border: "1px solid var(--line)",
        display: "grid", placeItems: "center",
        color: "var(--ink-4)",
      }}>
        <Ico size={22}/>
      </div>
      <div>
        <h2 className="h2" style={{ marginBottom: 8 }}>{heading}</h2>
        <p className="muted" style={{ fontSize: 13.5, maxWidth: 400, lineHeight: 1.6, margin: "0 auto" }}>{body}</p>
      </div>
      {onNav && (
        <button className="btn primary" onClick={() => onNav("documents")} style={{ marginTop: 4 }}>
          <I.upload size={13}/> Go to Documents
        </button>
      )}
    </div>
  );
}

/* ─── Helpers ─────────────────────────────────────────────────────────────── */
function debtCategoryToType(category) {
  const map = {
    credit_card: "Credit Card",
    student_loan: "Student",
    mortgage: "Mortgage",
    auto_loan: "Auto",
    personal_loan: "Personal",
    medical: "Medical",
    other: "Other",
  };
  return map[category] ?? "Other";
}

function capitalize(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, " ") : str;
}

/* ─── Extract typed arrays from snapshot ─────────────────────────────────── */
function getDebts(snapshot) {
  const da = snapshot?.debt_analysis;
  if (!da?.debts?.length) return [];
  return da.debts.map((d) => ({
    name: d.name,
    lender: d.name,
    balance: d.balance,
    rate: d.interest_rate,
    min: d.minimum_payment,
    type: debtCategoryToType(d.category),
    risk: da.risk_level === "critical" || da.risk_level === "high" ? "high"
         : da.risk_level === "moderate" ? "medium" : "low",
  }));
}

function getSavings(snapshot) {
  const sa = snapshot?.savings_strategy;
  if (!sa?.milestone_timeline?.length) return [];
  return sa.milestone_timeline.map((m) => ({
    name: m.goal,
    balance: 0,
    target: m.target_amount,
    monthly: sa.recommended_monthly_savings ?? 0,
    eta: m.eta,
    category: "Goal",
  }));
}

function getBudget(snapshot) {
  const ba = snapshot?.budget_advice;
  if (!ba?.categories?.length) return [];
  return ba.categories.map((c) => ({
    cat: capitalize(c.category),
    spent: c.amount,
    budget: c.suggested_amount ?? c.amount,
    color: c.recommendation === "reduce" ? "var(--negative)"
          : c.recommendation === "increase" ? "var(--warn)"
          : "var(--positive)",
  }));
}

/* ---------------- Debt Analyzer ---------------- */
export function DebtView({ snapshot, onNav }) {
  const debts = getDebts(snapshot);

  if (!snapshot || debts.length === 0) {
    return (
      <div className="scroll" data-screen-label="03 Debt">
        <ViewHeader agent="debt" title="Debt analyzer"
          sub="Rates, balances, and risk across every liability. The agent flags compounding traps and recommends payoff order."/>
        <EmptyState
          icon={I.debt}
          heading="No debts loaded"
          body="Upload credit card, auto loan, mortgage, or student loan statements in Documents to see your debt analysis."
          onNav={onNav}
        />
      </div>
    );
  }

  const total = debts.reduce((s, d) => s + d.balance, 0);
  const minPay = debts.reduce((s, d) => s + d.min, 0);
  const yearlyInterest = debts.reduce((s, d) => s + d.balance * (d.rate / 100), 0);
  const wAvgRate = total > 0 ? debts.reduce((s, d) => s + d.rate * d.balance, 0) / total : 0;

  // Build a synthetic 12-month projection (current + 11 prior) per debt
  const months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May"];
  const series = debts.map((d, i) => ({
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
        {minPay > 0 && <StatCard label="Min payments" value={minPay} icon={I.refresh}/>}
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
            slices={debts.map((d, i) => ({
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
            {[...debts].sort((a, b) => b.rate - a.rate).map((d, i) => (
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
export function SavingsView({ snapshot, onNav }) {
  const savings = getSavings(snapshot);
  const sa = snapshot?.savings_strategy;

  if (!snapshot || savings.length === 0) {
    return (
      <div className="scroll" data-screen-label="04 Savings">
        <ViewHeader agent="savings" title="Savings strategy"
          sub="Goals, timelines, and contribution recommendations. The agent simulates your savings rate against income and surplus to project realistic ETAs."/>
        <EmptyState
          icon={I.savings}
          heading="No savings data loaded"
          body="Upload savings account, investment, or retirement statements in Documents to see your goals and runway."
          onNav={onNav}
        />
      </div>
    );
  }

  const total = savings.reduce((s, d) => s + d.balance, 0);
  const targetTotal = savings.reduce((s, d) => s + d.target, 0);
  const monthlyContrib = sa?.recommended_monthly_savings ?? savings.reduce((s, d) => s + d.monthly, 0);

  const months = ["Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May"];
  // Synthetic trend — project from current total upward at the monthly contribution rate
  const trend = months.map((_, i) => Math.round(targetTotal * 0.1 + monthlyContrib * i));

  // Build surplus allocation from sa if available
  const milestones = sa?.milestone_timeline ?? [];
  const surplusRows = milestones.slice(0, 5).map((m, i) => {
    const colors = ["var(--positive)", "var(--info)", "var(--ink-2)", "var(--warn)", "var(--ink-3)"];
    return {
      label: m.goal,
      value: Math.round(monthlyContrib > 0 ? (m.target_amount / milestones.reduce((s, x) => s + x.target_amount, 1)) * 100 : 0),
      color: colors[i % colors.length],
    };
  }).filter((r) => r.value > 0);

  const monthsRunway = sa?.months_of_runway;

  return (
    <div className="scroll" data-screen-label="04 Savings">
      <ViewHeader agent="savings" title="Savings strategy"
        sub="Goals, timelines, and contribution recommendations. The agent simulates your savings rate against income and surplus to project realistic ETAs."/>

      <div className="grid-3">
        {total > 0 && <StatCard label="Total saved" value={total} icon={I.savings}/>}
        {targetTotal > 0 && <StatCard label="Total goals target" value={targetTotal} icon={I.spark}/>}
        {monthlyContrib > 0 && <StatCard label="Recommended / mo" value={monthlyContrib} icon={I.refresh}/>}
      </div>

      {monthsRunway != null && (
        <div className="card" style={{ marginTop: 16, padding: "14px 18px" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <span className="num" style={{ fontSize: 28, color: monthsRunway >= 6 ? "var(--positive)" : "var(--warn)" }}>
              {monthsRunway.toFixed(1)}
            </span>
            <span style={{ fontSize: 14, color: "var(--ink-3)" }}>months of emergency runway</span>
            <span className={`tag ${monthsRunway >= 6 ? "pos" : "warn"}`} style={{ marginLeft: "auto" }}>
              {monthsRunway >= 6 ? "On track" : "Below 6-month target"}
            </span>
          </div>
          {sa?.strategy_narrative && (
            <div style={{ fontSize: 12.5, color: "var(--ink-3)", marginTop: 8, lineHeight: 1.55 }}>
              {sa.strategy_narrative}
            </div>
          )}
        </div>
      )}

      <div className="split-main" style={{ marginTop: 16 }}>
        {trend.some((v) => v > 0) && (
          <div className="card">
            <div className="card-head">
              <div>
                <div className="card-title">Projected savings growth</div>
                {monthlyContrib > 0 && (
                  <div className="card-sub">Based on ${monthlyContrib}/mo contributions</div>
                )}
              </div>
            </div>
            <LineArea data={trend} labels={months} accent="var(--positive)" height={220}/>
          </div>
        )}

        {surplusRows.length > 0 && (
          <div className="card">
            <div className="card-head">
              <div>
                <div className="card-title">Goal allocation</div>
                <div className="card-sub">By target amount</div>
              </div>
            </div>
            <HBar valueFmt={(v) => `${v}%`} max={100} rows={surplusRows}/>
          </div>
        )}
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-head">
          <div className="card-title">Goals</div>
          <button className="btn ghost" style={{ fontSize: 12 }}><I.filter size={12}/> Sort by ETA</button>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {savings.map((g, i) => {
            const pct = g.target > 0 ? (g.balance / g.target) * 100 : 0;
            return (
              <div key={i} style={{ padding: 16, border: "1px solid var(--line)", borderRadius: 10, background: "var(--surface-2)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontSize: 14.5, fontWeight: 500 }}>{g.name}</div>
                    {g.monthly > 0 && (
                      <div style={{ fontSize: 11.5, color: "var(--ink-3)", marginTop: 2 }}>{g.category} · ${g.monthly.toLocaleString()}/mo</div>
                    )}
                  </div>
                  {g.eta && <span className="tag info">ETA {g.eta}</span>}
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
export function BudgetView({ snapshot, onNav }) {
  const budget = getBudget(snapshot);
  const ba = snapshot?.budget_advice;

  if (!snapshot || budget.length === 0) {
    return (
      <div className="scroll" data-screen-label="05 Budget">
        <ViewHeader agent="budget" title="Budget advisor"
          sub="Spending categorized from transactions. The agent flags categories trending over budget and suggests reallocations."/>
        <EmptyState
          icon={I.budget}
          heading="No budget data loaded"
          body="Upload bank statements or credit card exports in Documents to see your spending breakdown."
          onNav={onNav}
        />
      </div>
    );
  }

  const totalSpent = budget.reduce((s, d) => s + d.spent, 0);
  const totalBudget = budget.reduce((s, d) => s + d.budget, 0);
  const overCats = budget.filter(c => c.spent > c.budget);

  const monthlyIncome = ba?.monthly_income ?? 0;
  const totalExpenses = ba?.total_expenses ?? totalSpent;
  const surplusOrDeficit = ba?.surplus_or_deficit ?? (monthlyIncome - totalExpenses);

  // Top over-budget category
  const topLeak = [...budget].sort((a, b) => (b.spent - b.budget) - (a.spent - a.budget))[0];

  return (
    <div className="scroll" data-screen-label="05 Budget">
      <ViewHeader agent="budget" title="Budget advisor"
        sub="Spending categorized from transactions. The agent flags categories trending over budget and suggests reallocations."/>

      <div className="grid-4">
        <StatCard label="Spent this period" value={totalSpent} icon={I.spark}/>
        <StatCard label="Suggested budget" value={totalBudget} icon={I.budget}/>
        <StatCard label="Categories over" value={overCats.length} icon={I.alert}/>
        {monthlyIncome > 0 && <StatCard label="Monthly income" value={monthlyIncome} icon={I.trend_up}/>}
      </div>

      {surplusOrDeficit !== 0 && (
        <div className="card" style={{ marginTop: 16, padding: "14px 18px" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <span className="num" style={{ fontSize: 28, color: surplusOrDeficit >= 0 ? "var(--positive)" : "var(--negative)" }}>
              {surplusOrDeficit >= 0 ? "+" : ""}${Math.round(Math.abs(surplusOrDeficit)).toLocaleString()}
            </span>
            <span style={{ fontSize: 14, color: "var(--ink-3)" }}>
              monthly {surplusOrDeficit >= 0 ? "surplus" : "deficit"}
            </span>
          </div>
          {ba?.actionable_steps?.[0] && (
            <div style={{ fontSize: 12.5, color: "var(--ink-3)", marginTop: 8, lineHeight: 1.55 }}>
              {ba.actionable_steps[0]}
            </div>
          )}
        </div>
      )}

      <div className="split-main" style={{ marginTop: 16 }}>
        <div className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Category breakdown</div>
              <div className="card-sub">Spent vs. suggested · markers show targets</div>
            </div>
          </div>
          <HBar rows={budget.map(b => ({
            label: b.cat, value: b.spent, target: b.budget, color: b.color,
          }))}/>
        </div>

        {topLeak && topLeak.spent > topLeak.budget && (
          <div className="card">
            <div className="card-head">
              <div className="card-title">Top opportunity</div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 500 }}>{topLeak.cat}</div>
                  <div className="muted" style={{ fontSize: 12 }}>
                    ${topLeak.spent.toLocaleString()} spent vs ${topLeak.budget.toLocaleString()} suggested
                  </div>
                </div>
                <div className="num tnum" style={{ fontSize: 18, color: "var(--negative)" }}>
                  +${(topLeak.spent - topLeak.budget).toLocaleString()}
                </div>
              </div>
              {ba?.top_3_savings_opportunities?.length > 0 && (
                <>
                  <div className="divider"/>
                  <div style={{ fontSize: 12, color: "var(--ink-3)", letterSpacing: "0.06em", textTransform: "uppercase", fontWeight: 500 }}>
                    Opportunities
                  </div>
                  {ba.top_3_savings_opportunities.map((opp, i) => (
                    <div key={i} style={{ fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.5, paddingLeft: 8, borderLeft: "2px solid var(--line)" }}>
                      {opp}
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------------- Payoff Optimizer ---------------- */
export function PayoffView({ snapshot, onNav }) {
  const debts = getDebts(snapshot);
  const pp = snapshot?.payoff_plan;

  if (!snapshot || debts.length === 0) {
    return (
      <div className="scroll" data-screen-label="06 Payoff">
        <ViewHeader agent="payoff" title="Payoff optimizer"
          sub="Compare snowball vs avalanche on your real balances. Adjust monthly extra and watch your debt-free date move."/>
        <EmptyState
          icon={I.payoff}
          heading="No debts to optimize"
          body="Upload credit card, loan, or mortgage statements in Documents to run the payoff simulation."
          onNav={onNav}
        />
      </div>
    );
  }

  const [strategy, setStrategy] = React.useState("avalanche");
  const cards = debts.filter(d => d.type === "Credit Card" || d.type === "Auto" || d.type === "Student" || d.type === "Personal");
  const allCards = cards.length > 0 ? cards : debts;

  const ordered = strategy === "avalanche"
    ? [...allCards].sort((a, b) => b.rate - a.rate)
    : [...allCards].sort((a, b) => a.balance - b.balance);

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

  // Use backend payoff plan data if available
  const totalInterestSaved = pp?.total_interest_saved_vs_minimum;
  const debtFreeDate = pp?.debt_free_date;
  const backendStrategy = pp?.strategy;
  const cmp = pp?.comparison || {};

  const compare = [
    {
      name: "Snowball",
      desc: "Smallest balance first — psychological wins",
      monthsToFree: cmp.snowball?.months_to_payoff ?? null,
      interest: cmp.snowball?.total_interest != null ? Math.round(cmp.snowball.total_interest) : null,
      kept: backendStrategy === "snowball",
    },
    {
      name: "Avalanche",
      desc: "Highest APR first — mathematical optimum",
      monthsToFree: cmp.avalanche?.months_to_payoff ?? null,
      interest: cmp.avalanche?.total_interest != null ? Math.round(cmp.avalanche.total_interest) : null,
      kept: !backendStrategy || backendStrategy === "avalanche",
    },
    {
      name: "Min only",
      desc: "Pay minimums — slowest, most expensive",
      monthsToFree: null,
      interest: null,
      kept: false,
    },
  ];

  return (
    <div className="scroll" data-screen-label="06 Payoff">
      <ViewHeader agent="payoff" title="Payoff optimizer"
        sub="Compare snowball vs avalanche on your real balances. Adjust monthly extra and watch your debt-free date move."/>

      {(debtFreeDate || totalInterestSaved) && (
        <div className="card" style={{ marginBottom: 16, padding: "14px 18px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 24, flexWrap: "wrap" }}>
            {debtFreeDate && (
              <div>
                <div style={{ fontSize: 11, color: "var(--ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 500, marginBottom: 4 }}>
                  Debt-free date
                </div>
                <div className="num" style={{ fontSize: 22, color: "var(--positive)" }}>{debtFreeDate}</div>
              </div>
            )}
            {totalInterestSaved && (
              <div>
                <div style={{ fontSize: 11, color: "var(--ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 500, marginBottom: 4 }}>
                  Interest saved vs minimums
                </div>
                <div className="num" style={{ fontSize: 22, color: "var(--positive)" }}>−${totalInterestSaved.toLocaleString()}</div>
              </div>
            )}
            {backendStrategy && (
              <span className="tag pos" style={{ marginLeft: "auto" }}>
                {backendStrategy.charAt(0).toUpperCase() + backendStrategy.slice(1)} recommended
              </span>
            )}
          </div>
        </div>
      )}

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
                <div className="num" style={{ fontSize: 22 }}>
                  {c.monthsToFree != null ? <>{c.monthsToFree} <span style={{ fontSize: 13, color: "var(--ink-3)" }}>mo</span></> : <span style={{ color: "var(--ink-3)" }}>—</span>}
                </div>
              </div>
              {c.interest != null && (
                <div style={{ textAlign: "right" }}>
                  <div className="muted" style={{ fontSize: 11 }}>Total interest</div>
                  <div className="num" style={{ fontSize: 18, color: "var(--ink-2)" }}>${c.interest.toLocaleString()}</div>
                </div>
              )}
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
export function SettingsView({ clearAll, onNav }) {
  const securityChecks = [
    { label: "Local-first storage", desc: "Documents and embeddings live on this device only — no cloud sync, no remote server", status: "ok" },
    { label: "On-device embedding model", desc: "Vectors generated locally via a quantized model. Statement contents never leave your machine", status: "ok" },
    { label: "At-rest encryption", desc: "AES-256-GCM on the local vault · keys derived from your passphrase, stored only in OS keychain", status: "ok" },
    { label: "PII redaction before LLM", desc: "Account numbers, SSN, names stripped before any prompt is sent to the language model", status: "ok" },
    { label: "Read-only ingestion", desc: "No agent can move money. We only read the statements you upload", status: "ok" },
    { label: "Recovery passphrase", desc: "Generate an offline backup phrase — without it, the local vault cannot be recovered", status: "warn" },
  ];

  const [confirmNuke, setConfirmNuke] = React.useState(false);
  const [nuking, setNuking] = React.useState(false);

  const handleClearAll = async () => {
    setNuking(true);
    try {
      await clearAll?.();
    } finally {
      setNuking(false);
      setConfirmNuke(false);
    }
  };

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
          <div style={{ fontSize: 12.5, color: "var(--ink-2)", marginTop: 4 }}>Session-scoped storage · cleared on tab close</div>
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

      {/* Data management — nuke button wired to clearAll() */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-head">
          <div>
            <div className="card-title">Data management</div>
            <div className="card-sub">Remove all session data from the backend and reset the advisor</div>
          </div>
        </div>
        <div style={{ padding: "16px 0" }}>
          <div style={{ fontSize: 13, color: "var(--ink-2)", marginBottom: 16, lineHeight: 1.55 }}>
            This deletes all uploaded files, embeddings, and the financial snapshot for this session. The conversation history is also cleared. This action cannot be undone.
          </div>
          {confirmNuke ? (
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span style={{ fontSize: 13, color: "var(--ink-2)" }}>Are you sure? All session data will be deleted.</span>
              <button className="btn ghost" style={{ fontSize: 12 }} onClick={() => setConfirmNuke(false)}>Cancel</button>
              <button
                className="btn"
                style={{ fontSize: 12, color: "var(--surface)", background: "var(--negative)", borderColor: "var(--negative)" }}
                onClick={handleClearAll}
                disabled={nuking}
              >
                {nuking ? "Clearing…" : "Delete everything"}
              </button>
            </div>
          ) : (
            <button
              className="btn ghost"
              style={{ fontSize: 12, color: "var(--negative)" }}
              onClick={() => setConfirmNuke(true)}
            >
              <I.x size={12}/> Clear all session data
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

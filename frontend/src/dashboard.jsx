import React from 'react';
import { I } from './icons.jsx';
import { AGENT_META } from './data.js';
import { Sparkline, Donut } from './charts.jsx';

/* Dashboard view — hero stats, net worth chart, agent insights, transactions */

export function StatCard({ label, value, cents, delta, deltaLabel, sparkData, sparkColor, accent, icon: Ico, skeleton }) {
  const positive = (delta ?? 0) >= 0;
  return (
    <div className="stat">
      <div className="stat-label">
        {Ico && <Ico size={12}/>}
        {label}
      </div>
      {skeleton
        ? (
          <div
            className="skeleton"
            style={{ width: 80, height: 28, marginTop: 2 }}
            aria-label="Loading…"
            aria-busy="true"
          />
        ) : (
          <div className="stat-value">
            ${Math.abs(value).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            {cents != null && <span className="cents">.{cents}</span>}
          </div>
        )
      }
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
  return (
    <div style={{ padding: "12px 0", borderBottom: "1px solid var(--line)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div>
          <div style={{ fontSize: 13.5, fontWeight: 500 }}>{g.name}</div>
          <div style={{ fontSize: 11, color: "var(--ink-3)" }}>{g.category}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="num tnum" style={{ fontSize: 15 }}>${g.target.toLocaleString()}</div>
          {g.eta && <div style={{ fontSize: 11, color: "var(--ink-3)" }}>ETA {g.eta}</div>}
        </div>
      </div>
    </div>
  );
}

/* ─── Data-source badge ──────────────────────────────────────────────────── */
function DataBadge({ live }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      fontSize: 11, padding: "3px 8px", borderRadius: 20,
      background: live ? "var(--positive-tint)" : "var(--surface-2)",
      border: `1px solid ${live ? "var(--positive)" : "var(--line)"}`,
      color: live ? "var(--positive)" : "var(--ink-4)",
      fontWeight: 500,
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: 999,
        background: live ? "var(--positive)" : "var(--ink-4)",
      }}/>
      {live ? "Live data" : "No data"}
    </span>
  );
}

/* ─── Helper: map snapshot fields to debt/savings/budget arrays ──────────── */
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

function snapshotToStats(snapshot) {
  if (!snapshot) return null;

  const da = snapshot.debt_analysis;
  const ba = snapshot.budget_advice;
  const sa = snapshot.savings_strategy;
  const pp = snapshot.payoff_plan;

  const debts = da?.debts?.map((d) => ({
    name: d.name,
    lender: d.name,
    balance: d.balance,
    rate: d.interest_rate,
    min: d.minimum_payment,
    type: debtCategoryToType(d.category),
    risk: da.risk_level === "critical" || da.risk_level === "high" ? "high"
         : da.risk_level === "moderate" ? "medium" : "low",
  })) ?? [];

  const savings = sa?.milestone_timeline?.map((m) => ({
    name: m.goal,
    target: m.target_amount,
    monthly: sa.recommended_monthly_savings ?? 0,
    eta: m.eta,
    category: "Goal",
  })) ?? [];

  const budget = ba?.categories?.map((c) => ({
    cat: capitalize(c.category),
    spent: c.amount,
    budget: c.suggested_amount ?? c.amount,
    color: c.recommendation === "reduce" ? "var(--negative)"
          : c.recommendation === "increase" ? "var(--warn)"
          : "var(--positive)",
  })) ?? [];

  const monthlyIncome = ba?.monthly_income ?? 0;
  const monthlyExpenses = ba?.total_expenses ?? 0;
  const cashFlow = monthlyIncome - monthlyExpenses;
  const totalDebt = da?.total_debt ?? debts.reduce((s, d) => s + d.balance, 0);
  const totalSavings = sa?.current_emergency_fund ?? 0;

  return {
    debts,
    savings,
    budget,
    monthlyIncome,
    monthlyExpenses,
    cashFlow,
    totalDebt,
    totalSavings,
    riskLevel: da?.risk_level ?? null,
    topSavingsOpp: sa?.milestone_timeline?.[0]?.goal ?? null,
    debtFreeDate: pp?.debt_free_date ?? null,
    weightedAvgInterest: da?.weighted_avg_interest ?? null,
  };
}

/* ─── Live insight cards derived from snapshot ───────────────────────────── */
function LiveInsightCards({ snapshot }) {
  const da = snapshot.debt_analysis;
  const ba = snapshot.budget_advice;
  const sa = snapshot.savings_strategy;
  const pp = snapshot.payoff_plan;

  const cards = [];

  if (da) {
    cards.push({
      agent: "debt",
      headline: `${da.risk_level === "critical" || da.risk_level === "high" ? "High-rate" : "Active"} debt: $${Math.round(da.total_debt / 1000)}k total`,
      body: da.summary ?? `Weighted avg interest: ${da.weighted_avg_interest?.toFixed(2) ?? "—"}%. ${da.highest_priority_debt ? `Pay ${da.highest_priority_debt} first.` : ""}`,
      metric: da.weighted_avg_interest ? `${da.weighted_avg_interest.toFixed(1)}%` : null,
      metricSub: "weighted avg APR",
      action: "See debt analysis",
    });
  }

  if (pp) {
    const saved = pp.total_interest_saved_vs_minimum;
    cards.push({
      agent: "payoff",
      headline: `${capitalize(pp.strategy)} strategy recommended`,
      body: saved
        ? `Save $${saved.toLocaleString()} vs minimum payments. Debt-free: ${pp.debt_free_date ?? "—"}.`
        : `Debt-free date: ${pp.debt_free_date ?? "—"}.`,
      metric: saved ? `−$${Math.round(saved / 1000)}k` : pp.debt_free_date ?? null,
      metricSub: saved ? "vs min payments" : "debt-free date",
      action: "Compare strategies",
    });
  }

  if (sa) {
    const months = sa.months_of_runway ?? 0;
    cards.push({
      agent: "savings",
      headline: `${months.toFixed(1)} months runway`,
      body: sa.strategy_narrative ?? `Emergency fund target: $${sa.emergency_fund_target?.toLocaleString() ?? "—"}. Save $${sa.recommended_monthly_savings?.toLocaleString() ?? "—"}/mo.`,
      metric: `${months.toFixed(1)}mo`,
      metricSub: "emergency runway",
      action: "Adjust goal",
    });
  }

  if (ba) {
    const top3 = ba.top_3_savings_opportunities ?? [];
    const over = ba.categories?.filter((c) => c.recommendation === "reduce") ?? [];
    cards.push({
      agent: "budget",
      headline: over.length > 0 ? `${over.length} categor${over.length === 1 ? "y" : "ies"} to reduce` : "Budget on track",
      body: top3[0] ?? (ba.actionable_steps?.[0] ?? "Review your spending breakdown."),
      metric: ba.surplus_or_deficit != null ? (ba.surplus_or_deficit >= 0 ? `+$${Math.round(ba.surplus_or_deficit)}` : `−$${Math.round(Math.abs(ba.surplus_or_deficit))}`) : null,
      metricSub: ba.surplus_or_deficit >= 0 ? "monthly surplus" : "monthly deficit",
      action: "See breakdown",
    });
  }

  if (cards.length === 0) return null;

  return (
    <div className="grid-4">
      {cards.map((c, i) => <AgentInsightCard key={i} {...c}/>)}
    </div>
  );
}

/* ─── Empty state for the full dashboard ────────────────────────────────── */
function DashboardEmpty({ openChat, onNav }) {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      minHeight: 420,
      textAlign: "center",
      gap: 16,
      padding: "60px 24px",
    }}>
      <div style={{
        width: 56, height: 56, borderRadius: 999,
        background: "var(--surface-2)",
        border: "1px solid var(--line)",
        display: "grid", placeItems: "center",
        color: "var(--ink-4)",
      }}>
        <I.dashboard size={24}/>
      </div>
      <div>
        <h2 className="h2" style={{ marginBottom: 8 }}>No data yet</h2>
        <p className="muted" style={{ fontSize: 13.5, maxWidth: 400, lineHeight: 1.6, margin: "0 auto" }}>
          Drop a statement in <strong>Documents</strong> to populate your overview — net worth, debts, savings, and budget all derive from your uploaded files.
        </p>
      </div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "center", marginTop: 8 }}>
        <button className="btn primary" onClick={() => onNav?.("documents")}>
          <I.upload size={13}/> Go to Documents
        </button>
        <button className="btn ghost" onClick={openChat}>
          <I.chat size={13}/> Ask advisor
        </button>
      </div>
    </div>
  );
}

/* ─── Dashboard ──────────────────────────────────────────────────────────── */
function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning.";
  if (h < 17) return "Good afternoon.";
  return "Good evening.";
}

export function Dashboard({ snapshot, snapshotStatus, loading, openChat, onNav }) {
  const stats = snapshotToStats(snapshot);

  // Show loading state
  if (loading && !snapshot) {
    return (
      <div className="scroll" data-screen-label="01 Dashboard">
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "40px 0", color: "var(--ink-4)" }}>
          <span className="spinner" style={{ width: 16, height: 16, borderColor: "currentColor", borderTopColor: "transparent" }}/>
          <span style={{ fontSize: 14 }}>Loading your data…</span>
        </div>
      </div>
    );
  }

  const hasData = !!(snapshot && stats);
  const { debts = [], savings = [], budget = [], cashFlow = 0, totalDebt = 0, totalSavings = 0, riskLevel = null } = stats ?? {};

  const totalSpent = budget.reduce((s, d) => s + d.spent, 0);
  const totalBudget = budget.reduce((s, d) => s + d.budget, 0);

  return (
    <div className="scroll" data-screen-label="01 Dashboard">
      {/* Greeting row */}
      <div className="hero-row" style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 18, gap: 16 }}>
        <div>
          <div className="eyebrow" style={{ marginBottom: 6 }}>
            {new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}
            {loading && (
              <span style={{ marginLeft: 10, display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, color: "var(--ink-4)" }}>
                <span className="spinner" style={{ width: 8, height: 8, borderColor: "currentColor", borderTopColor: "transparent" }}/>
                Refreshing…
              </span>
            )}
          </div>
          <h1 className="h1" style={{ fontFamily: "var(--font-num)", fontWeight: 400, fontSize: 30, letterSpacing: "-0.02em" }}>
            {getGreeting()}
          </h1>
          <div className="muted" style={{ fontSize: 13.5, marginTop: 4 }}>
            {!hasData
              ? <span>No data yet — upload a statement to begin.</span>
              : riskLevel === "critical" || riskLevel === "high"
              ? <span>Your advisor has flagged <span style={{ color: "var(--negative)", fontWeight: 500 }}>high-risk items</span> to review.</span>
              : <span>Your finances are <span style={{ color: "var(--positive)", fontWeight: 500 }}>on track</span> — live data loaded.</span>
            }
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <DataBadge live={hasData}/>
          <button className="btn" onClick={openChat}><I.chat size={13}/> Ask advisor</button>
          <button className="btn primary" onClick={() => onNav?.("documents")}><I.upload size={13}/> Add document</button>
        </div>
      </div>

      {/* Hero stats */}
      <div className="grid-4">
        <StatCard label="Total debt" value={totalDebt} icon={I.debt}/>
        <StatCard label="Total savings" value={totalSavings} icon={I.savings}/>
        <StatCard label="Cash flow" value={Math.abs(cashFlow)} icon={I.spark}/>
        <StatCard label="Monthly spending" value={totalSpent} icon={I.budget}/>
      </div>

      {/* Budget chart when we have data */}
      {budget.length > 0 && (
        <div className="split-main" style={{ marginTop: 16 }}>
          <div className="card">
            <div className="card-head">
              <div>
                <div className="card-title">Monthly spending</div>
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
              slices={budget.slice(0, 6).map((b, idx) => ({
                label: b.cat, value: b.spent,
                color: ["#0E2238", "#2C4F7C", "#1E6B52", "#B27A1E", "#9E3A37", "#5C6B82"][idx % 6],
              }))}
              size={140}
              thickness={20}
              centerLabel={totalBudget > 0 ? `${Math.round((totalSpent / totalBudget) * 100)}%` : "—"}
              centerSub="OF BUDGET"
            />
          </div>

          <div className="card">
            <div className="card-head">
              <div>
                <div className="card-title">Budget categories</div>
                <div className="card-sub">Spent vs. suggested</div>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, paddingTop: 4 }}>
              {budget.slice(0, 6).map((b, i) => {
                const pct = b.budget > 0 ? Math.min(100, Math.round((b.spent / b.budget) * 100)) : 0;
                return (
                  <div key={i}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
                      <span style={{ color: "var(--ink-2)", fontWeight: 500 }}>{b.cat}</span>
                      <span className="num tnum" style={{ fontSize: 12, color: b.spent > b.budget ? "var(--negative)" : "var(--ink-3)" }}>
                        ${b.spent.toLocaleString()} / ${b.budget.toLocaleString()}
                      </span>
                    </div>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${pct}%`, background: b.color }}/>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Agent insights */}
      <div style={{ marginTop: 24 }}>
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 12 }}>
          <div>
            <h2 className="h2">What your advisors noticed</h2>
            <div className="muted" style={{ fontSize: 12.5 }}>Updated automatically as new transactions are ingested</div>
          </div>
          <button className="btn ghost" style={{ fontSize: 12 }}><I.refresh size={12}/> Re-analyze</button>
        </div>

        {hasData
          ? <LiveInsightCards snapshot={snapshot}/>
          : (
            <div className="grid-4">
              {["debt", "payoff", "savings", "budget"].map((agent) => {
                const meta = AGENT_META[agent];
                const isComputing = snapshotStatus === "computing";
                return (
                  <div key={agent} className="card" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span className="agent-dot" style={{ background: meta.color, width: 8, height: 8 }}/>
                      <span style={{ fontSize: 11, color: "var(--ink-3)", letterSpacing: "0.06em", textTransform: "uppercase", fontWeight: 500 }}>
                        {meta.label}
                      </span>
                    </div>
                    <div style={{ fontSize: 15, fontWeight: 500, color: "var(--ink-3)" }}>
                      {isComputing ? "Analyzing…" : "Awaiting data"}
                    </div>
                    <div style={{ fontSize: 12.5, color: "var(--ink-4)", lineHeight: 1.5, display: "flex", alignItems: "center", gap: 6 }}>
                      {isComputing && (
                        <span
                          className="spinner"
                          style={{ width: 11, height: 11, borderColor: "var(--ink-4)", borderTopColor: "transparent", flexShrink: 0 }}
                          aria-hidden="true"
                        />
                      )}
                      {isComputing ? "Analyzing your statements…" : "Will populate after you add documents."}
                    </div>
                  </div>
                );
              })}
            </div>
          )
        }
      </div>

      {/* Activity + Goals */}
      <div className="split-main" style={{ marginTop: 24 }}>
        <div className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Recent activity</div>
              <div className="card-sub">Parsed from your uploaded statements</div>
            </div>
          </div>
          <div style={{
            padding: "32px 0",
            textAlign: "center",
            color: "var(--ink-4)",
            fontSize: 13,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 10,
          }}>
            <I.doc size={22} style={{ color: "var(--ink-4)" }}/>
            <div>Upload a statement to see transactions.</div>
            <button className="btn ghost" style={{ fontSize: 12 }} onClick={() => onNav?.("documents")}>
              Go to Documents
            </button>
          </div>
        </div>

        {savings.length > 0 ? (
          <div className="card">
            <div className="card-head">
              <div>
                <div className="card-title">Savings goals</div>
                <div className="card-sub">{savings.length} goal{savings.length === 1 ? "" : "s"} detected</div>
              </div>
            </div>
            <div>
              {savings.map((g, i) => <GoalRow key={i} g={g}/>)}
            </div>
          </div>
        ) : (
          <div className="card">
            <div className="card-head">
              <div className="card-title">Savings goals</div>
            </div>
            <div style={{
              padding: "32px 0",
              textAlign: "center",
              color: "var(--ink-4)",
              fontSize: 13,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 10,
            }}>
              <I.savings size={22} style={{ color: "var(--ink-4)" }}/>
              <div>Upload savings or investment statements to see goals.</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

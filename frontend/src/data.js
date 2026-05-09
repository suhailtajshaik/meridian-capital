/* Sample data — mid-career persona, realistic finance app context. */
/* No real account numbers; this is design data only. */

export const PERSONAS = {
  midcareer: {
    name: "Maya Patel",
    initials: "MP",
    netWorth: 184320,
    netWorthDelta: 4280,
    netWorthSeries: [165000, 168200, 167800, 170400, 173000, 172500, 175800, 177200, 179400, 180900, 182600, 184320],
    cashFlow: 2840,
    cashFlowDelta: -180,
    monthlyIncome: 9450,
    monthlyExpenses: 6610,
    debts: [
      { name: "Mortgage — 30yr fixed", lender: "Wells Fargo", balance: 312400, rate: 5.875, min: 2140, type: "Mortgage", risk: "low" },
      { name: "Sapphire Preferred", lender: "Chase", balance: 4820, rate: 22.49, min: 145, type: "Credit Card", risk: "high" },
      { name: "Quicksilver", lender: "Capital One", balance: 1980, rate: 19.99, min: 60, type: "Credit Card", risk: "high" },
      { name: "Auto loan — Civic", lender: "Honda Financial", balance: 12640, rate: 6.49, min: 312, type: "Auto", risk: "medium" },
      { name: "Grad school refi", lender: "SoFi", balance: 18420, rate: 4.85, min: 218, type: "Student", risk: "low" },
    ],
    savings: [
      { name: "Emergency fund", balance: 9200, target: 18000, monthly: 400, eta: "Mar 2028", category: "Safety" },
      { name: "House — kitchen reno", balance: 6800, target: 25000, monthly: 600, eta: "Aug 2029", category: "Home" },
      { name: "Vacation — Japan '26", balance: 2400, target: 5500, monthly: 350, eta: "Dec 2026", category: "Lifestyle" },
      { name: "Roth IRA '26", balance: 3850, target: 7000, monthly: 583, eta: "Dec 2026", category: "Retirement" },
    ],
    budget: [
      { cat: "Housing", spent: 2410, budget: 2400, color: "var(--info)" },
      { cat: "Groceries", spent: 612, budget: 700, color: "var(--positive)" },
      { cat: "Dining out", spent: 486, budget: 350, color: "var(--negative)" },
      { cat: "Transport", spent: 312, budget: 400, color: "var(--ink-2)" },
      { cat: "Subscriptions", spent: 184, budget: 150, color: "var(--warn)" },
      { cat: "Health", spent: 220, budget: 250, color: "var(--positive)" },
      { cat: "Shopping", spent: 540, budget: 400, color: "var(--negative)" },
      { cat: "Travel", spent: 0, budget: 200, color: "var(--ink-3)" },
    ],
    transactions: [
      { date: "May 8", merchant: "Trader Joe's", cat: "Groceries", amount: -84.20, source: "Chase Checking" },
      { date: "May 8", merchant: "Lyft", cat: "Transport", amount: -12.40, source: "Chase Checking" },
      { date: "May 7", merchant: "Direct Deposit — Acme Corp", cat: "Income", amount: 4725.00, source: "Chase Checking" },
      { date: "May 6", merchant: "Spotify", cat: "Subscriptions", amount: -16.99, source: "Capital One" },
      { date: "May 6", merchant: "Whole Foods", cat: "Groceries", amount: -52.10, source: "Chase Checking" },
      { date: "May 5", merchant: "Shell", cat: "Transport", amount: -48.00, source: "Capital One" },
      { date: "May 5", merchant: "Bartaco", cat: "Dining out", amount: -68.30, source: "Chase Sapphire" },
      { date: "May 4", merchant: "Mortgage — Wells Fargo", cat: "Housing", amount: -2410.00, source: "Chase Checking" },
    ],
    documents: [
      { name: "chase_checking_apr2026.csv", size: "84 KB", added: "May 8", status: "ready", rows: 142, source: "Chase" },
      { name: "capital_one_apr2026.pdf", size: "240 KB", added: "May 8", status: "ready", rows: 41, source: "Capital One" },
      { name: "wells_mortgage_q1.pdf", size: "1.2 MB", added: "May 7", status: "ready", rows: 3, source: "Wells Fargo" },
      { name: "sofi_student_loan_apr.pdf", size: "180 KB", added: "May 7", status: "embedding", rows: 1, source: "SoFi" },
      { name: "honda_auto_loan.csv", size: "12 KB", added: "May 6", status: "ready", rows: 24, source: "Honda Financial" },
      { name: "schwab_brokerage_q1.pdf", size: "640 KB", added: "May 4", status: "ready", rows: 18, source: "Schwab" },
    ],
  },
};

/* Routing demo — supervisor decides which agents handle a query */
export const AGENT_META = {
  supervisor: { label: "Supervisor", color: "var(--agent-supervisor)" },
  debt: { label: "Debt Analyzer", color: "var(--agent-debt)" },
  savings: { label: "Savings Strategy", color: "var(--agent-savings)" },
  budget: { label: "Budget Advisor", color: "var(--agent-budget)" },
  payoff: { label: "Payoff Optimizer", color: "var(--agent-payoff)" },
};

/* Pre-canned chat for the prototype */
export const CHAT_SEED = [
  {
    role: "user",
    text: "I just got a $3,200 bonus. What should I do with it?",
  },
  {
    role: "supervisor",
    routing: ["debt", "savings", "payoff"],
    text: "Routing to Debt Analyzer, Payoff Optimizer, and Savings Strategy.",
  },
  {
    role: "agent",
    agent: "payoff",
    text:
      "Pay $3,200 toward the **Sapphire Preferred** card (22.49% APR). That's the highest-rate balance you carry and the avalanche move saves you about **$612 in interest** over the next 18 months versus splitting the bonus.",
    structured: {
      kind: "recommend-payoff",
      target: "Sapphire Preferred",
      amount: 3200,
      interestSaved: 612,
    },
    trace: {
      totalMs: 1820, toolCount: 6,
      steps: [
        { kind: "supervisor", title: "Decomposed into 3 sub-questions", ms: 380,
          details: [
            "Which debt yields the highest guaranteed return?",
            "Is the emergency fund adequate for full payoff?",
            "What's the long-run interest delta?",
          ],
          routes: ["debt", "savings", "payoff"] },
        { kind: "agent", agent: "debt", ms: 540,
          tools: [
            { name: "query_debt_table", args: 'filter: "active", sort: "apr desc"', result: "3 rows" },
            { name: "compute_apr_weighted_risk", args: "debts", result: "22.49% top APR" },
          ],
          conclusion: "Sapphire Preferred is the highest-yield payoff target." },
        { kind: "agent", agent: "payoff", ms: 620,
          tools: [
            { name: "rag_retrieve", args: '"chase sapphire statement", k=5', result: "rows 12, 47, 89, 104, 211" },
            { name: "simulate_avalanche", args: "extra: $3,200, horizon: 18mo", result: "−$612 interest" },
          ],
          conclusion: "Avalanche move saves $612 vs split." },
        { kind: "agent", agent: "savings", ms: 280,
          tools: [
            { name: "query_savings_goals", args: 'filter: "emergency"', result: "1 row · 51% of target" },
          ],
          conclusion: "Emergency fund at 51% — flag for synthesis." },
        { kind: "synth", ms: 180,
          summary: "Merged 3 agent outputs · prioritized by certainty · flagged emergency-fund tradeoff for follow-up" },
      ],
    },
  },
  {
    role: "agent",
    agent: "savings",
    text:
      "Counter-take: your **emergency fund is at 51%** of your 6-month target. If job stability is a concern, a 70/30 split (debt/emergency) keeps the avalanche logic mostly intact while strengthening your runway.",
    trace: {
      totalMs: 740, toolCount: 3,
      steps: [
        { kind: "agent", agent: "savings", ms: 540,
          tools: [
            { name: "query_savings_goals", args: 'filter: "emergency"', result: "balance: $7,200 / $14,000" },
            { name: "rag_retrieve", args: '"monthly fixed expenses 6mo"', result: "rows 4, 18, 31" },
            { name: "project_runway", args: "balance: 7200, burn: 4380/mo", result: "1.6mo runway" },
          ],
          conclusion: "Runway too thin for full payoff. Recommend 70/30 split." },
      ],
    },
  },
  {
    role: "agent",
    agent: "supervisor",
    text:
      "**Synthesis** — both are reasonable. Highest expected value is full payoff to Sapphire if your role feels stable. Tap **Apply** to schedule, or ask a follow-up.",
    actions: ["Apply payoff plan", "Split 70/30 instead", "What if I lose my job?"],
  },
];

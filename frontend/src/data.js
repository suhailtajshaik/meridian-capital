/* UI chrome only — agent display metadata. No financial data. */

/* Routing demo — supervisor decides which agents handle a query */
export const AGENT_META = {
  supervisor: { label: "Supervisor", color: "var(--agent-supervisor)" },
  debt: { label: "Debt Analyzer", color: "var(--agent-debt)" },
  savings: { label: "Savings Strategy", color: "var(--agent-savings)" },
  budget: { label: "Budget Advisor", color: "var(--agent-budget)" },
  payoff: { label: "Payoff Optimizer", color: "var(--agent-payoff)" },
};

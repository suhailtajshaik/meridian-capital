# UI copy

Canonical empty-state, help, and trust copy for every view. Write copy here
first, then reference from views — it keeps voice consistent and makes review
cheap.

**Voice rules.**

- Quietly confident. Plain English. No exclamation marks.
- Trust microcopy is direct: "stays on this device", not "completely private!".
- Help text is one paragraph. If it needs two, the view is too complicated.
- Existing reference line (keep this tone): *"Files are stored & embedded
  locally on this device."*

---

## Dashboard

**Empty state — no debts, no savings, no documents yet.**
> Welcome to Meridian. Drop a few bank exports into Documents to start. Your
> dashboard fills in as the vault indexes them.

**Help — what is this view?**
> Your full financial picture in one place: net worth, monthly cash flow, what
> each specialist agent has flagged this week, and recent activity. Numbers
> are derived from the documents you've indexed locally.

**Trust microcopy** *(near net worth pill)*
> Computed on this device.

---

## Documents

**Empty state — no documents uploaded.**
> No documents yet. Drop a CSV, OFX, or PDF statement into the box above.
> Meridian parses it, redacts personal account numbers, and indexes the rows
> into a private vector store. Nothing leaves your device.

**Help — what happens after upload?**
> Each file goes through five stages: Parse (CSV/PDF/OFX → typed rows),
> Normalize (dates, currencies, merchant cleanup), Redact (account numbers
> stripped), Embed (per-row vectors → tabular RAG store), and Index (made
> available to the advisor agents). The whole pipeline runs locally.

**Trust microcopy** *(under dropzone — keep this exact line)*
> Files are stored & embedded locally on this device.

---

## Debt Analyzer

**Empty state — no debts in vault.**
> Once you've uploaded a credit card or loan statement, the Debt Analyzer
> ranks balances by APR, projects payoff trajectories, and flags the
> highest-yield target.

**Help — what's this agent doing?**
> The Debt Analyzer ranks every active debt by interest cost and risk. It
> uses your statement data to compute the APR-weighted risk, then surfaces
> the single highest-yield payoff target alongside a balance trajectory.

**Trust microcopy**
> Pulled from your indexed statements. No bank logins involved.

---

## Savings Strategy

**Empty state — no savings goals defined.**
> Add a savings goal (Settings → Goals) or upload a brokerage statement to
> let the Savings Strategy agent project ETAs and surface emergency-fund
> coverage.

**Help — what's this agent doing?**
> Savings Strategy projects how long each goal will take at your current
> contribution rate, calls out goals that are off track, and computes
> emergency-fund coverage in months of runway. It's the agent that pushes
> back when other agents over-prioritize debt at the expense of safety.

**Trust microcopy**
> Projections use your real contributions and balances — not industry
> averages.

---

## Budget Advisor

**Empty state — no budget yet.**
> Set monthly targets per category and upload a recent month of
> transactions. Budget Advisor surfaces overspend, recurring discretionary,
> and the surplus you can redirect.

**Help — what's this agent doing?**
> Budget Advisor compares your actual spending to your category targets each
> month, finds where you're over, separates discretionary from fixed, and
> quantifies how much could be redirected to savings goals or debt paydown.

**Trust microcopy**
> Categorization is computed locally from merchant strings. You can override
> any category and the change persists in the vault.

---

## Payoff Optimizer

**Empty state — no debts indexed.**
> Upload a loan or credit-card statement first. Payoff Optimizer simulates
> snowball, avalanche, and minimum-only strategies side by side, projects
> total interest paid, and recommends the schedule that saves the most.

**Help — what's this agent doing?**
> Payoff Optimizer takes your debts and runs a deterministic month-by-month
> simulation under three strategies: Avalanche (highest APR first),
> Snowball (smallest balance first), and Minimum (status quo). It projects
> the interest delta over your chosen horizon and recommends the schedule
> that minimizes total interest paid — adjusted for any extra principal you
> can apply.

**Trust microcopy**
> Simulations are math, not vibes — pure pandas, deterministic, on-device.

---

## Advisor chat

**Empty state — fresh chat.**
> Ask anything. Try: "I just got a $3,200 bonus. What should I do with it?"
> The supervisor will route your question to the right specialists and merge
> their replies into a single recommendation.

**Help — what is this?**
> The Advisor is a multi-agent system. A supervisor decomposes your question,
> routes the parts to the specialists who can answer them (Debt, Savings,
> Budget, Payoff), and synthesizes their replies. Open "How I answered this"
> under any reply to see the full trace: every tool called, every row
> retrieved, every number computed.

**Trust microcopy**
> Your message stays on this device. So does every document the agents
> retrieve from.

---

## Settings & security

**Empty state — no documents indexed.**
> Once you've uploaded statements, you'll see them listed here with their
> indexed row counts and last-updated timestamps.

**Help — what is the vault?**
> The vault is a local sqlite + vector store on your machine. Documents,
> embeddings, derived facts, and your conversation history all live there.
> Nothing is uploaded; nothing is logged remotely.

**Trust microcopy** *(near vault status pill)*
> Local vault · on-device · no network calls.

**Security checklist (the items)**
- No bank credentials required.
- No outbound telemetry.
- No analytics, no crash reporting.
- All embeddings computed on-device.
- All agent calls run against a local model.
- You can wipe the vault with one click — and the app forgets.

---

## Reusable strings

For when a view needs a one-liner that already exists somewhere:

| Key | String |
| --- | --- |
| `local_files` | Files are stored & embedded locally on this device. |
| `local_compute` | Computed on this device. |
| `local_vault` | Local vault · on-device · no network calls. |
| `try_bonus_q` | Try: "I just got a $3,200 bonus. What should I do with it?" |
| `apply_action` | Apply |
| `alternatives_action` | Show alternatives |
| `why_action` | Why this recommendation? |

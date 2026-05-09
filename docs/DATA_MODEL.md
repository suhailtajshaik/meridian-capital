# Data model

The mocked data lives in `data.py` at the repo root. Three top-level objects:
`PERSONA`, `AGENT_META`, `CHAT_SEED` (plus `FOLLOWUP_RESPONSE`). Views read
these directly. If you extend any of them, this page is the contract.

## `PERSONA`

The mocked user. Today: Maya Patel. Every view consumes some subset.

| Field | Type | Used by | Notes |
| --- | --- | --- | --- |
| `name` | str | sidebar, dashboard | display name |
| `initials` | str | sidebar avatar | 2 chars |
| `net_worth` | int | dashboard | $ amount |
| `net_worth_delta` | int | dashboard | this month's change |
| `net_worth_series` | list[int] | dashboard | 12 trailing months for the chart |
| `cash_flow` | int | dashboard | monthly net |
| `cash_flow_delta` | int | dashboard | vs last month |
| `monthly_income` | int | dashboard, budget | $/mo |
| `monthly_expenses` | int | dashboard, budget | $/mo |
| `debts` | list[Debt] | debt, dashboard, payoff | see below |
| `savings` | list[SavingsGoal] | savings, dashboard | see below |
| `budget` | list[BudgetCategory] | budget, dashboard | see below |
| `transactions` | list[Transaction] | dashboard activity | recent feed |
| `documents` | list[Document] | documents, settings | the indexed vault |

### `Debt`

| Field | Type |
| --- | --- |
| `name` | str |
| `lender` | str |
| `balance` | int |
| `rate` | float (APR %) |
| `min` | int (min payment) |
| `type` | "Mortgage" \| "Credit Card" \| "Auto" \| "Student" |
| `risk` | "low" \| "medium" \| "high" |

### `SavingsGoal`

| Field | Type |
| --- | --- |
| `name` | str |
| `balance` | int |
| `target` | int |
| `monthly` | int |
| `eta` | str (e.g. "Mar 2028") |
| `category` | "Safety" \| "Home" \| "Lifestyle" \| "Retirement" |

### `BudgetCategory`

| Field | Type |
| --- | --- |
| `cat` | str (Housing, Groceries, Dining out, Transport, Subscriptions, Health, Shopping, Travel) |
| `spent` | int |
| `budget` | int |

### `Transaction`

| Field | Type |
| --- | --- |
| `date` | str ("May 8") |
| `merchant` | str |
| `cat` | str (matches a `BudgetCategory.cat`) |
| `amount` | float (negative = outflow) |
| `source` | str ("Chase Checking", "Capital One", "Chase Sapphire") |

### `Document`

| Field | Type |
| --- | --- |
| `name` | str (filename) |
| `size` | str ("84 KB") |
| `added` | str ("May 8") |
| `status` | "ready" \| "embedding" \| "parsing" |
| `rows` | int |
| `source` | str |

The persona's `documents` list **must reconcile with the files in
`sample_data/`** — the seed CSVs were produced to match these row counts and
sources.

## `AGENT_META`

Map of `agent_id → {label, color}`. Used to label agent messages in the chat
view and to color the per-agent dots in the sidebar.

| `agent_id` | `label` | hex color |
| --- | --- | --- |
| `supervisor` | Supervisor | `#4A3B6B` |
| `debt` | Debt Analyzer | `#9E3A37` |
| `savings` | Savings Strategy | `#1E6B52` |
| `budget` | Budget Advisor | `#B27A1E` |
| `payoff` | Payoff Optimizer | `#2C4F7C` |

> **Plotly note.** These colors are 6-char hex. When using them as fills or
> grid lines in Plotly, **convert to `rgba()` first** — Plotly chokes on
> 8-char hex (`#RRGGBBAA`).

## `CHAT_SEED` (and `FOLLOWUP_RESPONSE`)

A list of `Message` dicts used to seed the advisor chat with the bonus-scenario
demo. `FOLLOWUP_RESPONSE` is appended when the user types a follow-up; it's
the budget+savings counter-scenario.

### `Message`

| Field | Type | When present |
| --- | --- | --- |
| `role` | "user" \| "supervisor" \| "agent" | always |
| `agent` | str | when `role == "agent"` |
| `text` | str | always (markdown) |
| `routing` | list[str] | when supervisor announces a fan-out |
| `trace` | `Trace` | optional — drives the "How I answered this" expander |
| `structured` | dict | optional — chat view renders a card if `kind` matches |
| `actions` | list[str] | optional — supervisor-final action buttons |

### `Trace`

See [`AGENTS.md`](AGENTS.md#trace-schema) for the full schema. In short:
`{total_ms, tool_count, steps: [SupervisorStep | AgentStep | SynthStep]}`.

## How to add a new persona

The view code reads `persona` keys directly with no nullable fallbacks. To add
a new persona without breaking views, you must populate **every** field above.

1. Copy the existing `PERSONA` dict in `data.py` and rename it.
2. Update top-level numbers (net worth, cash flow, income/expenses).
3. Replace `debts`, `savings`, `budget`, `transactions`, `documents` lists.
4. Make sure `monthly_income - monthly_expenses ≈ cash_flow` so the dashboard
   doesn't look incoherent.
5. If you change `documents`, also update or replace the files in
   `sample_data/` so the demo upload still reconciles.
6. Update `streamlit_app.py` to import the new persona (or add a switcher).

The chat seed (`CHAT_SEED`) references specific persona facts (Sapphire
Preferred at 22.49%, $3,200 bonus saving $612). If you change those numbers
in the persona, update `CHAT_SEED` to match — otherwise the trace will lie
about the user's actual data.

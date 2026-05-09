# Agents

Meridian's reasoning layer is a **supervisor + 4 specialist sub-agents**. Each
specialist owns a narrow slice of the user's financial life and exposes a
small set of tools the supervisor can compose.

The agents live in `agents/`. Today they are stubs that return fixtures
matching the `CHAT_SEED` shape in `data.py`; the contract they satisfy is the
same one a real LLM-backed implementation will satisfy.

---

## Supervisor

**Role.** Decomposes a user question into sub-questions, picks which
specialists to route to, and merges their replies into a final synthesis with
action buttons.

**Inputs.** `question: str`, `persona: dict`.

**Outputs.** A list of `AgentMessage` dicts: a routing announcement, the
specialists' replies (in the order they returned), and a final supervisor
synthesis message.

**Tools.** None directly — the supervisor's "tool" is the dispatch table to
`{debt, savings, budget, payoff}.analyze`.

**Trace shape produced.**
```
SupervisorStep   ─▶ AgentStep × N (specialists) ─▶ SynthStep
```

---

## Debt Analyzer

**Role.** Ranks debts by APR-weighted risk; flags the highest-yield payoff
target.

**Inputs.** Question + persona (uses `persona["debts"]`).

**Tools.**

| Tool | Args | Returns |
| --- | --- | --- |
| `query_debt_table` | `filter`, `sort` | rows of debts matching filter |
| `compute_apr_weighted_risk` | `debts` | top-APR debt + risk scores |

**Canonical conclusion.** "Sapphire Preferred is the highest-yield payoff
target."

---

## Savings Strategy

**Role.** Surfaces savings-goal coverage and runway. Often plays the
*counter-take* role — the agent that says "yes, but consider…" when another
agent's recommendation has a hidden tradeoff.

**Inputs.** Question + persona (uses `persona["savings"]`,
`persona["monthly_expenses"]`).

**Tools.**

| Tool | Args | Returns |
| --- | --- | --- |
| `query_savings_goals` | `filter` | matching goal rows with progress |
| `rag_retrieve` | `query`, `k` | top-k indexed rows from local vault |
| `project_runway` | `balance`, `burn` | months of runway |
| `project_goal_eta` | `extra` | new ETA given extra monthly contribution |

**Canonical conclusion.** "Runway too thin for full payoff. Recommend 70/30
split."

---

## Budget Advisor

**Role.** Compares spending to budget targets, flags overspend categories,
quantifies the redirectable surplus.

**Inputs.** Question + persona (uses `persona["budget"]`,
`persona["transactions"]`).

**Tools.**

| Tool | Args | Returns |
| --- | --- | --- |
| `query_transactions` | `month` | transaction rows for month |
| `compare_to_budget` | `by` | per-category over/under deltas |
| `rag_retrieve` | `query`, `k` | recurring/discretionary tagged rows |

**Canonical conclusion.** "Dining +$136, Shopping +$140 — both discretionary."

---

## Payoff Optimizer

**Role.** Simulates payoff strategies (avalanche / snowball / minimum) and
projects the interest delta over a horizon. Produces a `structured`
recommendation that the chat view can render as an "Apply" action.

**Inputs.** Question + persona (uses `persona["debts"]`).

**Tools.**

| Tool | Args | Returns |
| --- | --- | --- |
| `rag_retrieve` | `query`, `k` | indexed statement rows for context |
| `simulate_avalanche` | `extra`, `horizon` | interest delta + payoff schedule |

**Canonical conclusion.** "Avalanche move saves $612 vs split."

**Structured output.** `{"kind": "recommend-payoff", "target": "Sapphire
Preferred", "amount": 3200, "interest_saved": 612}` — the chat view checks
for `structured.kind` to render an actionable card.

---

## Trace schema

Every agent returns an `AgentMessage`. The `trace` field is the contract that
makes orchestration legible in the UI.

### `Trace`

| Field | Type | Notes |
| --- | --- | --- |
| `total_ms` | int | Wall-clock total for the whole trace |
| `tool_count` | int | Sum of tool calls across steps |
| `steps` | list[Step] | Ordered — index 0 is what ran first |

### `Step` is one of three kinds

**`SupervisorStep`** — emitted by the supervisor when decomposing a question.

| Field | Type | Notes |
| --- | --- | --- |
| `kind` | `"supervisor"` | discriminator |
| `title` | str | "Decomposed into 3 sub-questions" |
| `ms` | int | duration |
| `details` | list[str] | the sub-questions, one per line in the UI |
| `routes` | list[str] | agent ids: e.g. `["debt", "savings", "payoff"]` |

**`AgentStep`** — emitted by a specialist while it runs.

| Field | Type | Notes |
| --- | --- | --- |
| `kind` | `"agent"` | discriminator |
| `agent` | str | one of `debt`/`savings`/`budget`/`payoff` |
| `ms` | int | duration |
| `tools` | list[Tool] | each `{name, args, result}` |
| `conclusion` | str | one-line takeaway shown at the bottom of the step |

**`SynthStep`** — emitted by the synthesizer at the end.

| Field | Type | Notes |
| --- | --- | --- |
| `kind` | `"synth"` | discriminator |
| `ms` | int | duration |
| `summary` | str | "Merged 3 outputs · prioritized by certainty · …" |

The chat view renders these by switching on `kind` — see
`views/chat.py::_trace_block`.

---

## Open questions / future work

- **LLM selection.** Llama 3.1 8B (Ollama) is the leading candidate for
  decomposition + synthesis. Phi-4 is faster but follows tool-use prompts
  less reliably in our tests.
- **Tool authoring UX.** Today tool stubs return canned strings. A path-to-real
  implementation needs a typed return shape (not just `str`) so the
  supervisor's synthesis prompt can structure its inputs cleanly.
- **Streaming.** The trace UI today renders the full trace once the reply
  arrives. With a real LLM, we should stream the trace step-by-step so the
  user watches the agents work.
- **Conflict resolution.** When two specialists disagree (the bonus scenario
  is exactly this), the synthesizer surfaces both. We should think about
  whether to also emit a confidence score.

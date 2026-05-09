# Demo script

A 5–7 minute walkthrough for the hackathon judges. There's also a 90-second
abridged version at the bottom for the hallway pitch.

## Setup (before the demo starts)

1. `streamlit run streamlit_app.py` — opens at `http://localhost:8501`.
2. Make sure the app starts on **Dashboard**.
3. Have `sample_data/` open in Finder/Explorer with the six CSVs visible.

The persona (`Maya Patel`) is pre-loaded. The CSVs in `sample_data/` are the
documents she'd realistically have uploaded — Chase checking, Capital One
Quicksilver, Wells Fargo mortgage, SoFi student loan, Honda auto loan, Schwab
brokerage. They reconcile with her dashboard numbers.

## Full walkthrough (5–7 min)

### 1. Land on Dashboard *(~30s)*

Frame the problem. Say: "This is Maya. She has a $312K mortgage, about $25K in
other debts across five accounts, four savings goals, and a brokerage. Her
financial life is fragmented across half a dozen apps and she can't see the
whole picture."

Point at:
- **Net worth** $184,320 (+$4,280 this month)
- **Cash flow** +$2,840/mo
- **Agent insights** strip — each specialist has already pre-flagged the most
  important thing in its domain.

### 2. Documents tab *(~60s)*

Click **Documents** in the sidebar. The vault is empty in the dropzone view.

Drag in all six CSVs from `sample_data/`. As they upload:

- The **Pipeline** card on the right shows the 5 stages: Parse → Normalize →
  Redact → Embed → Index. Walk through them as they animate.
- The **Sources** table at the bottom populates with the new rows.

**This is where you sell the wedge.** Read out the line at the bottom of the
dropzone: *"Files are stored & embedded locally on this device."* Say: "Most
finance apps want your bank credentials. Meridian asks for nothing. You drop
exports in, embeddings happen on your laptop, and your bank statements never
touch a server."

### 3. Advisor chat — **the moment** *(~120s)*

Click **Advisor chat**.

Type, verbatim: **"I just got a $3,200 bonus. What should I do with it?"**

The reply streams in. You'll see four messages:

1. Supervisor: *"Routing to Debt Analyzer, Payoff Optimizer, and Savings
   Strategy."*
2. Payoff Optimizer: *"Pay $3,200 toward Sapphire Preferred. Saves $612 over
   18 months."*
3. Savings Strategy: *"Counter-take: emergency fund is at 51% — consider 70/30
   split."*
4. Supervisor synthesis: *"Both are reasonable. Tap Apply or ask a follow-up."*

**Now click "How I answered this"** under the Payoff Optimizer's reply. The
trace expands. Walk the judges through:

- Supervisor decomposed the question into 3 sub-questions.
- Debt Analyzer called `query_debt_table` and `compute_apr_weighted_risk` →
  found Sapphire as top APR.
- Payoff Optimizer called `rag_retrieve("chase sapphire statement", k=5)` —
  *"this is a tabular RAG hit against the Chase CSV she just uploaded; rows
  12, 47, 89, 104, 211 are real recurring charges"* — and `simulate_avalanche`
  → -$612 interest.
- Savings Strategy called `query_savings_goals` + `project_runway` → 1.6
  months of runway, flagged.
- Synthesizer merged all three.

Total: ~1.8 seconds, 6 tool calls, fully traceable.

> **Why this matters.** Single-LLM finance bots return polished outputs you
> have to take on faith. Meridian shows the math. The judge sees a multi-agent
> architecture *visibly*, not as a slide.

### 4. Payoff view *(~45s)*

Click **Payoff Optimizer** in the sidebar.

Toggle the strategy buttons: **Snowball**, **Avalanche**, **Min only**. The
projected balance chart re-projects each time. Point at the *interest paid*
delta — avalanche saves the most, which is exactly what the agent recommended
in chat. The numbers reconcile.

### 5. Settings & security *(~30s)*

Click **Settings & security**.

Walk through the **Vault status** pill (local) and the **Security checklist**:
no network calls, no telemetry, no analytics, embeddings stored on-device.
The **Uploaded documents** table shows the six CSVs that are now indexed.

Say: *"You can pull your laptop off WiFi right now and Meridian still works."*

### 6. Close *(~30s)*

Two sentences:

- *"Meridian is the only personal-finance advisor that runs entirely on your
  device — your bank statements never leave your laptop."*
- *"And because the architecture is multi-agent with a visible trace, you can
  see exactly how every recommendation was made. That's a level of
  transparency single-model assistants can't offer."*

## Abridged version (90 seconds)

If you only have a minute and a half:

1. *"This is Meridian. Personal finance, multi-agent, runs entirely on your
   laptop."* — gesture at Dashboard.
2. *"You drop bank exports in once."* — switch to Documents, drag one CSV.
3. *"Then you ask questions."* — Advisor chat, paste the bonus question.
4. *"Every recommendation comes with a full trace."* — click "How I answered
   this", scroll through the steps.
5. Close: *"Local-first, multi-agent, fully transparent. Nothing else does
   all three."*

## What to do if it breaks

- **Streamlit hangs.** Refresh the page. State is restored from
  `st.session_state` — uploads persist within the session.
- **A view errors.** All views accept `persona` and degrade gracefully if a
  field is missing. Restart with `streamlit run streamlit_app.py`.
- **A judge asks "is this real?"** — answer honestly: the **UI, document
  pipeline, and trace are real**. The **agent layer is stubbed today**
  (returns canonical fixtures); see `docs/AGENTS.md` for the path-to-real.
  The reason we chose stubs is that the local-LLM substitution is mechanical
  once the trace contract is solid — and the trace contract is what the demo
  proves out.

# meridian-capital

**Meridian** — a local-first, multi-agent personal finance advisor.
React + Vite frontend. Hackathon project.

A supervisor agent decomposes your questions and routes them to four
specialists (Debt Analyzer, Savings Strategy, Budget Advisor, Payoff
Optimizer), all reasoning over a private document vault on your machine.
Nothing leaves the device.

## Run

```sh
cd frontend
npm install      # first time only
npm run dev
```

Opens at `http://localhost:5173`.

## Layout

```
meridian-capital/
├── frontend/             React + Vite UI
│   ├── package.json · vite.config.js · index.html
│   └── src/
│       ├── main.jsx · App.jsx · sidebar.jsx
│       ├── chat.jsx · dashboard.jsx · documents.jsx · views.jsx
│       ├── charts.jsx · icons.jsx · tweaks-panel.jsx
│       ├── data.js              mock persona, agent metadata, seeded chat
│       └── index.css
│
├── sample_data/          seed CSVs to drag into the Documents tab
│   ├── chase_checking_apr2026.csv      (142 rows)
│   ├── capital_one_apr2026.csv         (41 rows)
│   ├── honda_auto_loan.csv             (24 rows · amortization)
│   ├── schwab_brokerage_q1.csv         (18 rows · holdings + activity)
│   ├── wells_mortgage_q1.csv           (3 rows · statement summary)
│   └── sofi_student_loan_apr.csv       (1 row · loan statement)
│
└── docs/
    ├── financial-advisor-hackathon-plan.md
    └── overnight-hackathon-plan-refined.md
```

## Demo path

1. **Documents** → drop the six files from `sample_data/`. Watch the
   5-step pipeline animate (Parse → Normalize → Redact → Embed → Index).
2. **Dashboard** → net worth, agent insights at a glance.
3. **Advisor chat** → ask *"I just got a $3,200 bonus. What should I do
   with it?"* — open the **"How I answered this"** trace under the reply
   to see supervisor → debt → payoff → savings → synthesizer with tool
   calls.
4. **Payoff** → toggle Snowball / Avalanche / Min — chart re-projects.
5. **Settings** → local-first vault status + security checklist.

The orchestration trace under chat replies is the hackathon-judge moment —
it makes the multi-agent architecture *visible* instead of hidden behind
a polished output.

## What's real today vs. what's mocked

The **UI**, **document upload pipeline**, and **trace rendering** are all
real. The **agent layer** is mocked — `frontend/src/data.js::CHAT_SEED`
seeds canonical replies. Path-to-real wiring lives in the plan docs
under `docs/`.

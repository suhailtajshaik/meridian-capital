# Meridian — Streamlit demo

Multi-agent personal finance advisor. Streamlit port of the
[Claude Design](https://claude.ai/design) HTML/React prototype.

**Architecture:** supervisor + 4 sub-agents (Debt Analyzer, Savings
Strategy, Budget Advisor, Payoff Optimizer) over a local-first document
vault with tabular RAG.

## Run

```sh
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Opens on http://localhost:8501.

## Layout

```
streamlit_app.py    main shell — sidebar nav, view router
theme.py            color tokens + CSS injection (Geist + Newsreader)
data.py             mock persona, agent metadata, seeded chat trace
views/
  dashboard.py      hero stats, net-worth chart, agent insights, activity
  documents.py      upload, ingestion pipeline, "what happens next", sources
  debt.py           balance trajectory, interest mix, all debts table
  savings.py        growth chart, surplus allocation, goal cards
  budget.py         category bars vs targets, spending trend, top leak
  payoff.py         snowball/avalanche/min comparison, projected balances
  settings.py       vault status, security checklist, uploaded documents
  chat.py           advisor chat with orchestration trace
```

## Demo path

1. **Documents** → drop a CSV/PDF; see the pipeline animate
2. **Dashboard** → net worth, agent insights at a glance
3. **Advisor chat** → ask "I just got a $3,200 bonus" — open the
   "How I answered this" trace under the reply to see supervisor →
   debt → payoff → savings → synthesizer with tool calls
4. **Payoff** → toggle Snowball/Avalanche/Min only; chart re-projects
5. **Settings** → local-first vault status and security checklist

The orchestration trace under chat replies is the key hackathon-judge
moment — it makes the multi-agent architecture visible instead of
hidden behind a polished output.

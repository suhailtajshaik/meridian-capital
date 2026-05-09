# Architecture

Meridian (`meridian-capital`) is a **local-first, multi-agent personal finance
advisor**. The user drops bank exports into a private vault on their machine; a
supervisor agent decomposes their questions and routes to four specialist
sub-agents that retrieve from the vault and reason over the user's actual
numbers — never the cloud's.

## High-level flow

```
                       ┌────────────────────────┐
   user question  ───▶ │      Supervisor        │  decompose · route · synthesize
                       └─────────┬──────────────┘
                                 │ fan-out
              ┌──────────────────┼──────────────────┬──────────────────┐
              ▼                  ▼                  ▼                  ▼
        ┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐
        │   Debt   │       │ Savings  │       │  Budget  │       │  Payoff  │
        │ Analyzer │       │ Strategy │       │ Advisor  │       │Optimizer │
        └────┬─────┘       └────┬─────┘       └────┬─────┘       └────┬─────┘
             │ tools            │ tools            │ tools            │ tools
             ▼                  ▼                  ▼                  ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │   Local document vault  ·  tabular RAG  ·  numeric simulators   │
        │   (CSVs · PDFs · OFX → per-row vector index, all on-device)     │
        └─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                         ┌────────────────┐
                         │  Synthesizer   │   merge · rank · flag tradeoffs
                         └───────┬────────┘
                                 ▼
                         user-facing reply  +  expandable orchestration trace
```

## The local-first constraint

Nothing leaves the user's machine. Documents, embeddings, agent reasoning,
and tool calls all run on-device. This is a hard product constraint, not a
nice-to-have.

Why it matters:

- **Privacy.** Bank statements are among the most sensitive documents a person
  owns. Sending them to a SaaS analytics product is a non-starter for many
  users (and increasingly, their employers).
- **Regulatory.** Local execution sidesteps a substantial fraction of the
  consumer-financial-data compliance surface.
- **Demo credibility.** Claims of privacy from cloud-hosted finance apps are
  hard to verify. "Your laptop's network is unplugged and the app still works"
  is a credible demonstration.

## Tabular RAG over bank exports

Most RAG systems chunk documents into ~512-token passages. That's the wrong
unit for finance Q&A — a single transaction row is the atom of retrieval.
Meridian indexes **one vector per row** of every bank export ingested:

| Standard RAG | Meridian's tabular RAG |
| --- | --- |
| Chunk = paragraph | Chunk = transaction row |
| "What does this PDF say?" | "Which Sapphire transactions are recurring?" |
| Returns prose snippets | Returns typed rows the agent can compute on |
| Lossy for tables | Lossless — the row is the source |

Sub-agents combine `rag_retrieve` (finds relevant rows) with deterministic
numeric tools (`simulate_avalanche`, `project_runway`) so recommendations are
*backed by the user's actual data*, not a model's recollection.

## The orchestration trace

Under every advisor reply there is a "How I answered this" expander. It shows
the supervisor's decomposition, each sub-agent's tool calls (name, args,
result), and the synthesizer's merge — all rendered from the same `Trace`
schema documented in [`DATA_MODEL.md`](DATA_MODEL.md).

This is the demo's anchor moment. It makes a multi-agent architecture
*legible* — the user (and the hackathon judge) can see *how* the
recommendation was constructed, not just trust the polished final answer.

## Tech stack

| Layer | Today | Path-to-real |
| --- | --- | --- |
| UI | Streamlit + Plotly | unchanged |
| Theming | Custom CSS (Geist + Newsreader) in `theme.py` | unchanged |
| State | `st.session_state` + mocked `PERSONA` | sqlite + parquet for derived facts |
| Agent layer | Stubs in `agents/` returning fixtures from `CHAT_SEED` | local LLM (Ollama: Llama 3.1 8B / Phi-4) |
| Embeddings | (none yet) | `sentence-transformers/all-MiniLM-L6-v2` on-device |
| Vector store | (none yet) | `chromadb` or FAISS, persisted to disk |
| Numeric tools | Stubs in `agents/tools.py` returning canned strings | pure Python — pandas + numpy |

## What's mocked vs. real (today)

**Real:** the UI, the views, the Plotly charts, the document upload pipeline
(files are accepted and listed), the orchestration trace rendering, and the
sample CSVs in `sample_data/` (which reconcile with the persona).

**Mocked:** the agent layer (returns canonical fixtures from
`data.py::CHAT_SEED`), the embeddings/vector store (the "Embed" pipeline step
is theatrical), and the LLM. The mocks live behind the same interfaces that
real implementations will satisfy — see `agents/types.py` and
[`AGENTS.md`](AGENTS.md).

## Path to a real implementation

1. **Wire `agents/supervisor.run()` into `views/chat.py`** — replace the
   `CHAT_SEED` fixture with a call to `supervisor.run(question, persona)`.
   Trace shape is identical; no view changes needed.
2. **Plug in a local LLM** behind a single `agents/llm.py` module. Start with
   Ollama + Llama 3.1 8B; the supervisor's decomposition and synthesis are
   the only LLM-dependent steps.
3. **Replace `tools.rag_retrieve`** with chromadb over indexed CSV rows.
   Embeddings are computed at upload time inside the existing pipeline view.
4. **Replace numeric tool stubs** (`simulate_avalanche`, `project_runway`,
   etc.) with pure-Python implementations using pandas. These don't need an
   LLM and should be deterministic.
5. **Persist vault state** to `~/.meridian/vault.sqlite` so the demo survives
   a restart.

Each step is independently shippable. The chat view never needs to change.

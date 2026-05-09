# Meridian — Personal Finance Advisor (UI)

Vite + React export of the design prototype.

## Run

```bash
npm install
npm run dev
```

Then open http://localhost:5173

## Build

```bash
npm run build
npm run preview
```

## Project structure

- `src/main.jsx` — entry, mounts <App/>
- `src/App.jsx` — app shell, sidebar nav, chat panel, tweaks
- `src/data.js` — sample persona data, agent metadata, seeded chat
- `src/icons.jsx` — inline stroke icons
- `src/charts.jsx` — sparkline, donut, bars, etc.
- `src/sidebar.jsx` — left nav
- `src/chat.jsx` — advisor chat panel + orchestration trace
- `src/dashboard.jsx` — main dashboard view
- `src/documents.jsx` — ingestion view
- `src/views.jsx` — Debt / Savings / Budget / Payoff / Settings views
- `src/tweaks-panel.jsx` — design-time tweaks panel (theme, density, etc.)
- `src/index.css` — design tokens + global styles

## Notes

- The Tweaks panel uses a host postMessage protocol for persistence in the original prototype; in standalone Vite it just updates local state.
- Sample data is in `src/data.js` — replace `PERSONAS.midcareer` with real ingested data wired to your backend.
- The orchestration trace UI is fed by the `trace` field on each chat message; replace the seeded `CHAT_SEED` with real agent traces from your supervisor.

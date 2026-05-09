# assets/

Drop static assets here:

- `logo.svg` / `logo.png` — Meridian wordmark.
- `screenshot-dashboard.png`, `screenshot-chat-trace.png` — demo captures
  for the README and pitch deck.
- `demo.gif` — 30-second loop of the chat trace expanding.

Nothing here is loaded by the Streamlit app today; the app's branding
comes from `theme.py` (CSS) and the inline SVG mark in
`streamlit_app.py::sidebar`. This directory is for materials that live
*outside* the running app — README images, pitch slides, GIF captures
for socials.

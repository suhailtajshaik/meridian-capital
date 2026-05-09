## Meridian Backend

FastAPI multi-agent finance advisor backend. To run: navigate to `backend/`, create a virtual environment with `python3 -m venv venv && source venv/bin/activate`, install dependencies with `pip install -r requirements.txt`, copy `.env.example` to `.env` and fill in your `OPENROUTER_API_KEY`, then start the server with `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` — the API will be available at `http://127.0.0.1:8000` and the frontend (running on port 5173) is already CORS-whitelisted.

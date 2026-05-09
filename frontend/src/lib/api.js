/* API client — thin fetch wrapper for the Meridian backend at localhost:8000 */

const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

/* GET /api/health → { status, model } */
export async function getHealth(signal) {
  const res = await fetch(`${BASE}/api/health`, { signal });
  if (!res.ok) throw new Error(`health check failed: ${res.status}`);
  return res.json();
}

/**
 * streamUpload — POST /api/upload (multipart), parse SSE line-by-line, call onEvent per JSON object.
 *
 * SSE contract:
 *   data: {"type":"stage","stage":"parse|normalize|redact|index|analyze","label":"..."}
 *   data: {"type":"ingest_complete","rows","columns","table_name","raw_path","session_id"}
 *   data: {"type":"trace","event":{...}}
 *   data: {"type":"snapshot","snapshot":{...}}
 *   data: {"type":"error","stage","message"}
 *   data: {"type":"done"}
 *
 * Returns a final aggregated result {ingest, snapshot} on done.
 */
export async function streamUpload({ file, sessionId, onEvent, signal }) {
  const body = new FormData();
  body.append('file', file);
  if (sessionId) body.append('session_id', sessionId);

  const res = await fetch(`${BASE}/api/upload`, { method: 'POST', body, signal });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`upload failed: ${res.status} — ${text}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let ingest = null;
  let snapshot = null;
  let lastError = null;

  const handle = (event) => {
    if (event.type === 'ingest_complete') ingest = event;
    else if (event.type === 'snapshot') snapshot = event.snapshot;
    else if (event.type === 'error') lastError = event;
    onEvent(event);
  };

  while (true) {
    let done, value;
    try {
      ({ done, value } = await reader.read());
    } catch (err) {
      if (err.name === 'AbortError') return { ingest, snapshot };
      throw err;
    }
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('data:')) continue;
      const raw = trimmed.slice(5).trim();
      if (!raw || raw === '[DONE]') continue;
      try {
        handle(JSON.parse(raw));
      } catch { /* skip malformed */ }
    }
  }

  if (lastError) throw new Error(`${lastError.stage}: ${lastError.message}`);
  return { ingest, snapshot };
}

/* Legacy non-streaming upload — kept only for tooling that wants a single JSON response.
   Drives a no-op onEvent callback through streamUpload. */
export async function uploadFile(file, sessionId, signal) {
  const result = await streamUpload({ file, sessionId, onEvent: () => {}, signal });
  return {
    rows: result.ingest?.rows ?? 0,
    columns: result.ingest?.columns ?? [],
    table_name: result.ingest?.table_name,
    session_id: result.ingest?.session_id ?? sessionId,
    snapshot: result.snapshot,
  };
}

/* GET /api/snapshot/:session_id → Snapshot or throws on 404 */
export async function getSnapshot(sessionId, signal) {
  const res = await fetch(`${BASE}/api/snapshot/${encodeURIComponent(sessionId)}`, { signal });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`snapshot fetch failed: ${res.status}`);
  return res.json();
}

/* DELETE /api/data/:session_id → 204 */
export async function deleteData(sessionId) {
  const res = await fetch(`${BASE}/api/data/${encodeURIComponent(sessionId)}`, { method: 'DELETE' });
  if (res.status !== 204 && !res.ok) throw new Error(`delete failed: ${res.status}`);
}

/**
 * streamChat — POST /api/chat, parse SSE line-by-line, call onEvent per parsed JSON object.
 *
 * SSE contract:
 *   data: {"type":"trace","event":{...}}
 *   data: {"type":"message","message":{role,content,agent?}}
 *   data: {"type":"done"}
 *
 * Returns a promise that resolves when type:"done" is received or the stream ends.
 * Rejects on network error; AbortController signal cancels the stream cleanly.
 */
export async function streamChat({ messages, sessionId, context, onEvent, signal }) {
  const res = await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages,
      session_id: sessionId,
      ...(context != null ? { context } : {}),
    }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`chat stream failed: ${res.status} — ${text}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    let done, value;
    try {
      ({ done, value } = await reader.read());
    } catch (err) {
      // AbortError is expected when caller cancels
      if (err.name === 'AbortError') return;
      throw err;
    }

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete lines from buffer
    const lines = buffer.split('\n');
    // The last element may be a partial line — keep it in the buffer
    buffer = lines.pop();

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('data:')) continue;
      const raw = trimmed.slice(5).trim();
      if (!raw || raw === '[DONE]') continue;
      let event;
      try {
        event = JSON.parse(raw);
      } catch {
        // malformed line — skip
        continue;
      }
      onEvent(event);
      if (event.type === 'done') return;
    }
  }

  // Flush any remaining buffer content
  if (buffer.trim().startsWith('data:')) {
    const raw = buffer.trim().slice(5).trim();
    if (raw && raw !== '[DONE]') {
      try {
        onEvent(JSON.parse(raw));
      } catch { /* ignore */ }
    }
  }
}

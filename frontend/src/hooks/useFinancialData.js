import { useState, useEffect, useCallback } from 'react';
import { getSnapshot, uploadFile as apiUploadFile, deleteData } from '../lib/api.js';
import { getSessionId, clearSessionId } from '../lib/session.js';

/**
 * useFinancialData — manages snapshot + upload state.
 *
 * Returns:
 *   snapshot     — Snapshot | null
 *   loading      — boolean
 *   error        — Error | null
 *   uploadFile   — (file: File) => Promise<{ rows, columns, table_name, snapshot }>
 *   uploading    — boolean
 *   uploadError  — Error | null
 *   refresh      — () => Promise<void>  re-fetches snapshot from backend
 *   clearAll     — () => Promise<void>  DELETE /api/data/:session_id + clears local state
 */
export function useFinancialData() {
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const fetchSnapshot = useCallback(async (signal) => {
    const sessionId = getSessionId();
    setLoading(true);
    setError(null);
    try {
      const data = await getSnapshot(sessionId, signal);
      if (signal?.aborted) return;
      setSnapshot(data); // null on 404 — that's expected
    } catch (err) {
      if (err.name === 'AbortError') return;
      setError(err);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  // Fetch on mount
  useEffect(() => {
    const controller = new AbortController();
    fetchSnapshot(controller.signal);
    return () => controller.abort();
  }, [fetchSnapshot]);

  const refresh = useCallback(() => {
    const controller = new AbortController();
    return fetchSnapshot(controller.signal);
  }, [fetchSnapshot]);

  const uploadFile = useCallback(async (file) => {
    const sessionId = getSessionId();
    setUploading(true);
    setUploadError(null);
    try {
      const result = await apiUploadFile(file, sessionId);
      // Backend returns a snapshot inline with the upload response
      if (result.snapshot) {
        setSnapshot(result.snapshot);
      } else {
        // Fall back to fetching the snapshot separately
        await fetchSnapshot();
      }
      return result;
    } catch (err) {
      setUploadError(err);
      throw err;
    } finally {
      setUploading(false);
    }
  }, [fetchSnapshot]);

  const clearAll = useCallback(async () => {
    const sessionId = getSessionId();
    try {
      await deleteData(sessionId);
    } catch {
      // Best-effort — clear locally even if the backend call fails
    }
    clearSessionId();
    setSnapshot(null);
    setError(null);
  }, []);

  return { snapshot, loading, error, uploadFile, uploading, uploadError, refresh, clearAll };
}

import { useState, useEffect, useCallback, useRef } from 'react';
import { getSnapshot, uploadFile as apiUploadFile, deleteData, getSnapshotStatus } from '../lib/api.js';
import { getSessionId, clearSessionId } from '../lib/session.js';

/**
 * useFinancialData — manages snapshot + upload state.
 *
 * Returns:
 *   snapshot        — Snapshot | null
 *   loading         — boolean
 *   error           — Error | null
 *   uploadFile      — (file: File) => Promise<{ rows, columns, table_name, snapshot }>
 *   uploading       — boolean
 *   uploadError     — Error | null
 *   snapshotStatus  — "ready"|"computing"|"stale"|"none"|null
 *   refresh         — () => Promise<void>  re-fetches snapshot from backend
 *   clearAll        — () => Promise<void>  DELETE /api/data/:session_id + clears local state
 */
export function useFinancialData() {
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [snapshotStatus, setSnapshotStatus] = useState(null);

  const pollTimerRef = useRef(null);
  const pollActiveRef = useRef(false);

  const fetchSnapshot = useCallback(async (signal) => {
    const sessionId = getSessionId();
    setLoading(true);
    setError(null);
    try {
      const data = await getSnapshot(sessionId, signal);
      if (signal?.aborted) return;
      setSnapshot(data);
    } catch (err) {
      if (err.name === 'AbortError') return;
      setError(err);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchSnapshot(controller.signal);
    return () => controller.abort();
  }, [fetchSnapshot]);

  const refresh = useCallback(() => {
    const controller = new AbortController();
    return fetchSnapshot(controller.signal);
  }, [fetchSnapshot]);

  const stopPolling = useCallback(() => {
    pollActiveRef.current = false;
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const startPolling = useCallback(() => {
    if (pollActiveRef.current) return;
    pollActiveRef.current = true;
    setSnapshotStatus('computing');

    const poll = async () => {
      if (!pollActiveRef.current) return;
      const sessionId = getSessionId();
      try {
        const result = await getSnapshotStatus(sessionId);
        if (!pollActiveRef.current) return;
        if (result.status === 'ready') {
          stopPolling();
          try { await refresh(); } catch {}
          setSnapshotStatus('ready');
        } else if (result.status === 'computing') {
          setSnapshotStatus('computing');
          pollTimerRef.current = setTimeout(poll, 3000);
        } else {
          setSnapshotStatus(result.status);
          stopPolling();
        }
      } catch {
        if (pollActiveRef.current) {
          pollTimerRef.current = setTimeout(poll, 3000);
        }
      }
    };

    poll();
  }, [refresh, stopPolling]);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  const uploadFile = useCallback(async (file) => {
    const sessionId = getSessionId();
    setUploading(true);
    setUploadError(null);
    try {
      const result = await apiUploadFile(file, sessionId);
      if (result.snapshot) {
        setSnapshot(result.snapshot);
      } else {
        await fetchSnapshot();
      }
      startPolling();
      return result;
    } catch (err) {
      setUploadError(err);
      throw err;
    } finally {
      setUploading(false);
    }
  }, [fetchSnapshot, startPolling]);

  const clearAll = useCallback(async () => {
    const sessionId = getSessionId();
    stopPolling();
    try {
      await deleteData(sessionId);
    } catch {
      // Best-effort — clear locally even if the backend call fails
    }
    clearSessionId();
    setSnapshot(null);
    setError(null);
    setSnapshotStatus(null);
  }, [stopPolling]);

  return { snapshot, loading, error, uploadFile, uploading, uploadError, snapshotStatus, startPolling, refresh, clearAll };
}

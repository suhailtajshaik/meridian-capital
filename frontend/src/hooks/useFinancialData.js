import { useState, useEffect, useCallback, useRef } from 'react';
import { getSnapshot, uploadFile as apiUploadFile, deleteData, getSnapshotStatus } from '../lib/api.js';
import { getSessionId, clearSessionId } from '../lib/session.js';

export function useFinancialData() {
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [snapshotStatus, setSnapshotStatus] = useState(null);

  const pollTimerRef = useRef(null);
  const pollActiveRef = useRef(false);

  // Returns the fetched data so callers can know if they got real data.
  // Only updates snapshot state when data is non-null — never wipes existing
  // snapshot due to a transient 404 during a polling race.
  const fetchSnapshot = useCallback(async (signal) => {
    const sessionId = getSessionId();
    setLoading(true);
    setError(null);
    try {
      const data = await getSnapshot(sessionId, signal);
      if (signal?.aborted) return null;
      if (data != null) setSnapshot(data);
      return data;
    } catch (err) {
      if (err.name === 'AbortError') return null;
      setError(err);
      return null;
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  // Initial mount: always run; if 404 the snapshot stays null (correct for fresh session)
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

    let noneRetries = 0;

    const poll = async () => {
      if (!pollActiveRef.current) return;
      const sessionId = getSessionId();
      try {
        const result = await getSnapshotStatus(sessionId);
        if (!pollActiveRef.current) return;
        if (result.status === 'ready') {
          stopPolling();
          // Retry refresh until we get real data — the REST endpoint may lag
          // slightly behind the status endpoint on the backend.
          let data = null;
          for (let attempt = 0; attempt < 5 && !data; attempt++) {
            if (attempt > 0) await new Promise(r => setTimeout(r, 1500));
            try { data = await refresh(); } catch {}
          }
          setSnapshotStatus('ready');
        } else if (result.status === 'computing') {
          noneRetries = 0;
          setSnapshotStatus('computing');
          pollTimerRef.current = setTimeout(poll, 3000);
        } else if (result.status === 'none' && noneRetries < 6) {
          // Background task may not have registered yet — retry up to ~18 s
          noneRetries++;
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

  // Called by Documents when the SSE stream delivers the snapshot event.
  // Uses inline data when available; otherwise retries the REST endpoint.
  const onSnapshotReceived = useCallback(async (eventData) => {
    stopPolling();
    if (eventData != null) {
      setSnapshot(eventData);
    } else {
      let data = null;
      for (let i = 0; i < 4 && !data; i++) {
        if (i > 0) await new Promise(r => setTimeout(r, 1500));
        try { data = await refresh(); } catch {}
      }
    }
    setSnapshotStatus('ready');
  }, [stopPolling, refresh]);

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
      // best-effort
    }
    clearSessionId();
    setSnapshot(null);
    setError(null);
    setSnapshotStatus(null);
  }, [stopPolling]);

  return { snapshot, loading, error, uploadFile, uploading, uploadError, snapshotStatus, startPolling, onSnapshotReceived, refresh, clearAll };
}

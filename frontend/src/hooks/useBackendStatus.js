import { useState, useEffect, useRef } from 'react';
import { getHealth } from '../lib/api.js';

const POLL_INTERVAL_MS = 30_000;

/**
 * Pings /api/health on mount and every 30 seconds.
 * Returns { online: boolean, model: string|null, lastChecked: Date|null }
 */
export function useBackendStatus() {
  const [state, setState] = useState({
    online: false,
    model: null,
    lastChecked: null,
  });
  const timerRef = useRef(null);

  const check = async (signal) => {
    try {
      const data = await getHealth(signal);
      if (signal?.aborted) return;
      setState({ online: true, model: data.model ?? null, lastChecked: new Date() });
    } catch (err) {
      if (err.name === 'AbortError') return;
      setState((prev) => ({ ...prev, online: false, lastChecked: new Date() }));
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    check(controller.signal);

    timerRef.current = setInterval(() => {
      const c = new AbortController();
      check(c.signal);
    }, POLL_INTERVAL_MS);

    return () => {
      controller.abort();
      clearInterval(timerRef.current);
    };
  }, []);

  return state;
}

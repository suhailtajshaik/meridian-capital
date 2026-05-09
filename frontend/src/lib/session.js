/* session.js — stable session ID stored in sessionStorage */

const SESSION_KEY = 'meridian.session_id';

/**
 * Returns the current session ID, generating a new UUID if one doesn't exist yet.
 * Uses sessionStorage so the session is scoped to the browser tab.
 */
export function getSessionId() {
  let id = sessionStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

/** Clear the session ID — forces a fresh session on next getSessionId() call. */
export function clearSessionId() {
  sessionStorage.removeItem(SESSION_KEY);
}

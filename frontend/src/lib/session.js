/* session.js — stable session ID stored in localStorage (survives tab close) */

const SESSION_KEY = 'meridian.session_id';

export function getSessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export function clearSessionId() {
  localStorage.removeItem(SESSION_KEY);
}

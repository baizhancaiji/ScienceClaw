export interface SandboxTakeoverState {
  sessionId: string;
  active: boolean;
}

const STORAGE_PREFIX = 'scienceclaw:sandbox-takeover:';
export const SANDBOX_TAKEOVER_EVENT = 'sandbox-takeover-state';

/** Global lock: only one sandbox takeover tab can exist at a time. */
const GLOBAL_TAKEOVER_KEY = 'scienceclaw:sandbox-takeover-active';

export const getSandboxTakeoverStorageKey = (sessionId: string): string => `${STORAGE_PREFIX}${sessionId}`;

export const readSandboxTakeoverState = (sessionId: string): boolean => {
  if (typeof window === 'undefined' || !sessionId) {
    return false;
  }
  return window.localStorage.getItem(getSandboxTakeoverStorageKey(sessionId)) === '1';
};

export const writeSandboxTakeoverState = (sessionId: string, active: boolean): void => {
  if (typeof window === 'undefined' || !sessionId) {
    return;
  }

  const key = getSandboxTakeoverStorageKey(sessionId);
  if (active) {
    window.localStorage.setItem(key, '1');
  } else {
    window.localStorage.removeItem(key);
  }

  window.dispatchEvent(new CustomEvent<SandboxTakeoverState>(SANDBOX_TAKEOVER_EVENT, {
    detail: { sessionId, active },
  }));
};

// ── Global takeover lock ──────────────────────────────────────────────
// Prevents two sandbox takeover tabs from coexisting. The lock stores the
// sessionId of the session that currently owns the takeover slot.

/** Returns the sessionId of the session that currently holds the global takeover lock, or null. */
export const getActiveTakeoverSession = (): string | null => {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(GLOBAL_TAKEOVER_KEY);
};

/** Acquire the global takeover lock for the given session. */
export const setActiveTakeoverSession = (sessionId: string): void => {
  if (typeof window === 'undefined' || !sessionId) return;
  window.localStorage.setItem(GLOBAL_TAKEOVER_KEY, sessionId);
};

/** Release the global takeover lock (only if it matches the given session). */
export const clearActiveTakeoverSession = (sessionId: string): void => {
  if (typeof window === 'undefined' || !sessionId) return;
  if (window.localStorage.getItem(GLOBAL_TAKEOVER_KEY) === sessionId) {
    window.localStorage.removeItem(GLOBAL_TAKEOVER_KEY);
  }
};

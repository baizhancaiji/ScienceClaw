export interface SandboxExecEntry {
  toolName: string;
  command: string;
  output?: string;
  status: string;
}

export type SandboxHistoryChannelMessage =
  | { type: 'request-snapshot'; sessionId: string }
  | { type: 'snapshot'; sessionId: string; entries: SandboxExecEntry[] }
  | { type: 'incremental'; sessionId: string; entry: SandboxExecEntry };

export const getSandboxHistoryChannelName = (sessionId: string): string => `sandbox-history:${sessionId}`;

// ── localStorage persistence ──────────────────────────────────────────
// BroadcastChannel only works while the source tab is alive and listening.
// Persisting to localStorage allows a newly opened TakeOver tab to read the
// terminal history directly, even if the original tab has been closed or its
// ActivityPanel BroadcastChannel is not yet ready.

const HISTORY_STORAGE_PREFIX = 'scienceclaw:sandbox-history:';

const getHistoryStorageKey = (sessionId: string): string => `${HISTORY_STORAGE_PREFIX}${sessionId}`;

export const persistSandboxHistory = (sessionId: string, entries: SandboxExecEntry[]): void => {
  if (typeof window === 'undefined' || !sessionId) return;
  try {
    window.localStorage.setItem(getHistoryStorageKey(sessionId), JSON.stringify(entries));
  } catch {
    // localStorage may be full or unavailable; degrade silently.
  }
};

export const readSandboxHistory = (sessionId: string): SandboxExecEntry[] => {
  if (typeof window === 'undefined' || !sessionId) return [];
  try {
    const raw = window.localStorage.getItem(getHistoryStorageKey(sessionId));
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export const clearSandboxHistory = (sessionId: string): void => {
  if (typeof window === 'undefined' || !sessionId) return;
  try {
    window.localStorage.removeItem(getHistoryStorageKey(sessionId));
  } catch {
    // ignore
  }
};

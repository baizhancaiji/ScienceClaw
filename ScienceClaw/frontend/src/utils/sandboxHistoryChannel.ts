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

import { describe, expect, it, vi } from 'vitest';

import { useSessionListUpdate } from './useSessionListUpdate';

describe('useSessionListUpdate', () => {
  it('routes title updates and partial session patches through registered callbacks', () => {
    const updater = useSessionListUpdate();
    const titleUpdate = vi.fn();
    const sessionPatch = vi.fn();

    updater.setOnSessionTitleUpdate(titleUpdate);
    updater.setOnSessionPatch(sessionPatch);
    updater.updateSessionTitle('session-1', 'New title');
    updater.patchSessionItem('session-1', { has_password: true, is_shared: false });

    expect(titleUpdate).toHaveBeenCalledWith('session-1', 'New title');
    expect(sessionPatch).toHaveBeenCalledWith('session-1', { has_password: true, is_shared: false });

    updater.setOnSessionTitleUpdate(null);
    updater.setOnSessionPatch(null);
    updater.updateSessionTitle('session-1', 'Ignored');
    updater.patchSessionItem('session-1', { has_password: false });

    expect(titleUpdate).toHaveBeenCalledTimes(1);
    expect(sessionPatch).toHaveBeenCalledTimes(1);
  });
});

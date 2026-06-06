import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('agent api', () => {
  afterEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  it('serializes getSession pagination options as query params', async () => {
    const { apiClient } = await import('./client');
    const { getSession } = await import('./agent');

    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        data: {
          session_id: 'session-1',
          title: null,
          status: 'completed',
          events: [],
          is_shared: false,
          mode: 'deep',
          model_config_id: null,
        },
      },
    });

    await getSession('session-1', {
      cursorEventId: 'evt-10',
      limit: 100,
      direction: 'before',
    });

    expect(apiClient.get).toHaveBeenCalledWith('/sessions/session-1', {
      params: {
        cursor_event_id: 'evt-10',
        limit: '100',
        direction: 'before',
      },
    });
  });
});

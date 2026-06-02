import type { AxiosRequestConfig } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const authState = vi.hoisted(() => ({
  token: null as string | null,
  refreshToken: null as string | null,
  clearStoredTokens: vi.fn(),
  storeToken: vi.fn((token: string) => {
    authState.token = token;
  }),
}));

vi.mock('@/main', () => ({
  router: {
    currentRoute: {
      value: { path: '/' },
    },
  },
}));

vi.mock('./auth', () => ({
  getStoredToken: () => authState.token,
  getStoredRefreshToken: () => authState.refreshToken,
  storeToken: authState.storeToken,
  clearStoredTokens: authState.clearStoredTokens,
}));

describe('apiClient token refresh queue', () => {
  beforeEach(() => {
    authState.token = 'expired-token';
    authState.refreshToken = 'refresh-token';
    authState.clearStoredTokens.mockClear();
    authState.storeToken.mockClear();
  });

  afterEach(() => {
    vi.resetModules();
  });

  it('queues concurrent 401 retries behind one refresh request', async () => {
    const { apiClient } = await import('./client');
    const retryAuthorizations: string[] = [];
    let refreshCalls = 0;
    let releaseRefresh: (() => void) | undefined;

    apiClient.defaults.adapter = async (config) => {
      if (config.url === '/auth/refresh') {
        refreshCalls++;
        await new Promise<void>((resolve) => {
          releaseRefresh = resolve;
        });
        return {
          data: {
            data: {
              access_token: 'new-token',
            },
          },
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
        };
      }

      const retryableConfig = config as AxiosRequestConfig & { _retry?: boolean };
      if (!retryableConfig._retry) {
        throw {
          config,
          response: {
            data: { detail: 'Unauthorized' },
            status: 401,
            statusText: 'Unauthorized',
          },
        };
      }

      retryAuthorizations.push(String(config.headers?.Authorization ?? ''));
      return {
        data: { ok: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };

    const firstRequest = apiClient.get('/protected/one');
    const secondRequest = apiClient.get('/protected/two');

    await vi.waitFor(() => {
      expect(refreshCalls).toBe(1);
      expect(releaseRefresh).toBeDefined();
    });

    releaseRefresh?.();

    await expect(Promise.all([firstRequest, secondRequest])).resolves.toHaveLength(2);
    expect(authState.storeToken).toHaveBeenCalledWith('new-token');
    expect(retryAuthorizations).toEqual(['Bearer new-token', 'Bearer new-token']);
  });
});

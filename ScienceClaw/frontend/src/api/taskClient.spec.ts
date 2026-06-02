import type { AxiosError, AxiosRequestConfig } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const authState = vi.hoisted(() => ({
  token: null as string | null,
  clearStoredTokens: vi.fn(),
}));

vi.mock('./auth', () => ({
  getStoredToken: () => authState.token,
  clearStoredTokens: authState.clearStoredTokens,
}));

describe('taskClient', () => {
  beforeEach(() => {
    authState.token = null;
    authState.clearStoredTokens.mockClear();
  });

  afterEach(() => {
    vi.resetModules();
  });

  it('uses the proxied task-service base URL by default', async () => {
    const { TASK_SERVICE_BASE_URL, isTaskServiceConfigured, taskClient } = await import('./taskClient');

    expect(TASK_SERVICE_BASE_URL).toBe('/task-service');
    expect(isTaskServiceConfigured()).toBe(true);
    expect(taskClient.defaults.baseURL).toBe('/task-service');
    expect(taskClient.defaults.timeout).toBe(30000);
  });

  it('injects stored bearer token without overwriting an explicit Authorization header', async () => {
    const { taskClient } = await import('./taskClient');
    const seenHeaders: Array<AxiosRequestConfig['headers']> = [];

    taskClient.defaults.adapter = async (config) => {
      seenHeaders.push(config.headers);
      return {
        data: { ok: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };

    authState.token = 'stored-token';
    await taskClient.get('/tasks');
    await taskClient.get('/tasks', { headers: { Authorization: 'Bearer explicit-token' } });

    expect(seenHeaders[0]?.Authorization).toBe('Bearer stored-token');
    expect(seenHeaders[1]?.Authorization).toBe('Bearer explicit-token');
  });

  it('normalizes detail/message/http errors and network errors', async () => {
    const { normalizeTaskServiceError } = await import('./taskClient');

    expect(normalizeTaskServiceError({
      response: {
        data: { detail: 'Forbidden task' },
        status: 403,
        statusText: 'Forbidden',
      },
    } as AxiosError)).toEqual({
      code: 403,
      message: 'Forbidden task',
      details: { detail: 'Forbidden task' },
    });

    expect(normalizeTaskServiceError({
      response: {
        data: { message: 'Bad webhook' },
        status: 400,
        statusText: 'Bad Request',
      },
    } as AxiosError)).toEqual({
      code: 400,
      message: 'Bad webhook',
      details: { message: 'Bad webhook' },
    });

    expect(normalizeTaskServiceError({ request: {} } as AxiosError)).toEqual({
      code: 503,
      message: 'Task service network error',
    });
  });

  it('clears local tokens and emits logout on 401 responses', async () => {
    const { taskClient } = await import('./taskClient');
    const logoutEvents: Event[] = [];
    const onLogout = (event: Event) => logoutEvents.push(event);
    window.addEventListener('auth:logout', onLogout);

    taskClient.defaults.adapter = async (config) => {
      throw {
        config,
        response: {
          data: { detail: 'Not authenticated' },
          status: 401,
          statusText: 'Unauthorized',
        },
      };
    };

    await expect(taskClient.get('/tasks')).rejects.toEqual({
      code: 401,
      message: 'Not authenticated',
      details: { detail: 'Not authenticated' },
    });

    window.removeEventListener('auth:logout', onLogout);
    expect(authState.clearStoredTokens).toHaveBeenCalledTimes(1);
    expect(logoutEvents).toHaveLength(1);
  });
});

import { describe, expect, it, vi } from 'vitest';

const apiState = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}));

vi.mock('./client', () => ({
  apiClient: apiState,
}));

vi.mock('../composables/useI18n', () => ({
  i18n: {
    global: {
      locale: { value: 'zh' },
    },
  },
}));

describe('tooluniverse API', () => {
  it('passes nested JSON arguments through and returns the raw backend payload', async () => {
    const payload = {
      success: true,
      result: {
        rows: [{ score: 1 }],
      },
    };
    apiState.post.mockResolvedValueOnce({ data: payload });

    const { runTUTool } = await import('./tooluniverse');
    const result = await runTUTool('calc', {
      text: 'alpha',
      params: { threshold: 0.5, nullable: null },
      values: [1, 'two', false, { nested: true }],
    });

    expect(apiState.post).toHaveBeenCalledWith('/tooluniverse/tools/calc/run', {
      arguments: {
        text: 'alpha',
        params: { threshold: 0.5, nullable: null },
        values: [1, 'two', false, { nested: true }],
      },
    });
    expect(result).toBe(payload);
  });

  it('keeps list response unwrapped because backend returns a raw business object', async () => {
    const payload = {
      tools: [],
      total: 0,
      categories: [],
    };
    apiState.get.mockResolvedValueOnce({ data: payload });

    const { listTUTools } = await import('./tooluniverse');
    const result = await listTUTools('search', 'chem');

    expect(apiState.get).toHaveBeenCalledWith('/tooluniverse/tools', {
      params: { lang: 'zh', search: 'search', category: 'chem' },
    });
    expect(result).toBe(payload);
  });
});

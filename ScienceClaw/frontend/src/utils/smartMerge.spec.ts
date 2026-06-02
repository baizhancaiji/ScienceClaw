import { describe, expect, it } from 'vitest';

import { smartMerge } from './smartMerge';

describe('smartMerge', () => {
  it('overwrites target fields with meaningful source values', () => {
    const target = { status: 'calling', args: { query: 'old' } };

    const result = smartMerge(target, {
      status: 'called',
      args: { query: 'new' },
      duration_ms: 120,
    });

    expect(result).toBe(target);
    expect(target).toEqual({
      status: 'called',
      args: { query: 'new' },
      duration_ms: 120,
    });
  });

  it('preserves existing fields when source values are empty placeholders', () => {
    const target = {
      args: { query: 'keep' },
      content: 'keep',
      status: 'calling',
      list: ['keep'],
    };

    smartMerge(target, {
      args: {},
      content: null,
      status: undefined,
      list: [],
      count: 0,
      enabled: false,
      label: '',
    });

    expect(target).toEqual({
      args: { query: 'keep' },
      content: 'keep',
      status: 'calling',
      list: [],
      count: 0,
      enabled: false,
      label: '',
    });
  });
});

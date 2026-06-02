import { describe, expect, it } from 'vitest';

import { findBestStepForFlush } from './planSteps';

describe('findBestStepForFlush', () => {
  it('prefers the running step', () => {
    const running = { id: 'running', status: 'running' as const };

    expect(findBestStepForFlush([
      { id: 'completed', status: 'completed' as const },
      running,
    ])).toBe(running);
  });

  it('falls back to completed and then first step', () => {
    const completed = { id: 'completed', status: 'completed' as const };
    const pending = { id: 'pending', status: 'pending' as const };

    expect(findBestStepForFlush([pending, completed])).toBe(completed);
    expect(findBestStepForFlush([pending])).toBe(pending);
  });

  it('returns undefined when there are no steps', () => {
    expect(findBestStepForFlush([])).toBeUndefined();
    expect(findBestStepForFlush(undefined)).toBeUndefined();
  });
});

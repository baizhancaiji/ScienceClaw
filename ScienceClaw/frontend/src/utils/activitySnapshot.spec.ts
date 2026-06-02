import { describe, expect, it } from 'vitest';

import { createActivitySnapshot } from './activitySnapshot';

describe('createActivitySnapshot', () => {
  it('copies the activity list and deep-clones the plan', () => {
    const items = [{
      id: 'tool-1',
      type: 'tool' as const,
      timestamp: 1,
    }];
    const plan = {
      event_id: 'plan-1',
      timestamp: 1,
      steps: [{
        event_id: 'step-event-1',
        timestamp: 1,
        id: 'step-1',
        description: 'Run tool',
        status: 'running' as const,
        tools: [],
      }],
    };

    const snapshot = createActivitySnapshot(items, plan);

    expect(snapshot.items).toEqual(items);
    expect(snapshot.items).not.toBe(items);
    expect(snapshot.plan).toEqual(plan);
    expect(snapshot.plan).not.toBe(plan);
    expect(snapshot.plan?.steps).not.toBe(plan.steps);
  });

  it('preserves an absent plan', () => {
    expect(createActivitySnapshot([], undefined)).toEqual({
      items: [],
      plan: undefined,
    });
  });
});

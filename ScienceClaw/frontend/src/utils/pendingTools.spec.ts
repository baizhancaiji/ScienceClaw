import { describe, expect, it } from 'vitest';

import { flushPendingToolsIntoStep } from './pendingTools';
import type { ActivityItem } from '../components/ActivityPanel.vue';
import type { StepEventData, ToolEventData } from '../types/event';

const createStep = (tools: StepEventData['tools'] = []): StepEventData => ({
  event_id: 'step-event-1',
  timestamp: 1,
  id: 'step-1',
  description: 'Run tools',
  status: 'running',
  tools,
});

const createToolItem = (toolCallId: string): ActivityItem => ({
  id: `tool-${toolCallId}`,
  type: 'tool',
  timestamp: 1,
  tool: {
    timestamp: 1,
    tool_call_id: toolCallId,
    name: 'search',
    status: 'called',
    function: 'search',
    args: {},
  },
});

describe('flushPendingToolsIntoStep', () => {
  it('associates pending activity tools with a step and clears the pending list', () => {
    const step = createStep();
    const toolItem = createToolItem('call-1');

    const pending = flushPendingToolsIntoStep({
      planStep: step,
      pendingToolCallIds: ['call-1'],
      activityItems: [toolItem],
    });

    expect(step.tools).toEqual([toolItem.tool]);
    expect(pending).toEqual([]);
  });

  it('does not duplicate tools already associated with the step', () => {
    const toolItem = createToolItem('call-1');
    const step = createStep([toolItem.tool as unknown as ToolEventData]);

    flushPendingToolsIntoStep({
      planStep: step,
      pendingToolCallIds: ['call-1'],
      activityItems: [toolItem],
    });

    expect(step.tools).toHaveLength(1);
  });

  it('clears unresolved pending ids without adding a tool', () => {
    const step = createStep();

    const pending = flushPendingToolsIntoStep({
      planStep: step,
      pendingToolCallIds: ['missing-call'],
      activityItems: [],
    });

    expect(step.tools).toEqual([]);
    expect(pending).toEqual([]);
  });

  it('initializes a missing tools list only when there are pending ids', () => {
    const step = createStep(undefined);
    const toolItem = createToolItem('call-1');

    flushPendingToolsIntoStep({
      planStep: step,
      pendingToolCallIds: ['call-1'],
      activityItems: [toolItem],
    });

    expect(step.tools).toEqual([toolItem.tool]);
  });
});

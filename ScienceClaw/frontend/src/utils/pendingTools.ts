import type { ActivityItem } from '../components/ActivityPanel.vue';
import type { StepEventData, ToolEventData } from '../types/event';

export interface FlushPendingToolsOptions {
  planStep: StepEventData;
  pendingToolCallIds: string[];
  activityItems: ActivityItem[];
}

export const flushPendingToolsIntoStep = ({
  planStep,
  pendingToolCallIds,
  activityItems,
}: FlushPendingToolsOptions): string[] => {
  if (pendingToolCallIds.length === 0) return pendingToolCallIds;
  if (!planStep.tools) planStep.tools = [];

  for (const toolCallId of pendingToolCallIds) {
    if (planStep.tools.some(tool => tool.tool_call_id === toolCallId)) continue;
    const activityItem = activityItems.find(
      item => item.type === 'tool' && item.tool?.tool_call_id === toolCallId,
    );
    if (activityItem?.tool) {
      planStep.tools.push(activityItem.tool as unknown as ToolEventData);
    }
  }

  return [];
};

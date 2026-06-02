import type { ActivityItem } from '../components/ActivityPanel.vue';
import type { PlanEventData } from '../types/event';

export interface ActivitySnapshot {
  items: ActivityItem[];
  plan: PlanEventData | undefined;
}

export const createActivitySnapshot = (
  items: ActivityItem[],
  plan: PlanEventData | undefined,
): ActivitySnapshot => ({
  items: [...items],
  plan: plan ? JSON.parse(JSON.stringify(plan)) as PlanEventData : undefined,
});

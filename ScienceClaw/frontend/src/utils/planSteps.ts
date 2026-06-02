import type { StepEventData } from '../types/event';

export const findBestStepForFlush = <T extends Pick<StepEventData, 'status'>>(steps: T[] | undefined): T | undefined => {
  if (!steps?.length) return undefined;
  return steps.find((step) => step.status === 'running')
    || steps.find((step) => step.status === 'completed')
    || steps[0];
};

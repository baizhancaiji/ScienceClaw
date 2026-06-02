import type { JsonObject, JsonValue } from './json';

export type ToolArgs = JsonObject | string | null;
export type ToolResultContent = unknown;

export const isToolArgsObject = (args: ToolArgs | undefined): args is JsonObject =>
  args !== null && args !== undefined && typeof args === 'object' && !Array.isArray(args);

export const getToolArgValue = (args: ToolArgs | undefined, key: string): JsonValue | undefined => {
  if (!isToolArgsObject(args)) return undefined;
  return args[key];
};

export const getToolStringArg = (args: ToolArgs | undefined, key: string): string => {
  const value = getToolArgValue(args, key);
  return typeof value === 'string' ? value : '';
};

export const stringifyToolValue = (value: JsonValue | undefined): string => {
  if (value === undefined || value === null) return '';
  if (typeof value === 'string') return value;
  return JSON.stringify(value);
};

export const getFirstToolArgPreview = (args: ToolArgs | undefined, maxLength = 80): string => {
  if (typeof args === 'string') return args.length > maxLength ? `${args.slice(0, maxLength)}...` : args;
  if (!isToolArgsObject(args)) return '';

  for (const value of Object.values(args)) {
    if (typeof value === 'string' && value.length > 0 && value.length < maxLength) {
      return value;
    }
  }

  const firstValue = Object.values(args)[0];
  const preview = stringifyToolValue(firstValue);
  return preview.length > maxLength ? `${preview.slice(0, maxLength)}...` : preview;
};

export const isToolResultObject = (content: ToolResultContent): content is Record<string, unknown> =>
  content !== null && typeof content === 'object' && !Array.isArray(content);

export const getToolResultStringField = (content: ToolResultContent, keys: string[]): string => {
  if (!isToolResultObject(content)) return '';
  for (const key of keys) {
    const value = content[key];
    if (typeof value === 'string') return value;
  }
  return '';
};

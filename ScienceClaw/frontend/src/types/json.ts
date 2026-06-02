export type JsonPrimitive = string | number | boolean | null;
export type JsonObject = { [key: string]: JsonValue };
export type JsonArray = JsonValue[];
export type JsonValue = JsonPrimitive | JsonObject | JsonArray;

export const isJsonObject = (value: JsonValue): value is JsonObject =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

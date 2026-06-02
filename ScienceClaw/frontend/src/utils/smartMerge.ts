const isEmptyPlainObject = (value: unknown): boolean =>
  value !== null && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === 0;

export const smartMerge = <T extends object, S extends object>(target: T, source: S): T => {
  const targetRecord = target as Record<string, unknown>;
  const sourceRecord = source as Record<string, unknown>;
  for (const key of Object.keys(sourceRecord)) {
    const value = sourceRecord[key];
    if (value === undefined || value === null) continue;
    if (isEmptyPlainObject(value)) continue;
    targetRecord[key] = value;
  }
  return target;
};

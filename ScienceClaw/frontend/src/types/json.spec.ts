import { describe, expect, it } from 'vitest';

import { isJsonObject, type JsonValue } from './json';

describe('JsonValue', () => {
  it('allows nested objects, arrays, primitives, and null', () => {
    const value: JsonValue = {
      text: 'alpha',
      count: 3,
      enabled: true,
      empty: null,
      nested: {
        list: ['a', 1, false, null, { child: 'ok' }],
      },
    };

    expect(value).toEqual({
      text: 'alpha',
      count: 3,
      enabled: true,
      empty: null,
      nested: {
        list: ['a', 1, false, null, { child: 'ok' }],
      },
    });
  });
});

describe('isJsonObject', () => {
  it('narrows plain JSON objects only', () => {
    expect(isJsonObject({ a: 1 })).toBe(true);
    expect(isJsonObject(['a'])).toBe(false);
    expect(isJsonObject(null)).toBe(false);
    expect(isJsonObject('a')).toBe(false);
  });
});

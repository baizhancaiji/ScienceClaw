import { describe, expect, it } from 'vitest';

import {
  getFirstToolArgPreview,
  getToolArgValue,
  getToolResultStringField,
  getToolStringArg,
  isToolArgsObject,
  isToolResultObject,
  stringifyToolValue,
  type ToolArgs,
} from './toolPayload';

describe('tool payload helpers', () => {
  it('narrows object args while preserving string and null historical payloads', () => {
    const objectArgs: ToolArgs = { file: '/tmp/a.txt', nested: { ok: true } };

    expect(isToolArgsObject(objectArgs)).toBe(true);
    expect(isToolArgsObject('{"file":"/tmp/a.txt"}')).toBe(false);
    expect(isToolArgsObject(null)).toBe(false);
  });

  it('reads JSON arg values and string fields safely', () => {
    const args: ToolArgs = {
      file: '/tmp/a.txt',
      count: 2,
      nested: { key: 'value' },
    };

    expect(getToolArgValue(args, 'count')).toBe(2);
    expect(getToolStringArg(args, 'file')).toBe('/tmp/a.txt');
    expect(getToolStringArg(args, 'count')).toBe('');
    expect(getToolStringArg('{"file":"/tmp/a.txt"}', 'file')).toBe('');
  });

  it('builds compact previews for JSON values', () => {
    expect(getFirstToolArgPreview({ query: 'science' })).toBe('science');
    expect(getFirstToolArgPreview({ nested: { id: 1 } })).toBe('{"id":1}');
    expect(getFirstToolArgPreview('raw args')).toBe('raw args');
    expect(stringifyToolValue(['a', 1, null])).toBe('["a",1,null]');
  });

  it('narrows result content before reading object fields', () => {
    expect(isToolResultObject({ stdout: 'ok' })).toBe(true);
    expect(isToolResultObject(['stdout'])).toBe(false);
    expect(getToolResultStringField({ stdout: 'ok', output: 'fallback' }, ['stdout', 'output'])).toBe('ok');
    expect(getToolResultStringField('plain text', ['stdout'])).toBe('');
  });
});

import { describe, expect, it } from 'vitest';

import { sanitizeHtml, transformSrc } from './content';

describe('transformSrc', () => {
  it('keeps external and API URLs unchanged', () => {
    expect(transformSrc('https://example.test/file.png')).toBe('https://example.test/file.png');
    expect(transformSrc('http://example.test/file.png')).toBe('http://example.test/file.png');
    expect(transformSrc('/api/v1/files/file.png')).toBe('/api/v1/files/file.png');
  });

  it('converts absolute sandbox paths to download API URLs', () => {
    expect(transformSrc('/tmp/report 1.png?cache=1')).toBe(
      `/api/v1/file/download?path=${encodeURIComponent('/tmp/report 1.png')}`,
    );
  });

  it('keeps empty and relative paths unchanged', () => {
    expect(transformSrc('')).toBe('');
    expect(transformSrc('images/file.png')).toBe('images/file.png');
  });
});

describe('sanitizeHtml', () => {
  it('removes unsafe script tags while keeping allowed custom tags', () => {
    const sanitized = sanitizeHtml(
      '<molecule-viewer src="/tmp/a.sdf"></molecule-viewer><script>alert("x")</script>',
    );

    expect(sanitized).toContain('molecule-viewer');
    expect(sanitized).toContain('src="/tmp/a.sdf"');
    expect(sanitized).not.toContain('<script>');
  });
});

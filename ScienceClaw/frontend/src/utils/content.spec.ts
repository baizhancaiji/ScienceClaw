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
      '<molecule-viewer src="/api/v1/file/download?path=a.sdf"></molecule-viewer><script>alert("x")</script>',
    );

    expect(sanitized).toContain('molecule-viewer');
    expect(sanitized).toContain('src="/api/v1/file/download?path=a.sdf"');
    expect(sanitized).not.toContain('<script>');
  });

  it('removes unsafe molecule viewer sources through the shared purifier hook', () => {
    const sanitized = sanitizeHtml('<molecule-viewer src="/tmp/a.sdf"></molecule-viewer>');

    expect(sanitized).toContain('molecule-viewer');
    expect(sanitized).not.toContain('src="/tmp/a.sdf"');
  });

  it('keeps the Mermaid toolbar data attributes and accessibility metadata', () => {
    const sanitized = sanitizeHtml(`
      <div class="mermaid-wrapper" data-mermaid-id="m1" data-mermaid-code="graph" data-mermaid-rendered="false" data-mermaid-error="false">
        <div class="mermaid-toolbar" role="toolbar" aria-label="Mermaid tools">
          <button type="button" data-mermaid-action="copy-source" title="Copy" aria-label="Copy">Copy</button>
        </div>
        <pre class="mermaid-source-panel" data-mermaid-source-panel hidden>graph TD; A--&gt;B;</pre>
      </div>
    `);

    expect(sanitized).toContain('data-mermaid-action="copy-source"');
    expect(sanitized).toContain('role="toolbar"');
    expect(sanitized).toContain('aria-label="Mermaid tools"');
    expect(sanitized).toContain('title="Copy"');
    expect(sanitized).toContain('data-mermaid-source-panel=""');
    expect(sanitized).toContain('hidden=""');
  });
});

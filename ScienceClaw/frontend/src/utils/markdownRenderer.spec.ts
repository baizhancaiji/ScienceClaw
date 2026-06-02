import { describe, expect, it } from 'vitest';

import {
  escapeCodeForCopyAttribute,
  getCodeBlockLayout,
  normalizeMarkdownCodeToken,
  renderMarkdownLink,
} from './markdownRenderer';

describe('renderMarkdownLink', () => {
  it('renders marked token links and opens external links in a new tab', () => {
    expect(renderMarkdownLink({
      href: 'https://example.com',
      title: 'Example',
      text: 'Visit',
    })).toBe('<a href="https://example.com" title="Example" target="_blank" rel="noopener noreferrer">Visit</a>');
  });

  it('renders legacy string links without external attributes for relative hrefs', () => {
    expect(renderMarkdownLink('/docs', 'Docs', 'Read')).toBe('<a href="/docs" title="Docs">Read</a>');
  });

  it('falls back to a hash href when token href is absent', () => {
    expect(renderMarkdownLink({ text: 'Missing href' })).toBe('<a href="#">Missing href</a>');
  });

  it('preserves existing unescaped text behavior', () => {
    expect(renderMarkdownLink('mailto:test@example.com', null, '<span>Email</span>')).toBe('<a href="mailto:test@example.com"><span>Email</span></a>');
  });
});

describe('normalizeMarkdownCodeToken', () => {
  it('normalizes marked token objects', () => {
    expect(normalizeMarkdownCodeToken({
      text: 'const value = 1;',
      lang: 'ts',
    })).toEqual({
      code: 'const value = 1;',
      lang: 'ts',
    });
  });

  it('falls back to raw code and plaintext language for token objects', () => {
    expect(normalizeMarkdownCodeToken({ raw: 42 })).toEqual({
      code: '42',
      lang: 'plaintext',
    });
  });

  it('normalizes legacy string code blocks', () => {
    expect(normalizeMarkdownCodeToken('echo hello', 'bash')).toEqual({
      code: 'echo hello',
      lang: 'bash',
    });
  });
});

describe('escapeCodeForCopyAttribute', () => {
  it('preserves existing HTML attribute escaping rules for copy payloads', () => {
    expect(escapeCodeForCopyAttribute('&"\'`')).toBe('&amp;&quot;&#39;&#96;');
  });
});

describe('getCodeBlockLayout', () => {
  it('returns line numbers without collapse for short blocks', () => {
    expect(getCodeBlockLayout('a\nb\nc')).toEqual({
      lineCount: 3,
      lineNumbers: '1\n2\n3',
      shouldCollapse: false,
      collapseClass: '',
    });
  });

  it('marks blocks over the collapse threshold as collapsed', () => {
    expect(getCodeBlockLayout(Array.from({ length: 21 }, (_, i) => String(i)).join('\n'))).toMatchObject({
      lineCount: 21,
      shouldCollapse: true,
      collapseClass: 'code-block-collapsed',
    });
  });
});

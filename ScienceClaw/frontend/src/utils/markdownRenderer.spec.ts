import { describe, expect, it } from 'vitest';

import { renderMarkdownLink } from './markdownRenderer';

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

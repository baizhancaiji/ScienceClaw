import { describe, expect, it } from 'vitest';

import {
  escapeCodeForCopyAttribute,
  getCodeBlockLayout,
  normalizeMarkdownCodeToken,
  postprocessMath,
  preprocessMath,
  renderHighlightedCodeBlock,
  renderKaTeX,
  renderMermaidError,
  renderMermaidPlaceholder,
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

describe('renderHighlightedCodeBlock', () => {
  it('renders the existing code block controls and line metadata', () => {
    const html = renderHighlightedCodeBlock({
      code: 'const value = "&";',
      highlightedCode: '<span>const</span> value = "&amp;";',
      lang: 'ts',
    });

    expect(html).toContain('class="code-block-wrapper " data-lines="1"');
    expect(html).toContain('<span class="code-block-lang">ts</span>');
    expect(html).toContain('<span class="code-block-line-count">1 行</span>');
    expect(html).toContain('class="code-block-fullscreen"');
    expect(html).toContain('class="code-block-copy"');
    expect(html).toContain('decodeURIComponent(`const%20value%20%3D%20%26quot%3B%26amp%3B%26quot%3B%3B`)');
    expect(html).toContain('<code class="hljs language-ts"><span>const</span> value = "&amp;";</code>');
  });

  it('renders collapse controls and expand hint for long blocks', () => {
    const highlightedCode = Array.from({ length: 21 }, (_, i) => `line ${i + 1}`).join('\n');
    const html = renderHighlightedCodeBlock({
      code: highlightedCode,
      highlightedCode,
      lang: 'plaintext',
    });

    expect(html).toContain('code-block-wrapper code-block-collapsed');
    expect(html).toContain('class="code-block-expand"');
    expect(html).toContain('点击展开全部 21 行代码');
  });
});

describe('renderMermaidPlaceholder', () => {
  it('renders the existing mermaid loading placeholder', () => {
    const html = renderMermaidPlaceholder({
      id: 'mermaid-1',
      code: 'graph TD; A-->B;',
    });

    expect(html).toContain('class="mermaid-wrapper"');
    expect(html).toContain('data-mermaid-id="mermaid-1"');
    expect(html).toContain('data-mermaid-code="graph%20TD%3B%20A--%3EB%3B"');
    expect(html).toContain('<span>正在渲染图表...</span>');
    expect(html).toContain('<div class="mermaid-content" id="mermaid-1"></div>');
  });
});

describe('renderMermaidError', () => {
  it('renders the existing mermaid error content with raw code', () => {
    const html = renderMermaidError('graph TD; A-->B;');

    expect(html).toContain('class="mermaid-error"');
    expect(html).toContain('<span>图表渲染失败</span>');
    expect(html).toContain('<pre class="mermaid-raw-code">graph TD; A-->B;</pre>');
  });
});

describe('renderKaTeX', () => {
  it('renders display math with the existing KaTeX options', () => {
    const html = renderKaTeX('a+b', true);

    expect(html).toContain('class="katex-display"');
    expect(html).toContain('a');
    expect(html).toContain('b');
  });
});

describe('preprocessMath', () => {
  const createId = (() => {
    let counter = 0;
    return (kind: 'block' | 'inline') => `MATH_${kind.toUpperCase()}_${counter++}`;
  });

  it('replaces block and inline formulas with generated placeholders', () => {
    const nextId = createId();
    const result = preprocessMath('Block $$a+b$$ and inline $x_1$.', nextId);

    expect(result.text).toBe('Block MATH_BLOCK_0 and inline MATH_INLINE_1.');
    expect(result.mathBlocks.get('MATH_BLOCK_0')).toContain('<div class="katex-display">');
    expect(result.mathBlocks.get('MATH_INLINE_1')).toContain('<span class="katex-inline">');
  });

  it('preserves text that does not look like math', () => {
    const result = preprocessMath('Cost is $100 and $$ok$$ stays.', createId());

    expect(result.text).toBe('Cost is $100 and $$ok$$ stays.');
    expect(result.mathBlocks.size).toBe(0);
  });
});

describe('postprocessMath', () => {
  it('restores math placeholder HTML', () => {
    const blocks = new Map([['MATH_INLINE_1', '<span class="katex-inline">x</span>']]);

    expect(postprocessMath('Value MATH_INLINE_1.', blocks)).toBe('Value <span class="katex-inline">x</span>.');
  });
});

import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';

import {
  createMermaidLoader,
  escapeCodeForCopyAttribute,
  getCodeBlockLayout,
  normalizeMarkdownCodeToken,
  postprocessMath,
  preprocessMath,
  renderHighlightedCodeBlock,
  renderKaTeX,
  renderMermaidError,
  renderMermaidPlaceholder,
  renderMermaidWrapper,
  renderMarkdownLink,
  resetMermaidLoader,
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
  it('renders the Mermaid toolbar, source panel, and loading placeholder', () => {
    const html = renderMermaidPlaceholder({
      id: 'mermaid-1',
      code: 'graph TD; A-->B;',
      labels: {
        toolbar: 'Mermaid diagram tools',
        fullscreen: 'Fullscreen',
        copySource: 'Copy Mermaid source',
        downloadSvg: 'Download SVG',
        zoomIn: 'Zoom in',
        zoomOut: 'Zoom out',
        resetZoom: 'Reset zoom',
        showSource: 'Show source',
      },
    });

    expect(html).toContain('class="mermaid-wrapper"');
    expect(html).toContain('data-mermaid-id="mermaid-1"');
    expect(html).toContain('data-mermaid-code="graph%20TD%3B%20A--%3EB%3B"');
    expect(html).toContain('class="mermaid-toolbar"');
    expect(html).toContain('data-mermaid-action="fullscreen"');
    expect(html).toContain('data-mermaid-action="copy-source"');
    expect(html).toContain('data-mermaid-action="download-svg"');
    expect(html).toContain('data-mermaid-action="toggle-source"');
    expect(html).toContain('class="mermaid-viewport"');
    expect(html).toContain('class="mermaid-transform-layer"');
    expect(html).toContain('class="mermaid-feedback" role="status" hidden');
    expect(html).toContain('data-mermaid-source-panel');
    expect(html).toContain('<span>正在渲染图表...</span>');
    expect(html).toContain('<div class="mermaid-content" id="mermaid-1"></div>');
  });
});

describe('renderMermaidError', () => {
  it('renders the existing mermaid error content with raw code', () => {
    const html = renderMermaidError('graph TD; A-->B;');

    expect(html).toContain('class="mermaid-error"');
    expect(html).toContain('<span>图表渲染失败</span>');
    expect(html).toContain('<pre class="mermaid-raw-code">graph TD; A--&gt;B;</pre>');
  });
});

describe('renderMermaidWrapper', () => {
  const createWrapper = (code: string) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'mermaid-wrapper';
    wrapper.setAttribute('data-mermaid-code', encodeURIComponent(code));
    wrapper.innerHTML = `
      <div class="mermaid-loading"></div>
      <div class="mermaid-content"></div>
    `;
    return wrapper;
  };

  /** renderMermaidWrapper 内部用 wrapper.isConnected 校验 DOM 有效性，
   *  脱离文档树的节点 isConnected === false，所以测试需要先挂载到 document */
  const attachedWrappers: HTMLElement[] = [];
  afterEach(() => {
    attachedWrappers.forEach(w => {
      if (w.parentNode) w.parentNode.removeChild(w);
    });
    attachedWrappers.length = 0;
  });
  const attachWrapper = (wrapper: HTMLElement) => {
    document.body.appendChild(wrapper);
    attachedWrappers.push(wrapper);
    return wrapper;
  };

  it('renders mermaid SVG and caches the result', async () => {
    const wrapper = attachWrapper(createWrapper('graph TD; A-->B;'));
    const cache = new Map<string, string>();
    const mermaid = {
      render: async (id: string, code: string) => ({
        svg: `<svg data-id="${id}">${code}</svg>`,
      }),
    };

    await renderMermaidWrapper({
      wrapper,
      index: 0,
      mermaid,
      cache,
      makeRenderId: index => `test-svg-${index}`,
    });

    const content = wrapper.querySelector('.mermaid-content') as HTMLElement;
    const loading = wrapper.querySelector('.mermaid-loading') as HTMLElement;
    expect(content.querySelector('svg')?.getAttribute('data-id')).toBe('test-svg-0');
    expect(content.style.display).toBe('block');
    expect(loading.style.display).toBe('none');
    expect(cache.get('graph TD; A-->B;')).toBe('<svg data-id="test-svg-0">graph TD; A-->B;</svg>');
  });

  it('uses cached SVG without calling mermaid render', async () => {
    const wrapper = attachWrapper(createWrapper('graph TD; A-->B;'));
    const cache = new Map([['graph TD; A-->B;', '<svg>cached</svg>']]);
    const mermaid = {
      render: async () => {
        throw new Error('should not render');
      },
    };

    await renderMermaidWrapper({
      wrapper,
      index: 0,
      mermaid,
      cache,
    });

    const content = wrapper.querySelector('.mermaid-content') as HTMLElement;
    const loading = wrapper.querySelector('.mermaid-loading') as HTMLElement;
    expect(content.innerHTML).toBe('<svg>cached</svg>');
    expect(content.style.display).toBe('block');
    expect(loading.style.display).toBe('none');
  });

  it('shows the existing error HTML when mermaid render fails', async () => {
    const wrapper = attachWrapper(createWrapper('flowchart TD\nA'));
    const cache = new Map<string, string>();
    const mermaid = {
      render: async () => {
        throw new Error('render failed');
      },
    };

    await renderMermaidWrapper({
      wrapper,
      index: 0,
      mermaid,
      cache,
    });

    const loading = wrapper.querySelector('.mermaid-loading') as HTMLElement;
    expect(loading.innerHTML).toContain('class="mermaid-error"');
    expect(loading.innerHTML).toContain('<span>图表渲染失败</span>');
    expect(loading.querySelector('.mermaid-raw-code')?.textContent).toBe('flowchart TD\nA');
  });

  it('retries once and displays SVG when the second render succeeds', async () => {
    vi.useFakeTimers();
    const wrapper = attachWrapper(createWrapper('graph TD; A-->B;'));
    const cache = new Map<string, string>();
    const mermaid = {
      render: vi.fn()
        .mockRejectedValueOnce(new Error('first render failed'))
        .mockResolvedValueOnce({ svg: '<svg data-test="retry"></svg>' }),
    };

    const renderPromise = renderMermaidWrapper({
      wrapper,
      index: 2,
      mermaid,
      cache,
      makeRenderId: index => `retry-svg-${index}`,
      maxRetries: 1,
      retryDelayMs: 300,
    });

    await vi.advanceTimersByTimeAsync(300);
    await renderPromise;
    vi.useRealTimers();

    const content = wrapper.querySelector('.mermaid-content') as HTMLElement;
    const loading = wrapper.querySelector('.mermaid-loading') as HTMLElement;
    expect(mermaid.render).toHaveBeenNthCalledWith(1, 'retry-svg-4', 'graph TD; A-->B;');
    expect(mermaid.render).toHaveBeenNthCalledWith(2, 'retry-svg-5', 'graph TD; A-->B;');
    expect(content.innerHTML).toContain('data-test="retry"');
    expect(content.style.display).toBe('block');
    expect(loading.style.display).toBe('none');
  });

  it('skips DOM write when wrapper is disconnected from the document', async () => {
    // 不挂载到 document → isConnected === false
    const wrapper = createWrapper('graph TD; A-->B;');
    const cache = new Map<string, string>();
    const mermaid = {
      render: async (id: string, code: string) => ({
        svg: `<svg data-id="${id}">${code}</svg>`,
      }),
    };

    await renderMermaidWrapper({
      wrapper,
      index: 0,
      mermaid,
      cache,
    });

    // SVG 不写入脱离文档的 DOM
    const content = wrapper.querySelector('.mermaid-content') as HTMLElement;
    expect(content.innerHTML).toBe('');
    // 但缓存应已填充，以便后续重连的 wrapper 可复用
    expect(cache.has('graph TD; A-->B;')).toBe(true);
  });

  it('does not write an error when a retry target disconnects before retry', async () => {
    vi.useFakeTimers();
    const wrapper = attachWrapper(createWrapper('graph TD; A-->B;'));
    const cache = new Map<string, string>();
    const mermaid = {
      render: vi.fn().mockRejectedValueOnce(new Error('first render failed')),
    };

    const renderPromise = renderMermaidWrapper({
      wrapper,
      index: 0,
      mermaid,
      cache,
      maxRetries: 1,
      retryDelayMs: 300,
    });
    wrapper.remove();

    await vi.advanceTimersByTimeAsync(300);
    await renderPromise;
    vi.useRealTimers();

    const loading = wrapper.querySelector('.mermaid-loading') as HTMLElement;
    expect(mermaid.render).toHaveBeenCalledTimes(1);
    expect(loading.innerHTML).not.toContain('mermaid-error');
  });
});

describe('createMermaidLoader', () => {
  beforeEach(() => {
    resetMermaidLoader();
  });

  it('uses a single dynamic import promise and initializes mermaid once', async () => {
    let importCount = 0;
    const initializeCalls: Record<string, unknown>[] = [];
    const mermaid = {
      initialize: (config: Record<string, unknown>) => {
        initializeCalls.push(config);
      },
      render: async () => ({ svg: '<svg></svg>' }),
    };
    const loader = createMermaidLoader(async () => {
      importCount += 1;
      return mermaid;
    });

    await Promise.all([loader.loadMermaid(), loader.loadMermaid()]);
    await loader.initMermaid();
    await loader.initMermaid();

    expect(importCount).toBe(1);
    expect(initializeCalls).toHaveLength(1);
    expect(initializeCalls[0]).toMatchObject({
      startOnLoad: false,
      theme: 'base',
      securityLevel: 'loose',
      fontFamily: 'inherit',
      themeVariables: {
        background: 'transparent',
        primaryColor: '#f8fafc',
        primaryTextColor: '#0f172a',
        primaryBorderColor: '#64748b',
      },
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis',
      },
      sequence: {
        useMaxWidth: true,
        diagramMarginX: 10,
        diagramMarginY: 10,
      },
      gantt: {
        useMaxWidth: true,
      },
    });
  });

  it('returns mermaid even when initialization throws', async () => {
    const mermaid = {
      initialize: () => {
        throw new Error('init failed');
      },
      render: async () => ({ svg: '<svg></svg>' }),
    };
    const loader = createMermaidLoader(async () => mermaid);

    await expect(loader.initMermaid()).resolves.toBe(mermaid);
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

  it('renders common single-letter inline formulas', () => {
    const result = preprocessMath('Let $x$ be positive.', createId());

    expect(result.text).toBe('Let MATH_INLINE_0 be positive.');
    expect(result.mathBlocks.get('MATH_INLINE_0')).toContain('<span class="katex-inline">');
  });

  it('does not preprocess math inside fenced code blocks', () => {
    const result = preprocessMath(['```md', 'inline $x$ stays literal', '```'].join('\n'), createId());

    expect(result.text).toBe(['```md', 'inline $x$ stays literal', '```'].join('\n'));
    expect(result.mathBlocks.size).toBe(0);
  });

  it('does not preprocess math inside tilde fenced code blocks', () => {
    const result = preprocessMath(['~~~mermaid', 'inline $x$ stays literal', '~~~'].join('\n'), createId());

    expect(result.text).toBe(['~~~mermaid', 'inline $x$ stays literal', '~~~'].join('\n'));
    expect(result.mathBlocks.size).toBe(0);
  });
});

describe('postprocessMath', () => {
  it('restores math placeholder HTML', () => {
    const blocks = new Map([['MATH_INLINE_1', '<span class="katex-inline">x</span>']]);

    expect(postprocessMath('Value MATH_INLINE_1.', blocks)).toBe('Value <span class="katex-inline">x</span>.');
  });
});

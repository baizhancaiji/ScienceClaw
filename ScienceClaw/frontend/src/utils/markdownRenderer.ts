import katex from 'katex';

export interface MarkedLinkToken {
  href?: string;
  title?: string | null;
  text?: string;
}

export interface MarkedCodeToken {
  text?: unknown;
  raw?: unknown;
  lang?: unknown;
  language?: unknown;
}

export interface NormalizedCodeBlock {
  code: string;
  lang: string;
}

export interface CodeBlockLayout {
  lineCount: number;
  lineNumbers: string;
  shouldCollapse: boolean;
  collapseClass: string;
}

export interface HighlightedCodeBlockOptions {
  code: string;
  highlightedCode: string;
  lang: string;
}

export interface MermaidPlaceholderOptions {
  id: string;
  code: string;
}

export interface MermaidRenderAdapter {
  render: (id: string, code: string) => Promise<{ svg: string }>;
}

export interface RenderMermaidWrapperOptions {
  wrapper: Element;
  index: number;
  mermaid: MermaidRenderAdapter;
  cache: Map<string, string>;
  logPrefix?: string;
  now?: () => number;
  makeRenderId?: (index: number) => string;
}

export type MathPlaceholderKind = 'block' | 'inline';

export interface PreprocessMathResult {
  text: string;
  mathBlocks: Map<string, string>;
}

export type CreateMathPlaceholderId = (kind: MathPlaceholderKind) => string;

export const normalizeMarkdownCodeToken = (
  token: MarkedCodeToken | string,
  language?: string,
): NormalizedCodeBlock => {
  try {
    if (typeof token === 'object' && token !== null) {
      const rawCode = token.text ?? token.raw ?? '';
      const rawLang = token.lang || token.language || 'plaintext';
      return {
        code: rawCode === null || rawCode === undefined ? '' : String(rawCode),
        lang: typeof rawLang === 'string' && rawLang ? rawLang : 'plaintext',
      };
    }

    if (typeof token === 'string') {
      return {
        code: token,
        lang: language || 'plaintext',
      };
    }
  } catch {
    // Fall through to the same safe default used by the component renderer.
  }

  return { code: '', lang: 'plaintext' };
};

export const escapeCodeForCopyAttribute = (code: string): string => code
  .replace(/&/g, '&amp;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;')
  .replace(/`/g, '&#96;');

export const getCodeBlockLayout = (
  highlightedCode: string,
  collapseAfterLines = 20,
): CodeBlockLayout => {
  const lineCount = highlightedCode.split('\n').length;
  const shouldCollapse = lineCount > collapseAfterLines;

  return {
    lineCount,
    lineNumbers: Array.from({ length: lineCount }, (_, i) => i + 1).join('\n'),
    shouldCollapse,
    collapseClass: shouldCollapse ? 'code-block-collapsed' : '',
  };
};

export const renderHighlightedCodeBlock = ({
  code,
  highlightedCode,
  lang,
}: HighlightedCodeBlockOptions): string => {
  const escapedCode = escapeCodeForCopyAttribute(code);
  const { lineCount, lineNumbers, shouldCollapse, collapseClass } = getCodeBlockLayout(highlightedCode);

  return `<div class="code-block-wrapper ${collapseClass}" data-lines="${lineCount}">
    <div class="code-block-header">
      <span class="code-block-lang">${lang}</span>
      <span class="code-block-line-count">${lineCount} 行</span>
      <div class="code-block-actions">
        ${shouldCollapse ? `<button class="code-block-expand" onclick="this.closest('.code-block-wrapper').classList.toggle('code-block-collapsed')">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="7 13 12 18 17 13"></polyline><polyline points="7 6 12 11 17 6"></polyline></svg>
          <span class="expand-text">展开</span>
        </button>` : ''}
        <button class="code-block-fullscreen" title="全屏查看">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>
          <span>全屏</span>
        </button>
        <button class="code-block-copy" onclick="navigator.clipboard.writeText(decodeURIComponent(\`${encodeURIComponent(escapedCode)}\`)).then(() => { const el = this.querySelector('span'); el.textContent = '已复制!'; setTimeout(() => el.textContent = '复制', 2000); }).catch(() => this.querySelector('span').textContent = '失败')">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
          <span>复制</span>
        </button>
      </div>
    </div>
    <div class="code-block-content">
      <div class="code-block-lines"><pre>${lineNumbers}</pre></div>
      <pre class="code-block-pre"><code class="hljs language-${lang}">${highlightedCode}</code></pre>
    </div>
    ${shouldCollapse ? `<div class="code-block-expand-hint" onclick="this.closest('.code-block-wrapper').classList.remove('code-block-collapsed')">点击展开全部 ${lineCount} 行代码</div>` : ''}
  </div>`;
};

export const renderMermaidPlaceholder = ({ id, code }: MermaidPlaceholderOptions): string => (
  `<div class="mermaid-wrapper" data-mermaid-id="${id}" data-mermaid-code="${encodeURIComponent(code)}">
      <div class="mermaid-loading">
        <svg class="animate-spin h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>正在渲染图表...</span>
      </div>
      <div class="mermaid-content" id="${id}"></div>
    </div>`
);

export const renderMermaidError = (code: string): string => (
  `<div class="mermaid-error">
            <svg class="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>图表渲染失败</span>
          </div>
          <pre class="mermaid-raw-code">${code}</pre>`
);

export const renderMermaidWrapper = async ({
  wrapper,
  index,
  mermaid,
  cache,
  logPrefix = '[Mermaid]',
  now = () => performance.now(),
  makeRenderId = diagramIndex => `mermaid-svg-${Date.now()}-${diagramIndex}`,
}: RenderMermaidWrapperOptions): Promise<void> => {
  const code = decodeURIComponent(wrapper.getAttribute('data-mermaid-code') || '');
  const contentEl = wrapper.querySelector('.mermaid-content') as HTMLElement;
  const loadingEl = wrapper.querySelector('.mermaid-loading') as HTMLElement;

  if (!code || !contentEl) {
    console.warn(logPrefix, `Diagram ${index + 1}: missing code or content element`);
    return;
  }

  console.log(logPrefix, `Diagram ${index + 1}:`, code.substring(0, 50) + '...');

  // 检查缓存
  if (cache.has(code)) {
    console.log(logPrefix, `Diagram ${index + 1}: using cache`);
    contentEl.innerHTML = cache.get(code)!;
    if (loadingEl) loadingEl.style.display = 'none';
    contentEl.style.display = 'block';
    return;
  }

  try {
    const startTime = now();
    // 使用 mermaid.render 渲染
    const { svg } = await mermaid.render(makeRenderId(index), code);
    cache.set(code, svg);
    contentEl.innerHTML = svg;
    if (loadingEl) loadingEl.style.display = 'none';
    contentEl.style.display = 'block';
    const elapsed = (now() - startTime).toFixed(2);
    console.log(logPrefix, `Diagram ${index + 1}: rendered in ${elapsed}ms`);
  } catch (e) {
    console.error(logPrefix, `Diagram ${index + 1}: render error:`, e);
    if (loadingEl) {
      loadingEl.innerHTML = renderMermaidError(code);
    }
  }
};

export const renderKaTeX = (formula: string, displayMode: boolean = false): string => {
  try {
    return katex.renderToString(formula, {
      displayMode,
      throwOnError: false,
      output: 'html',
      strict: false,
      trust: true,
    });
  } catch (e) {
    console.warn('KaTeX render error:', e);
    // 返回原始公式作为后备
    return displayMode
      ? `<div class="katex-error">$$${formula}$$</div>`
      : `<span class="katex-error">$${formula}$</span>`;
  }
};

export const preprocessMath = (
  text: string,
  createPlaceholderId: CreateMathPlaceholderId,
): PreprocessMathResult => {
  const mathBlocks = new Map<string, string>();
  let result = text;

  try {
    // 处理块级公式 $$...$$
    // 只匹配多行或包含数学符号的内容
    result = result.replace(/\$\$([\s\S]+?)\$\$/g, (_, formula) => {
      const trimmed = formula.trim();
      // 检查是否像数学公式
      const hasMathChars = /[\^\\\_\/\+\-\=\<\>\(\)\[\]\{\}]/.test(trimmed);
      const hasGreekLetters = /alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|omega/i.test(trimmed);

      if (!hasMathChars && !hasGreekLetters && trimmed.length < 3) {
        // 不像数学公式，保留原样
        return `$$${formula}$$`;
      }

      const id = createPlaceholderId('block');
      const rendered = renderKaTeX(trimmed, true);
      mathBlocks.set(id, `<div class="katex-display">${rendered}</div>`);
      console.log('[KaTeX] Block formula:', trimmed.substring(0, 50));
      return id;
    });

    // 处理行内公式 $...$
    // 严格匹配：必须是合理的数学表达式
    result = result.replace(/\$([^\$\n]+?)\$/g, (fullMatch, formula) => {
      const trimmed = formula.trim();

      // 排除条件：
      // 1. 内容为空
      // 2. 只包含数字（货币符号如 $100）
      // 3. 包含 Markdown 语法字符
      // 4. 长度太短且不含数学符号
      if (!trimmed || /^\d+(\.\d+)?$/.test(trimmed)) {
        return fullMatch; // 货币符号，保留原样
      }
      if (trimmed.includes('**') || trimmed.includes('__') || trimmed.includes('##')) {
        return fullMatch; // Markdown 语法，保留原样
      }
      if (trimmed.length < 2 && !/[\^\\\_]/.test(trimmed)) {
        return fullMatch; // 太短且不是数学符号
      }

      // 检查是否像数学公式
      const hasMathChars = /[\^\\\_\/\+\-\=\<\>\(\)\[\]\{\}]/.test(trimmed);
      const hasGreekLetters = /alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|omega|infty|frac|sqrt/i.test(trimmed);
      const hasSubscript = /[a-zA-Z]_[a-zA-Z0-9]/.test(trimmed);

      if (!hasMathChars && !hasGreekLetters && !hasSubscript) {
        // 不像数学公式，保留原样
        return fullMatch;
      }

      const id = createPlaceholderId('inline');
      try {
        const rendered = renderKaTeX(trimmed, false);
        mathBlocks.set(id, `<span class="katex-inline">${rendered}</span>`);
        console.log('[KaTeX] Inline formula:', trimmed.substring(0, 30));
        return id;
      } catch (e) {
        console.warn('[KaTeX] Failed to render:', trimmed);
        return fullMatch; // 渲染失败，保留原样
      }
    });

    if (mathBlocks.size > 0) {
      console.log('[KaTeX] Preprocessed', mathBlocks.size, 'formulas');
    }
  } catch (e) {
    console.error('[KaTeX] Preprocess error:', e);
    // 返回原始文本
    return { text: text, mathBlocks: new Map() };
  }

  return { text: result, mathBlocks };
};

export const postprocessMath = (text: string, mathBlocks: Map<string, string>): string => {
  let result = text;
  mathBlocks.forEach((html, id) => {
    result = result.replace(id, html);
  });
  return result;
};

export const renderMarkdownLink = (
  token: MarkedLinkToken | string,
  title?: string | null,
  text?: string,
): string => {
  let href: string;
  let linkTitle: string | null | undefined;
  let linkText = '';

  try {
    if (typeof token === 'object' && token !== null) {
      href = token.href ?? '#';
      linkTitle = token.title;
      linkText = token.text ?? '';
    } else if (typeof token === 'string') {
      href = token || '#';
      linkTitle = title;
      linkText = text || '';
    } else {
      href = '#';
      linkTitle = null;
      linkText = '';
    }

    if (!href || typeof href !== 'string') {
      href = '#';
    }
  } catch {
    href = '#';
    linkText = linkText || '';
  }

  const isExternal = href.startsWith('http://') || href.startsWith('https://');
  const titleAttr = linkTitle ? ` title="${linkTitle}"` : '';
  const targetAttr = isExternal ? ' target="_blank" rel="noopener noreferrer"' : '';
  return `<a href="${href}"${titleAttr}${targetAttr}>${linkText}</a>`;
};

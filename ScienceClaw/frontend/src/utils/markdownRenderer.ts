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

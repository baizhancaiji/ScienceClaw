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

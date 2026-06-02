export interface MarkedLinkToken {
  href?: string;
  title?: string | null;
  text?: string;
}

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

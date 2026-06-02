export interface ChatMessagePart {
  type: 'html' | 'molecule' | 'image' | 'html-file' | 'questions';
  content?: string;
  src?: string;
  alt?: string;
  questions?: string[];
}

export interface ParseChatMessageContentOptions {
  renderMarkdown: (markdown: string) => string;
  transformSrc: (src: string) => string;
}

const extractSuggestedQuestions = (markdown: string): { content: string; questions: string[] } => {
  const questions: string[] = [];
  const suggestionRegex = /<suggested_questions>([\s\S]*?)<\/suggested_questions>/;
  const match = markdown.match(suggestionRegex);

  if (!match) {
    return { content: markdown, questions };
  }

  const questionsXml = match[1];
  const qRegex = /<question>(.*?)<\/question>/g;
  let qMatch;
  while ((qMatch = qRegex.exec(questionsXml)) !== null) {
    questions.push(qMatch[1].trim());
  }

  return {
    content: markdown.replace(suggestionRegex, ''),
    questions,
  };
};

const escapeHtml = (text: string): string => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

export const parseChatMessageContent = (
  markdown: string,
  { renderMarkdown, transformSrc }: ParseChatMessageContentOptions,
): ChatMessagePart[] => {
  const { content, questions } = extractSuggestedQuestions(markdown);
  const html = renderMarkdown(content);

  const parser = new DOMParser();
  const doc = parser.parseFromString(`<body>${html}</body>`, 'text/html');
  const body = doc.body;

  const processNode = (node: Node): ChatMessagePart[] => {
    if (node.nodeType === Node.TEXT_NODE) {
      const text = node.textContent || '';
      if (!text.trim()) return [];
      return [{ type: 'html', content: escapeHtml(text) }];
    }

    if (node.nodeType !== Node.ELEMENT_NODE) {
      return [];
    }

    const el = node as HTMLElement;
    const tagName = el.tagName.toLowerCase();

    if (tagName === 'molecule-viewer') {
      return [{ type: 'molecule', src: transformSrc(el.getAttribute('src') || '') }];
    }
    if (tagName === 'html-viewer') {
      return [{ type: 'html-file', src: transformSrc(el.getAttribute('src') || '') }];
    }
    if (tagName === 'img') {
      return [{
        type: 'image',
        src: transformSrc(el.getAttribute('src') || ''),
        alt: el.getAttribute('alt') || '',
      }];
    }

    let childParts: ChatMessagePart[] = [];
    node.childNodes.forEach(child => {
      childParts = childParts.concat(processNode(child));
    });

    const hasSpecialComponent = childParts.some(part => part.type !== 'html');
    return hasSpecialComponent ? childParts : [{ type: 'html', content: el.outerHTML }];
  };

  let rawParts: ChatMessagePart[] = [];
  body.childNodes.forEach(node => {
    rawParts = rawParts.concat(processNode(node));
  });

  const mergedParts: ChatMessagePart[] = [];
  let currentHtmlContent = '';

  rawParts.forEach(part => {
    if (part.type === 'html') {
      currentHtmlContent += part.content || '';
    } else {
      if (currentHtmlContent) {
        mergedParts.push({ type: 'html', content: currentHtmlContent });
        currentHtmlContent = '';
      }
      mergedParts.push(part);
    }
  });

  if (currentHtmlContent) {
    mergedParts.push({ type: 'html', content: currentHtmlContent });
  }

  if (questions.length > 0) {
    mergedParts.push({ type: 'questions', questions });
  }

  return mergedParts.length > 0 ? mergedParts : [{ type: 'html', content: '' }];
};

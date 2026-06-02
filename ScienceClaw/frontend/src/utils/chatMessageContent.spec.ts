import { describe, expect, it } from 'vitest';

import { parseChatMessageContent } from './chatMessageContent';

const parse = (html: string) => parseChatMessageContent(html, {
  renderMarkdown: value => value,
  transformSrc: src => `/transformed${src}`,
});

describe('parseChatMessageContent', () => {
  it('returns merged html content for plain rendered markdown', () => {
    expect(parse('<p>Hello</p><p>World</p>')).toEqual([
      { type: 'html', content: '<p>Hello</p><p>World</p>' },
    ]);
  });

  it('extracts suggested questions after rendered content', () => {
    expect(parse('<p>Answer</p><suggested_questions><question>Next?</question><question>Why?</question></suggested_questions>')).toEqual([
      { type: 'html', content: '<p>Answer</p>' },
      { type: 'questions', questions: ['Next?', 'Why?'] },
    ]);
  });

  it('splits special viewer nodes and transforms their sources', () => {
    expect(parse('<p>Before</p><molecule-viewer src="/mol.sdf"></molecule-viewer><img src="/plot.png" alt="Plot"><html-viewer src="/report.html"></html-viewer><p>After</p>')).toEqual([
      { type: 'html', content: '<p>Before</p>' },
      { type: 'molecule', src: '/transformed/mol.sdf' },
      { type: 'image', src: '/transformed/plot.png', alt: 'Plot' },
      { type: 'html-file', src: '/transformed/report.html' },
      { type: 'html', content: '<p>After</p>' },
    ]);
  });

  it('returns an empty html part when nothing renderable remains', () => {
    expect(parse('')).toEqual([{ type: 'html', content: '' }]);
  });
});

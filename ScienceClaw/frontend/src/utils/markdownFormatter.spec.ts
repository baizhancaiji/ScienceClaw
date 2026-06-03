import { describe, expect, it } from 'vitest';

import { formatMarkdown } from './markdownFormatter';

describe('formatMarkdown', () => {
  it('preserves explicit markdown source fences instead of unwrapping them', () => {
    const input = ['```markdown', '# Title', '', '- item', '```'].join('\n');

    expect(formatMarkdown(input)).toBe(input);
  });
});

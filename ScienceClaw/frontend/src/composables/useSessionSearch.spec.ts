import { describe, expect, it } from 'vitest';
import { nextTick, ref } from 'vue';

import type { Message, MessageContent, MessageType } from '../types/message';
import { getSessionSearchMessageKey, useSessionSearch } from './useSessionSearch';

const message = (type: Extract<MessageType, 'user' | 'assistant' | 'tool'>, content: string, timestamp: number): Message => ({
  type,
  content: { content, timestamp } as MessageContent,
});

describe('getSessionSearchMessageKey', () => {
  it('builds a stable DOM key from the original message index', () => {
    expect(getSessionSearchMessageKey(7)).toBe('session-search-message-7');
  });
});

describe('useSessionSearch', () => {
  it('searches user and assistant messages only', () => {
    const search = useSessionSearch(ref([
      message('user', 'Find the catalyst', 1),
      message('tool', 'tool output mentions catalyst', 2),
      message('assistant', 'The Catalyst appears twice: catalyst.', 3),
    ]));

    search.query.value = 'catalyst';

    expect(search.results.value).toHaveLength(3);
    expect(search.results.value.map((result) => result.messageIndex)).toEqual([0, 2, 2]);
    expect(search.results.value.map((result) => result.role)).toEqual(['user', 'assistant', 'assistant']);
  });

  it('supports excluded message indexes and result navigation', () => {
    const excludedMessageIndexes = ref([1]);
    const search = useSessionSearch(
      ref([
        message('user', 'alpha one', 1),
        message('assistant', 'alpha excluded', 2),
        message('assistant', 'alpha final', 3),
      ]),
      { excludedMessageIndexes },
    );

    search.query.value = 'alpha';

    expect(search.results.value.map((result) => result.messageIndex)).toEqual([0, 2]);
    expect(search.currentResult.value?.messageIndex).toBe(0);
    expect(search.selectNext()?.messageIndex).toBe(2);
    expect(search.canSelectNext.value).toBe(false);
    expect(search.selectPrevious()?.messageIndex).toBe(0);
  });

  it('resets active index when query changes and clears state on close', async () => {
    const search = useSessionSearch(ref([
      message('user', 'alpha alpha', 1),
      message('assistant', 'beta', 2),
    ]));

    search.openSearch();
    search.query.value = 'alpha';
    search.selectResult(1);
    expect(search.activeIndex.value).toBe(1);

    search.query.value = 'beta';
    await nextTick();
    expect(search.activeIndex.value).toBe(0);
    expect(search.results.value).toHaveLength(1);

    search.closeSearch();
    expect(search.isOpen.value).toBe(false);
    expect(search.query.value).toBe('');
    expect(search.activeIndex.value).toBe(0);
  });
});

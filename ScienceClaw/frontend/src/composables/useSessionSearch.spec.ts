import { describe, expect, it } from 'vitest';
import { nextTick } from 'vue';

import { getSessionSearchMessageKey, useSessionSearch } from './useSessionSearch';

const backendResult = (eventId: string, eventIndex: number, role: 'user' | 'assistant' = 'user') => ({
  id: `${eventIndex}-0`,
  event_id: eventId,
  event_index: eventIndex,
  role,
  text: `text ${eventIndex}`,
  snippet: `snippet ${eventIndex}`,
  match_start: 0,
  match_end: 4,
  timestamp: eventIndex,
});

describe('getSessionSearchMessageKey', () => {
  it('builds a stable DOM key from the event id or fallback index', () => {
    expect(getSessionSearchMessageKey('evt-7')).toBe('session-search-message-evt-7');
    expect(getSessionSearchMessageKey(7)).toBe('session-search-message-7');
  });
});

describe('useSessionSearch', () => {
  it('maps backend search results and supports result navigation', () => {
    const search = useSessionSearch();

    search.setSearchResults([
      backendResult('evt-1', 0, 'user'),
      backendResult('evt-2', 2, 'assistant'),
    ]);

    expect(search.results.value).toHaveLength(2);
    expect(search.results.value.map(result => result.eventId)).toEqual(['evt-1', 'evt-2']);
    expect(search.results.value.map(result => result.eventIndex)).toEqual([0, 2]);
    expect(search.results.value.map(result => result.roleLabel)).toEqual(['User', 'ScienceClaw']);
    expect(search.currentResult.value?.eventId).toBe('evt-1');
    expect(search.selectNext()?.eventId).toBe('evt-2');
    expect(search.canSelectNext.value).toBe(false);
    expect(search.selectPrevious()?.eventId).toBe('evt-1');
  });

  it('resets active index when query changes and clears state on close', async () => {
    const search = useSessionSearch();

    search.openSearch();
    search.setSearchResults([
      backendResult('evt-1', 0),
      backendResult('evt-2', 1),
    ]);
    search.selectResult(1);
    expect(search.activeIndex.value).toBe(1);

    search.query.value = 'beta';
    await nextTick();
    expect(search.activeIndex.value).toBe(0);
    expect(search.results.value).toHaveLength(2);

    search.closeSearch();
    expect(search.isOpen.value).toBe(false);
    expect(search.query.value).toBe('');
    expect(search.results.value).toHaveLength(0);
    expect(search.activeIndex.value).toBe(0);
  });
});

import { computed, ref, watch } from 'vue';

import type { SessionSearchResult as ApiSessionSearchResult } from '../types/response';

export interface SessionSearchResult {
  id: string;
  eventId: string;
  eventIndex: number;
  messageKey: string;
  role: 'user' | 'assistant';
  roleLabel: string;
  text: string;
  snippet: string;
  matchStart: number;
  matchEnd: number;
  timestamp: number;
}

export const getSessionSearchMessageKey = (eventIdOrIndex: string | number) => `session-search-message-${eventIdOrIndex}`;

const toSessionSearchResult = (result: ApiSessionSearchResult): SessionSearchResult => ({
  id: result.id,
  eventId: result.event_id,
  eventIndex: result.event_index,
  messageKey: getSessionSearchMessageKey(result.event_id || result.event_index),
  role: result.role,
  roleLabel: result.role === 'user' ? 'User' : 'ScienceClaw',
  text: result.text,
  snippet: result.snippet,
  matchStart: result.match_start,
  matchEnd: result.match_end,
  timestamp: result.timestamp,
});

export function useSessionSearch() {
  const isOpen = ref(false);
  const query = ref('');
  const activeIndex = ref(0);
  const isSearching = ref(false);
  const results = ref<SessionSearchResult[]>([]);

  const currentResult = computed(() => results.value[activeIndex.value] ?? null);
  const hasResults = computed(() => results.value.length > 0);
  const canSelectPrevious = computed(() => hasResults.value && activeIndex.value > 0);
  const canSelectNext = computed(() => hasResults.value && activeIndex.value < results.value.length - 1);

  const openSearch = () => {
    isOpen.value = true;
  };

  const closeSearch = ({ clearQuery = true } = {}) => {
    isOpen.value = false;
    activeIndex.value = 0;
    results.value = [];
    isSearching.value = false;
    if (clearQuery) {
      query.value = '';
    }
  };

  const setSearchResults = (nextResults: ApiSessionSearchResult[]) => {
    results.value = nextResults.map(toSessionSearchResult);
    activeIndex.value = results.value.length ? Math.min(activeIndex.value, results.value.length - 1) : 0;
  };

  const clearSearchResults = () => {
    results.value = [];
    activeIndex.value = 0;
  };

  const selectResult = (index: number) => {
    if (!results.value.length) return null;

    const nextIndex = Math.max(0, Math.min(index, results.value.length - 1));
    activeIndex.value = nextIndex;
    return results.value[nextIndex] ?? null;
  };

  const selectPrevious = () => {
    if (!canSelectPrevious.value) return currentResult.value;
    return selectResult(activeIndex.value - 1);
  };

  const selectNext = () => {
    if (!canSelectNext.value) return currentResult.value;
    return selectResult(activeIndex.value + 1);
  };

  watch(query, () => {
    activeIndex.value = 0;
  });

  return {
    activeIndex,
    canSelectNext,
    canSelectPrevious,
    clearSearchResults,
    closeSearch,
    currentResult,
    hasResults,
    isOpen,
    isSearching,
    openSearch,
    query,
    results,
    selectNext,
    selectPrevious,
    selectResult,
    setSearchResults,
  };
}

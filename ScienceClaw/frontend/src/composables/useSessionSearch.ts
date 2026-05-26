import { computed, ref, watch, type Ref } from 'vue';

import type { Message, MessageContent } from '../types/message';

export interface SessionSearchResult {
  id: string;
  messageIndex: number;
  messageKey: string;
  role: 'user' | 'assistant';
  roleLabel: string;
  text: string;
  snippet: string;
  matchStart: number;
  matchEnd: number;
  timestamp: number;
}

const SEARCHABLE_MESSAGE_TYPES = new Set(['user', 'assistant']);

const normalizeSearchText = (value: string) => value.toLocaleLowerCase();

const collapseWhitespace = (value: string) => value.replace(/\s+/g, ' ').trim();

const buildSnippet = (text: string, matchStart: number, matchEnd: number) => {
  const cleaned = collapseWhitespace(text);
  if (!cleaned) return '';

  const safeStart = Math.max(0, Math.min(matchStart, cleaned.length));
  const safeEnd = Math.max(safeStart, Math.min(matchEnd, cleaned.length));
  const snippetRadius = 42;
  const snippetStart = Math.max(0, safeStart - snippetRadius);
  const snippetEnd = Math.min(cleaned.length, safeEnd + snippetRadius);
  const prefix = snippetStart > 0 ? '...' : '';
  const suffix = snippetEnd < cleaned.length ? '...' : '';

  return `${prefix}${cleaned.slice(snippetStart, snippetEnd)}${suffix}`;
};

export const getSessionSearchMessageKey = (messageIndex: number) => `session-search-message-${messageIndex}`;

interface UseSessionSearchOptions {
  excludedMessageIndexes?: Ref<number[]>;
}

export function useSessionSearch(messages: Ref<Message[]>, options: UseSessionSearchOptions = {}) {
  const isOpen = ref(false);
  const query = ref('');
  const activeIndex = ref(0);
  const excludedIndexes = computed(() => new Set(options.excludedMessageIndexes?.value ?? []));

  const searchableMessages = computed(() =>
    messages.value
      .map((message, originalIndex) => ({ message, originalIndex }))
      .filter(({ message, originalIndex }) =>
        SEARCHABLE_MESSAGE_TYPES.has(message.type) && !excludedIndexes.value.has(originalIndex),
      )
      .map(({ message, originalIndex }) => {
        const content = message.content as MessageContent;

        return {
          message,
          originalIndex,
          text: typeof content.content === 'string' ? content.content : '',
          timestamp: content.timestamp,
        };
      })
      .filter(({ text }) => text.trim().length > 0),
  );

  const results = computed<SessionSearchResult[]>(() => {
    const trimmedQuery = query.value.trim();
    if (!trimmedQuery) return [];

    const normalizedQuery = normalizeSearchText(trimmedQuery);
    const nextResults: SessionSearchResult[] = [];

    for (const { message, originalIndex, text, timestamp } of searchableMessages.value) {
      const normalizedText = normalizeSearchText(text);
      let searchFrom = 0;

      while (searchFrom < normalizedText.length) {
        const matchStart = normalizedText.indexOf(normalizedQuery, searchFrom);
        if (matchStart === -1) break;

        const matchEnd = matchStart + normalizedQuery.length;
        nextResults.push({
          id: `${originalIndex}-${matchStart}`,
          messageIndex: originalIndex,
          messageKey: getSessionSearchMessageKey(originalIndex),
          role: message.type as 'user' | 'assistant',
          roleLabel: message.type === 'user' ? 'User' : 'ScienceClaw',
          text,
          snippet: buildSnippet(text, matchStart, matchEnd),
          matchStart,
          matchEnd,
          timestamp,
        });

        searchFrom = matchEnd;
      }
    }

    return nextResults;
  });

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
    if (clearQuery) {
      query.value = '';
    }
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

  watch(results, (nextResults) => {
    if (!nextResults.length) {
      activeIndex.value = 0;
      return;
    }

    if (activeIndex.value >= nextResults.length) {
      activeIndex.value = nextResults.length - 1;
    }
  });

  return {
    activeIndex,
    canSelectNext,
    canSelectPrevious,
    closeSearch,
    currentResult,
    hasResults,
    isOpen,
    openSearch,
    query,
    results,
    selectNext,
    selectPrevious,
    selectResult,
  };
}

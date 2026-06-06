import { beforeEach, describe, expect, it, vi } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import { ref } from 'vue';

import ChatPage from './ChatPage.vue';
import type { AgentSSEEvent } from '../types/event';

vi.mock('vue-router', () => ({
  createRouter: () => ({
    beforeEach: vi.fn(),
    push: vi.fn(),
    replace: vi.fn(),
    install: vi.fn(),
  }),
  createWebHistory: vi.fn(),
  useRouter: () => ({
    currentRoute: ref({ params: {} }),
    replace: vi.fn(),
  }),
}));

vi.mock('vue-gtag', () => ({
  configure: vi.fn(),
  default: {
    install: vi.fn(),
  },
}));

vi.mock('vue-i18n', () => ({
  createI18n: () => ({
    global: {},
    install: vi.fn(),
  }),
  useI18n: () => ({
    t: (key: string, params?: Record<string, string>) => {
      if (!params) return key;
      return Object.entries(params).reduce(
        (text, [paramKey, value]) => text.replace(`{${paramKey}}`, value),
        key,
      );
    },
    locale: ref('en'),
  }),
}));

vi.mock('../api/agent', () => ({
  chatWithSession: vi.fn(),
  clearUnreadMessageCount: vi.fn(),
  getSession: vi.fn(),
  lockSessionPassword: vi.fn(),
  stopSession: vi.fn(),
}));

vi.mock('../api/models', () => ({
  listModels: vi.fn().mockResolvedValue([{ id: 'model-a', is_system: true }]),
}));

vi.mock('../composables/useSessionFileList', () => ({
  useSessionFileList: () => ({ shared: { files: ref([]) } }),
}));

vi.mock('../composables/useFilePanel', () => ({
  useFilePanel: () => ({
    hideFilePanel: vi.fn(),
    showFileListPanel: vi.fn(),
  }),
}));

vi.mock('../composables/useSessionListUpdate', () => ({
  useSessionListUpdate: () => ({
    patchSessionItem: vi.fn(),
    updateSessionTitle: vi.fn(),
  }),
}));

vi.mock('../composables/useSessionNotifications', () => ({
  useSessionNotifications: () => ({
    onSessionUpdated: vi.fn(),
  }),
}));

vi.mock('../composables/usePendingChat', () => ({
  consumePendingChat: vi.fn(),
}));

vi.mock('../composables/useSettingsDialog', () => ({
  useSettingsDialog: () => ({
    isSettingsDialogOpen: ref(false),
    openSettingsDialog: vi.fn(),
  }),
}));

vi.mock('../utils/toast', () => ({
  showErrorToast: vi.fn(),
  showSuccessToast: vi.fn(),
}));

vi.mock('../utils/dom', () => ({
  copyToClipboard: vi.fn(),
}));

type ChatPageTestApi = {
  handleEvent: (event: AgentSSEEvent) => void;
  replayHistoryEvents: (events: AgentSSEEvent[]) => boolean;
  flushPendingMessageChunks: () => void;
  getState: () => {
    messages: any[];
    realTime: boolean;
    activityItems: any[];
    activitySnapshots: Array<{ items: any[]; plan: any }>;
    plan: any;
    pendingSkillSave: string | null;
    pendingToolSave: string | null;
    isReplayingHistory: boolean;
  };
};

const mountChatPage = () => {
  const wrapper = shallowMount(ChatPage, {
    global: {
      stubs: {
        SimpleBar: {
          template: '<div><slot /></div>',
          methods: {
            scrollToBottom: vi.fn(),
            scrollToElement: vi.fn(),
          },
        },
        ChatBox: true,
        ChatMessage: true,
        ActivityPanel: {
          template: '<div />',
          methods: {
            show: vi.fn(),
            hide: vi.fn(),
          },
        },
        ToolPanel: true,
        ChatTimeline: true,
        LoadingIndicator: true,
        SessionPasswordDialog: true,
        VerifySessionPasswordDialog: true,
        Popover: { template: '<div><slot /></div>' },
        PopoverContent: { template: '<div><slot /></div>' },
        PopoverTrigger: { template: '<div><slot /></div>' },
        ShareIcon: true,
      },
    },
  });

  return (wrapper.vm as unknown as { __test: ChatPageTestApi }).__test;
};

const createRoundEvents = (): AgentSSEEvent[] => [
  {
    event: 'message',
    data: {
      event_id: 'evt-user',
      timestamp: 1,
      role: 'user',
      content: 'Run analysis',
      attachments: [],
    },
  },
  {
    event: 'plan',
    data: {
      event_id: 'evt-plan',
      timestamp: 2,
      steps: [{
        event_id: 'evt-step-plan',
        timestamp: 2,
        id: 'step-1',
        description: 'Search data',
        status: 'running',
        tools: [],
      }],
    },
  },
  {
    event: 'step',
    data: {
      event_id: 'evt-step-running',
      timestamp: 3,
      id: 'step-1',
      description: 'Search data',
      status: 'running',
      tools: [],
    },
  },
  {
    event: 'tool',
    data: {
      event_id: 'evt-tool',
      timestamp: 4,
      tool_call_id: 'call-1',
      name: 'search_tool',
      function: 'search_tool',
      status: 'called',
      args: { query: 'science' },
      content: { result: 'ok' },
    },
  },
  {
    event: 'message_chunk',
    data: {
      event_id: 'evt-chunk-1',
      timestamp: 5,
      role: 'assistant',
      content: 'Hello ',
    },
  },
  {
    event: 'message_chunk',
    data: {
      event_id: 'evt-chunk-2',
      timestamp: 6,
      role: 'assistant',
      content: 'world',
    },
  },
  {
    event: 'message_chunk_done',
    data: {
      event_id: 'evt-chunk-done',
      timestamp: 7,
    },
  },
  {
    event: 'done',
    data: {
      event_id: 'evt-done',
      timestamp: 8,
      statistics: {
        total_duration_ms: 123,
        tool_call_count: 1,
      },
      round_files: [{
        file_id: 'file-1',
        filename: 'result.csv',
        relative_path: 'result.csv',
        size: 10,
        upload_date: '2026-06-06T00:00:00Z',
        file_url: '/files/result.csv',
        category: 'output',
      }],
    },
  },
];

describe('ChatPage history replay batching', () => {
  beforeEach(() => {
    vi.useRealTimers();
  });

  it('keeps handleEvent semantics while replaying history into one final messages assignment', () => {
    const events = createRoundEvents();
    const live = mountChatPage();
    const replay = mountChatPage();

    events.forEach(event => live.handleEvent(event));
    live.flushPendingMessageChunks();

    expect(replay.replayHistoryEvents(events)).toBe(true);

    const liveState = live.getState();
    const replayState = replay.getState();

    expect(replayState.messages).toEqual(liveState.messages);
    expect(replayState.messages[replayState.messages.length - 1]).toMatchObject({
      type: 'assistant',
      content: {
        content: 'Hello world',
        statistics: {
          total_duration_ms: 123,
          tool_call_count: 1,
        },
        round_files: [{
          file_id: 'file-1',
          filename: 'result.csv',
        }],
      },
    });
    expect(replayState.activitySnapshots).toHaveLength(1);
    expect(replayState.activitySnapshots[0].items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          type: 'tool',
          tool: expect.objectContaining({ tool_call_id: 'call-1' }),
        }),
      ]),
    );
    expect(replayState.activitySnapshots[0].plan.steps[0].tools).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ tool_call_id: 'call-1' }),
      ]),
    );
    expect(replayState.plan).toBeUndefined();
    expect(replayState.realTime).toBe(true);
    expect(replayState.isReplayingHistory).toBe(false);
  });

  it('does not enter replay mode for realtime SSE events', () => {
    const page = mountChatPage();

    page.handleEvent({
      event: 'message',
      data: {
        event_id: 'evt-live-user',
        timestamp: 1,
        role: 'user',
        content: 'Live message',
        attachments: [],
      },
    });

    const state = page.getState();
    expect(state.isReplayingHistory).toBe(false);
    expect(state.realTime).toBe(true);
    expect(state.messages).toEqual([
      expect.objectContaining({
        type: 'user',
        content: expect.objectContaining({ content: 'Live message' }),
      }),
    ]);
  });
});

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { shallowMount, type VueWrapper } from '@vue/test-utils';
import { nextTick, ref } from 'vue';

import ChatPage from './ChatPage.vue';
import type { AgentSSEEvent } from '../types/event';
import * as agentApi from '../api/agent';
import { SessionStatus } from '../types/response';

const currentRoute = ref<{ params: { sessionId?: string } }>({ params: {} });
const routerReplace = vi.fn();
const mountedWrappers: VueWrapper[] = [];

vi.mock('vue-router', () => ({
  createRouter: () => ({
    beforeEach: vi.fn(),
    push: vi.fn(),
    replace: vi.fn(),
    install: vi.fn(),
  }),
  createWebHistory: vi.fn(),
  useRouter: () => ({
    currentRoute,
    replace: routerReplace,
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
  lockSessionPassword: vi.fn().mockResolvedValue({ locked: true }),
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
  resetSessionRuntimeState: () => void;
  setSessionRuntimeForTest: (nextState: {
    cancelCurrentChat?: (() => void) | null;
    sessionHasPassword?: boolean;
    shareMode?: 'private' | 'public';
    showVerifyPasswordDialog?: boolean;
    activitySnapshots?: Array<{ items: any[]; plan: any }>;
    pendingSkillSave?: string | null;
    pendingToolSave?: string | null;
    lastTurnHadError?: boolean;
    searchQuery?: string;
  }) => void;
  getState: () => {
    sessionId: string | undefined;
    messages: any[];
    realTime: boolean;
    isLoading: boolean;
    title: string;
    shareMode: 'private' | 'public';
    activityItems: any[];
    activitySnapshots: Array<{ items: any[]; plan: any }>;
    plan: any;
    sessionHasPassword: boolean;
    showVerifyPasswordDialog: boolean;
    pendingSkillSave: string | null;
    pendingToolSave: string | null;
    isReplayingHistory: boolean;
    lastTurnHadError: boolean;
    sessionSearchQuery: string;
    isSessionSearchOpen: boolean;
  };
};

const mountChatPageWrapper = () => {
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

  mountedWrappers.push(wrapper);
  return wrapper;
};

const mountChatPage = () => {
  const wrapper = mountChatPageWrapper();
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

afterEach(() => {
  mountedWrappers.splice(0).forEach(wrapper => wrapper.unmount());
});

describe('ChatPage history replay batching', () => {
  beforeEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
    vi.mocked(agentApi.lockSessionPassword).mockResolvedValue({ locked: true });
    currentRoute.value = { params: {} };
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

describe('ChatPage route session reuse', () => {
  beforeEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
    vi.mocked(agentApi.lockSessionPassword).mockResolvedValue({ locked: true });
    currentRoute.value = { params: { sessionId: 'session-a' } };
    vi.mocked(agentApi.getSession).mockResolvedValue({
      session_id: 'session-a',
      title: 'Session A',
      status: SessionStatus.COMPLETED,
      events: [],
      is_shared: true,
      mode: 'deep',
      model_config_id: null,
      selected_skill_names: [],
      has_password: true,
      locked: false,
    });
  });

  it('reuses ChatPage on sessionId change, cancels old SSE, locks password session, and resets old state', async () => {
    const wrapper = mountChatPageWrapper();
    const page = (wrapper.vm as unknown as { __test: ChatPageTestApi }).__test;
    await nextTick();
    await Promise.resolve();

    page.handleEvent({
      event: 'message',
      data: {
        event_id: 'evt-old-user',
        timestamp: 1,
        role: 'user',
        content: 'old message',
        attachments: [],
      },
    });
    page.handleEvent({
      event: 'done',
      data: {
        event_id: 'evt-old-done',
        timestamp: 2,
      },
    });

    const cancelOldSse = vi.fn();
    page.setSessionRuntimeForTest({
      cancelCurrentChat: cancelOldSse,
      sessionHasPassword: true,
      shareMode: 'public',
      showVerifyPasswordDialog: true,
      activitySnapshots: [{ items: [{ id: 'old-activity', type: 'thinking' }], plan: undefined }],
      pendingSkillSave: 'old-skill',
      pendingToolSave: 'old-tool',
      lastTurnHadError: true,
      searchQuery: 'old',
    });

    vi.mocked(agentApi.getSession).mockResolvedValueOnce({
      session_id: 'session-b',
      title: 'Session B',
      status: SessionStatus.COMPLETED,
      events: [{
        event: 'message',
        data: {
          event_id: 'evt-new-user',
          timestamp: 10,
          role: 'user',
          content: 'new message',
          attachments: [],
        },
      }],
      is_shared: false,
      mode: 'deep',
      model_config_id: null,
      selected_skill_names: [],
      has_password: false,
      locked: false,
    });

    const unmountedBeforeSwitch = wrapper.emitted();
    currentRoute.value = { params: { sessionId: 'session-b' } };
    await nextTick();
    await Promise.resolve();
    await nextTick();

    expect(wrapper.exists()).toBe(true);
    expect(wrapper.emitted()).toEqual(unmountedBeforeSwitch);
    expect(cancelOldSse).toHaveBeenCalledOnce();
    expect(agentApi.lockSessionPassword).toHaveBeenCalledWith('session-a');
    expect(agentApi.getSession).toHaveBeenLastCalledWith('session-b');

    const state = page.getState();
    expect(state.sessionId).toBe('session-b');
    expect(state.title).toBe('Session B');
    expect(state.shareMode).toBe('private');
    expect(state.sessionHasPassword).toBe(false);
    expect(state.showVerifyPasswordDialog).toBe(false);
    expect(state.activitySnapshots).toHaveLength(0);
    expect(state.pendingSkillSave).toBeNull();
    expect(state.pendingToolSave).toBeNull();
    expect(state.lastTurnHadError).toBe(false);
    expect(state.sessionSearchQuery).toBe('');
    expect(state.isSessionSearchOpen).toBe(false);
    expect(state.messages).toEqual([
      expect.objectContaining({
        type: 'user',
        content: expect.objectContaining({ content: 'new message' }),
      }),
    ]);
  });
});

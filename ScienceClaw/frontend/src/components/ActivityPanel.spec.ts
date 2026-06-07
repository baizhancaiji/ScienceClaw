import { mount } from '@vue/test-utils';
import { createI18n } from 'vue-i18n';
import { defineComponent, nextTick, ref } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import ActivityPanel from './ActivityPanel.vue';

type Listener = (event: MessageEvent) => void;

class MockBroadcastChannel {
  static channels = new Map<string, Set<MockBroadcastChannel>>();

  readonly listeners = new Set<Listener>();

  constructor(public readonly name: string) {
    const channelSet = MockBroadcastChannel.channels.get(name) ?? new Set<MockBroadcastChannel>();
    channelSet.add(this);
    MockBroadcastChannel.channels.set(name, channelSet);
  }

  postMessage(data: unknown) {
    const peers = MockBroadcastChannel.channels.get(this.name) ?? new Set<MockBroadcastChannel>();
    for (const peer of peers) {
      if (peer === this) {
        continue;
      }
      for (const listener of peer.listeners) {
        listener({ data } as MessageEvent);
      }
    }
  }

  addEventListener(_type: 'message', listener: Listener) {
    this.listeners.add(listener);
  }

  removeEventListener(_type: 'message', listener: Listener) {
    this.listeners.delete(listener);
  }

  close() {
    MockBroadcastChannel.channels.get(this.name)?.delete(this);
    this.listeners.clear();
  }

  static reset() {
    MockBroadcastChannel.channels.clear();
  }
}

vi.mock('../composables/useResizeObserver', () => ({
  useResizeObserver: () => ({
    size: ref(400),
  }),
}));

vi.mock('./SandboxPreview.vue', () => ({
  default: defineComponent({
    name: 'SandboxPreviewStub',
    props: {
      history: {
        type: Array,
        default: () => [],
      },
      mode: {
        type: String,
        default: 'none',
      },
      isLive: {
        type: Boolean,
        default: false,
      },
    },
    template: '<div class="sandbox-preview-stub" :data-history-length="String(history.length)" :data-mode="mode" :data-live="String(isLive)" />',
  }),
}));

const makeToolItem = (id: string, status: 'calling' | 'called', output?: string) => ({
  id,
  type: 'tool' as const,
  timestamp: 1,
  tool: {
    timestamp: 1,
    tool_call_id: id,
    function: 'execute',
    name: 'execute',
    status,
    args: {
      command: `echo ${id}`,
    },
    content: output ? { stdout: output } : undefined,
    tool_meta: {
      icon: '>',
      category: 'sandbox',
      description: 'Sandbox execute',
      sandbox: true,
    },
  },
});

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: { en: {} },
  missingWarn: false,
  fallbackWarn: false,
});

describe('ActivityPanel sandbox history channel', () => {
  beforeEach(() => {
    MockBroadcastChannel.reset();
    vi.stubGlobal('BroadcastChannel', MockBroadcastChannel);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    MockBroadcastChannel.reset();
  });

  it('responds to snapshot requests and broadcasts incrementals on the bound session channel', async () => {
    const wrapper = mount(ActivityPanel, {
      props: {
        sessionId: 'session-a',
        items: [
          makeToolItem('call-1', 'calling'),
          makeToolItem('call-1', 'called', 'first output'),
        ],
        isLoading: false,
      },
      global: {
        plugins: [i18n],
        stubs: {
          LoadingSpinnerIcon: true,
          XIcon: true,
          ChevronRightIcon: true,
          ZapIcon: true,
          Lightbulb: true,
          ListChecks: true,
          WrenchIcon: true,
        },
      },
    });
    await nextTick();

    const external = new MockBroadcastChannel('sandbox-history:session-a');
    const received: unknown[] = [];
    external.addEventListener('message', (event) => {
      received.push(event.data);
    });

    external.postMessage({
      type: 'request-snapshot',
      sessionId: 'session-a',
    });
    await nextTick();

    expect(received).toContainEqual({
      type: 'snapshot',
      sessionId: 'session-a',
      entries: [
        { toolName: 'execute', command: 'echo call-1', status: 'calling' },
        { toolName: 'execute', command: 'echo call-1', output: 'first output', status: 'called' },
      ],
    });

    await wrapper.setProps({
      items: [
        makeToolItem('call-1', 'calling'),
        makeToolItem('call-1', 'called', 'first output'),
        makeToolItem('call-2', 'calling'),
      ],
    });
    await nextTick();

    expect(received).toContainEqual({
      type: 'incremental',
      sessionId: 'session-a',
      entry: {
        toolName: 'execute',
        command: 'echo call-2',
        status: 'calling',
      },
    });
  });

  it('does NOT respond to snapshot requests when sandboxHistory is empty', async () => {
    const wrapper = mount(ActivityPanel, {
      props: {
        sessionId: 'session-empty',
        items: [],
        isLoading: false,
      },
      global: {
        plugins: [i18n],
        stubs: {
          LoadingSpinnerIcon: true,
          XIcon: true,
          ChevronRightIcon: true,
          ZapIcon: true,
          Lightbulb: true,
          ListChecks: true,
          WrenchIcon: true,
        },
      },
    });
    await nextTick();

    const external = new MockBroadcastChannel('sandbox-history:session-empty');
    const received: unknown[] = [];
    external.addEventListener('message', (event) => {
      received.push(event.data);
    });

    external.postMessage({
      type: 'request-snapshot',
      sessionId: 'session-empty',
    });
    await nextTick();

    expect(received).toEqual([]);
  });
});

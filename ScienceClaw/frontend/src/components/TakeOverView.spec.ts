import { mount } from '@vue/test-utils';
import { createI18n } from 'vue-i18n';
import { defineComponent, nextTick, reactive } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const route = reactive<{
  params: { sessionId?: string | string[] };
  query: Record<string, unknown>;
}>({
  params: {},
  query: {},
});

vi.mock('vue-router', () => ({
  createRouter: () => ({
    beforeEach: vi.fn(),
    push: vi.fn(),
    replace: vi.fn(),
    install: vi.fn(),
  }),
  createWebHistory: vi.fn(),
  useRoute: () => route,
}));

vi.mock('vue-gtag', () => ({
  configure: vi.fn(),
  default: {
    install: vi.fn(),
  },
}));

const VNCViewerStub = defineComponent({
  name: 'VNCViewerStub',
  props: {
    sessionId: {
      type: String,
      required: true,
    },
    enabled: {
      type: Boolean,
      default: false,
    },
    viewOnly: {
      type: Boolean,
      default: false,
    },
  },
  template: `
    <div
      class="vnc-viewer-stub"
      :data-session-id="sessionId"
      :data-enabled="String(enabled)"
      :data-view-only="String(viewOnly)"
    />
  `,
});

vi.mock('./VNCViewer.vue', () => ({
  default: VNCViewerStub,
}));

const SandboxTerminalStub = defineComponent({
  name: 'SandboxTerminalStub',
  props: {
    active: {
      type: Boolean,
      default: false,
    },
    history: {
      type: Array,
      default: () => [],
    },
  },
  template: `
    <div
      class="sandbox-terminal-stub"
      :data-active="String(active)"
      :data-history-length="String(history.length)"
    />
  `,
});

vi.mock('./SandboxTerminal.vue', () => ({
  default: SandboxTerminalStub,
}));

const { default: TakeOverView } = await import('./TakeOverView.vue');

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      Sandbox: 'Sandbox',
      Terminal: 'Terminal',
      Browser: 'Browser',
      'Exit Takeover': 'Exit Takeover',
      'Browser View Only': 'Browser View Only',
      'Enable Browser Control': 'Enable Browser Control',
      'Disable Browser Control': 'Disable Browser Control',
    },
  },
});

const mountTakeOverView = () => mount(TakeOverView, {
  global: {
    plugins: [i18n],
  },
});

describe('TakeOverView', () => {
  beforeEach(() => {
    route.params = {};
    route.query = {};
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('shows takeover for direct sandbox routes and toggles browser control mode', async () => {
    route.params = { sessionId: 'session-sandbox' };
    route.query = { sandbox: '1' };

    const wrapper = mountTakeOverView();
    await nextTick();

    const viewer = wrapper.get('.vnc-viewer-stub');
    expect(viewer.attributes('data-session-id')).toBe('session-sandbox');
    expect(viewer.attributes('data-enabled')).toBe('true');
    expect(viewer.attributes('data-view-only')).toBe('true');

    await wrapper.get('[data-testid="takeover-browser-control-toggle"]').trigger('click');

    expect(wrapper.get('.vnc-viewer-stub').attributes('data-view-only')).toBe('false');

    await wrapper.get('[data-testid="takeover-tab-terminal"]').trigger('click');

    expect(wrapper.find('.vnc-viewer-stub').exists()).toBe(false);
    expect(wrapper.get('.sandbox-terminal-stub').attributes('data-active')).toBe('true');
  });

  it('keeps vnc direct entry compatibility', async () => {
    route.params = { sessionId: 'session-vnc' };
    route.query = { vnc: '1' };

    const wrapper = mountTakeOverView();
    await nextTick();

    expect(wrapper.get('.vnc-viewer-stub').attributes('data-session-id')).toBe('session-vnc');
    expect(wrapper.text()).toContain('Exit Takeover');
  });

  it('binds the takeover session from the event and does not drift with later route changes', async () => {
    const wrapper = mountTakeOverView();
    await nextTick();

    window.dispatchEvent(new CustomEvent('takeover', {
      detail: {
        active: true,
        sessionId: 'event-session',
      },
    }));
    await nextTick();

    expect(wrapper.get('.vnc-viewer-stub').attributes('data-session-id')).toBe('event-session');

    route.params = { sessionId: 'different-session' };
    route.query = { sandbox: '1' };
    await nextTick();

    expect(wrapper.get('.vnc-viewer-stub').attributes('data-session-id')).toBe('event-session');
  });
});

import { mount } from '@vue/test-utils';
import { createI18n } from 'vue-i18n';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import SandboxPreview from './SandboxPreview.vue';
import { SANDBOX_TAKEOVER_EVENT } from '@/utils/sandboxTakeoverState';

vi.mock('@/utils/sandbox', () => ({
  getSandboxVncUrl: () => 'http://sandbox.local/vnc/index.html',
}));

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      'Sandbox': 'Sandbox',
      'Terminal': 'Terminal',
      'Browser': 'Browser',
      'Take Over': 'Take Over',
      'Sandbox Taken Over': 'Taken Over',
    },
  },
  missingWarn: false,
  fallbackWarn: false,
});

describe('SandboxPreview takeover entry', () => {
  beforeEach(() => {
    vi.spyOn(window, 'open').mockImplementation(() => null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows an always-visible takeover button on the same header row as the tabs and opens a new takeover tab', async () => {
    const wrapper = mount(SandboxPreview, {
      props: {
        mode: 'browser',
        isLive: true,
        sessionId: 'session-a',
        history: [],
      },
      global: {
        plugins: [i18n],
        stubs: {
          SandboxTerminal: {
            template: '<div class="sandbox-terminal-stub" />',
          },
          ChevronRightIcon: true,
          MonitorIcon: true,
          XIcon: true,
        },
      },
    });

    const buttons = wrapper.findAll('button');
    const takeoverButton = buttons.find((button) => button.text().includes('Take Over'));

    expect(takeoverButton).toBeTruthy();

    await takeoverButton!.trigger('click');

    expect(window.open).toHaveBeenCalledWith('/chat/session-a?sandbox=1', '_blank', 'noopener');
  });

  it('keeps the sandbox card mounted without a close button and reflects takeover status', async () => {
    const wrapper = mount(SandboxPreview, {
      props: {
        mode: 'browser',
        isLive: false,
        sessionId: 'session-b',
        history: [],
      },
      global: {
        plugins: [i18n],
        stubs: {
          SandboxTerminal: {
            template: '<div class="sandbox-terminal-stub" />',
          },
          ChevronRightIcon: true,
          MonitorIcon: true,
        },
      },
    });

    expect(wrapper.text()).toContain('Sandbox');
    expect(wrapper.text()).not.toContain('Close');
    expect(wrapper.text()).not.toContain('Taken Over');

    window.dispatchEvent(new CustomEvent(SANDBOX_TAKEOVER_EVENT, {
      detail: {
        sessionId: 'session-b',
        active: true,
      },
    }));

    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Taken Over');
  });
});

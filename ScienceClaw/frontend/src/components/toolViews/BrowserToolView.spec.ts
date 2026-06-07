import { mount } from '@vue/test-utils';
import { createI18n } from 'vue-i18n';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import BrowserToolView from './BrowserToolView.vue';
import type { ToolContent } from '@/types/message';

vi.mock('@/utils/sandbox', () => ({
  getSandboxVncUrl: () => 'http://sandbox.local/vnc/index.html',
}));

vi.mock('@/components/icons/TakeOverIcon.vue', () => ({
  default: {
    name: 'TakeOverIconStub',
    template: '<span class="takeover-icon-stub" />',
  },
}));

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      'Take Over': 'Take Over',
    },
  },
  missingWarn: false,
  fallbackWarn: false,
});

const toolContent: ToolContent = {
  timestamp: 1,
  tool_call_id: 'tool-1',
  name: 'browser_view',
  function: 'browser_view',
  args: {
    url: 'https://example.com',
  },
  status: 'called',
  content: {
    screenshot: 'https://example.com/screenshot.png',
  },
};

describe('BrowserToolView', () => {
  beforeEach(() => {
    vi.spyOn(window, 'open').mockImplementation(() => null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('opens the bound sandbox takeover page in a new tab', async () => {
    const wrapper = mount(BrowserToolView, {
      props: {
        sessionId: 'session-a',
        toolContent,
        live: false,
        isShare: false,
      },
      global: {
        plugins: [i18n],
      },
    });

    await wrapper.get('button').trigger('click');

    expect(window.open).toHaveBeenCalledWith('/chat/session-a?sandbox=1', '_blank', 'noopener');
  });
});

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
      'Browser': 'Browser',
      'Browser Preview Image': 'Browser Preview Image',
      'No screenshot available': 'No screenshot available',
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

const toolContentWithoutPreview: ToolContent = {
  timestamp: 2,
  tool_call_id: 'tool-2',
  name: 'browser_view',
  function: 'browser_view',
  args: {},
  status: 'called',
  content: {},
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

  it('renders translated fallback browser strings for empty previews', () => {
    const wrapper = mount(BrowserToolView, {
      props: {
        sessionId: 'session-a',
        toolContent: toolContentWithoutPreview,
        live: false,
        isShare: false,
      },
      global: {
        plugins: [i18n],
      },
    });

    expect(wrapper.text()).toContain('Browser');
    expect(wrapper.text()).toContain('No screenshot available');
  });
});

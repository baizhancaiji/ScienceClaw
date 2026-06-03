import { mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import ChatMessage from './ChatMessage.vue';
import type { Message, MessageContent } from '../types/message';

const mermaidRendererCalls = vi.hoisted(() => [] as Array<{ autoRender?: boolean }>);

vi.mock('../composables/useMermaidRenderer', () => ({
  useMermaidRenderer: (options: { autoRender?: boolean }) => {
    mermaidRendererCalls.push({ autoRender: options.autoRender });
    return {
      createMermaidPlaceholderId: () => 'mermaid-test',
      scheduleRenderMermaidDiagrams: vi.fn(),
    };
  },
}));

vi.mock('../composables/useTime', () => ({
  useRelativeTime: () => ({
    relativeTime: () => '刚刚',
  }),
}));

const mermaidContent = ['```mermaid', 'graph TD; A-->B;', '```'].join('\n');

const mountMessage = (type: 'user' | 'assistant') => mount(ChatMessage, {
  props: {
    message: {
      type,
      content: {
        timestamp: Date.now(),
        content: mermaidContent,
      } as MessageContent,
    } satisfies Message,
  },
  global: {
    stubs: {
      AttachmentsMessage: true,
      ImageViewer: true,
      HtmlViewer: true,
      MoleculeViewer: true,
      SuggestedQuestions: true,
      MarkdownEnhancements: true,
      MessageFooter: true,
      RobotAvatar: true,
    },
  },
});

describe('ChatMessage markdown rendering', () => {
  beforeEach(() => {
    mermaidRendererCalls.length = 0;
  });

  it('displays user messages as plain text (no markdown rendering)', () => {
    const wrapper = mountMessage('user');

    // 用户消息应以纯文本显示，不渲染 Markdown/Mermaid
    expect(wrapper.find('.msg-enter-right .code-block-wrapper').exists()).toBe(false);
    expect(wrapper.find('.msg-enter-right .mermaid-wrapper').exists()).toBe(false);
    // 用户消息不使用 useMermaidRenderer（autoRender 为 false + 不传 getContent）
    expect(mermaidRendererCalls).toEqual([{ autoRender: false }]);
    // 纯文本内容应原样显示（mermaid 代码块标记不应该被渲染）
    expect(wrapper.find('.msg-enter-right').text()).toContain('```mermaid');
  });

  it('renders mermaid fences in assistant messages as diagram placeholders', () => {
    const wrapper = mountMessage('assistant');

    expect(wrapper.find('.msg-enter-left .mermaid-wrapper').exists()).toBe(true);
    expect(wrapper.find('.msg-enter-left .code-block-wrapper').exists()).toBe(false);
    expect(mermaidRendererCalls).toEqual([{ autoRender: true }]);
  });
});

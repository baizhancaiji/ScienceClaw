import { mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createI18n } from 'vue-i18n';

import ChatMessage from './ChatMessage.vue';
import type { Message, MessageContent } from '../types/message';

const mermaidRendererCalls = vi.hoisted(() => [] as Array<{ autoRender?: boolean }>);
const pdfExportMock = vi.hoisted(() => ({
  exporting: { value: false },
  exportPdf: vi.fn(),
}));

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

vi.mock('../composables/usePdfExport', () => ({
  usePdfExport: () => pdfExportMock,
}));

vi.mock('../utils/toast', () => ({
  showErrorToast: vi.fn(),
}));

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: {
      'Collapse message': '折叠消息',
      'Expand message': '展开消息',
      'Message collapsed': '消息已折叠',
      'pdf_export.action': '导出 PDF',
      'pdf_export.unavailable': '当前消息无法导出 PDF',
    },
  },
});

const mermaidContent = ['```mermaid', 'graph TD; A-->B;', '```'].join('\n');

const mountMessage = (type: 'user' | 'assistant', props: Record<string, unknown> = {}) => mount(ChatMessage, {
  props: {
    message: {
      type,
      content: {
        timestamp: Date.now(),
        content: mermaidContent,
      } as MessageContent,
    } satisfies Message,
    ...props,
  },
  global: {
    plugins: [i18n],
    stubs: {
      AttachmentsMessage: true,
      ImageViewer: true,
      HtmlViewer: true,
      MoleculeViewer: true,
      SuggestedQuestions: true,
      MarkdownEnhancements: true,
      RobotAvatar: true,
    },
  },
});

describe('ChatMessage markdown rendering', () => {
  beforeEach(() => {
    mermaidRendererCalls.length = 0;
    pdfExportMock.exportPdf.mockReset();
    pdfExportMock.exporting.value = false;
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

  it('exports assistant markdown DOM through the pdf composable', async () => {
    const wrapper = mountMessage('assistant', { sessionId: 'session-1' });

    await wrapper.find('button[aria-label="导出 PDF"]').trigger('click');

    expect(pdfExportMock.exportPdf).toHaveBeenCalledTimes(1);
    const [sessionId, markdownEl, locale] = pdfExportMock.exportPdf.mock.calls[0];
    expect(sessionId).toBe('session-1');
    expect(markdownEl).toBe(wrapper.find('.markdown-content').element);
    expect(locale).toBe('zh');
  });
});

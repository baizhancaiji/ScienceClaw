import { mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createI18n } from 'vue-i18n';

import ChatMessage from './ChatMessage.vue';
import type { Message, MessageContent } from '../types/message';

const mermaidRendererCalls = vi.hoisted(() => [] as Array<{ autoRender?: boolean }>);
const pdfExportMock = vi.hoisted(() => ({
  exporting: { value: false },
  exportPdf: vi.fn(),
}));
const markdownEnhancementExposeMock = vi.hoisted(() => ({
  openLightbox: vi.fn(),
  closeLightbox: vi.fn(),
  openCodeFullscreen: vi.fn(),
  closeCodeFullscreen: vi.fn(),
  openMermaidFullscreen: vi.fn(),
  closeMermaidFullscreen: vi.fn(),
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

vi.mock('./MarkdownEnhancements.vue', () => ({
  default: {
    name: 'MarkdownEnhancements',
    template: '<div class="markdown-enhancements-stub"></div>',
    setup: () => markdownEnhancementExposeMock,
  },
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
      'mermaid.toolbar': 'Mermaid 图表工具',
      'mermaid.fullscreen': '全屏查看',
      'mermaid.copy_source': '复制源码',
      'mermaid.download_svg': '下载 SVG',
      'mermaid.close_fullscreen': '关闭全屏',
      'mermaid.zoom_in': '放大图表',
      'mermaid.zoom_out': '缩小图表',
      'mermaid.reset_zoom': '重置缩放',
      'mermaid.show_source': '显示源码',
      'mermaid.copy_source_success': 'Mermaid 源码已复制',
      'mermaid.copy_source_failed': '复制 Mermaid 源码失败',
      'mermaid.download_svg_success': 'Mermaid SVG 已开始下载',
      'mermaid.download_svg_failed': '下载 Mermaid SVG 失败',
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
      RobotAvatar: true,
    },
  },
});

describe('ChatMessage markdown rendering', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    mermaidRendererCalls.length = 0;
    pdfExportMock.exportPdf.mockReset();
    pdfExportMock.exporting.value = false;
    markdownEnhancementExposeMock.openLightbox.mockReset();
    markdownEnhancementExposeMock.openCodeFullscreen.mockReset();
    markdownEnhancementExposeMock.openMermaidFullscreen.mockReset();
    Object.defineProperty(window.navigator, 'clipboard', {
      configurable: true,
      value: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
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

  it('renders Mermaid toolbar actions for assistant diagrams', () => {
    const wrapper = mountMessage('assistant');

    expect(wrapper.find('[data-mermaid-action="fullscreen"]').exists()).toBe(true);
    expect(wrapper.find('[data-mermaid-action="copy-source"]').exists()).toBe(true);
    expect(wrapper.find('[data-mermaid-action="download-svg"]').exists()).toBe(true);
    expect(wrapper.find('[data-mermaid-action="zoom-in"]').exists()).toBe(true);
    expect(wrapper.find('[data-mermaid-action="zoom-out"]').exists()).toBe(true);
    expect(wrapper.find('[data-mermaid-action="reset-zoom"]').exists()).toBe(true);
    expect(wrapper.find('[data-mermaid-action="toggle-source"]').exists()).toBe(true);
    expect(wrapper.find('.mermaid-scale-indicator').text()).toBe('100%');
  });

  it('updates the Mermaid scale indicator and transform on zoom actions', async () => {
    const wrapper = mountMessage('assistant');
    const transformLayer = wrapper.find('.mermaid-transform-layer').element as HTMLElement;

    await wrapper.find('[data-mermaid-action="zoom-in"]').trigger('click');

    expect(wrapper.find('.mermaid-scale-indicator').text()).toBe('125%');
    expect(transformLayer.style.transform).toContain('scale(1.25)');

    await wrapper.find('[data-mermaid-action="zoom-out"]').trigger('click');

    expect(wrapper.find('.mermaid-scale-indicator').text()).toBe('100%');
    expect(transformLayer.style.transform).toContain('scale(1)');
  });

  it('resets Mermaid zoom and offset through the reset action', async () => {
    const wrapper = mountMessage('assistant');
    const viewport = wrapper.find('.mermaid-viewport');
    const transformLayer = wrapper.find('.mermaid-transform-layer').element as HTMLElement;

    await wrapper.find('[data-mermaid-action="zoom-in"]').trigger('click');
    await viewport.trigger('pointerdown', {
      pointerId: 1,
      clientX: 100,
      clientY: 120,
    });
    await viewport.trigger('pointermove', {
      pointerId: 1,
      clientX: 140,
      clientY: 150,
    });
    await viewport.trigger('pointerup', {
      pointerId: 1,
      clientX: 140,
      clientY: 150,
    });

    expect(transformLayer.style.transform).toContain('translate(40px, 30px) scale(1.25)');

    await wrapper.find('[data-mermaid-action="reset-zoom"]').trigger('click');

    expect(wrapper.find('.mermaid-scale-indicator').text()).toBe('100%');
    expect(transformLayer.style.transform).toBe('translate(0px, 0px) scale(1)');
  });

  it('only allows Mermaid dragging after zooming in', async () => {
    const wrapper = mountMessage('assistant');
    const viewport = wrapper.find('.mermaid-viewport');
    const transformLayer = wrapper.find('.mermaid-transform-layer').element as HTMLElement;

    await viewport.trigger('pointerdown', {
      pointerId: 3,
      clientX: 80,
      clientY: 90,
    });
    await viewport.trigger('pointermove', {
      pointerId: 3,
      clientX: 120,
      clientY: 130,
    });

    expect(transformLayer.style.transform).toBe('');

    await wrapper.find('[data-mermaid-action="zoom-in"]').trigger('click');
    await viewport.trigger('pointerdown', {
      pointerId: 3,
      clientX: 80,
      clientY: 90,
    });
    await viewport.trigger('pointermove', {
      pointerId: 3,
      clientX: 120,
      clientY: 130,
    });
    await viewport.trigger('pointerup', {
      pointerId: 3,
      clientX: 120,
      clientY: 130,
    });

    expect(transformLayer.style.transform).toContain('translate(40px, 40px) scale(1.25)');
  });

  it('copies Mermaid source through the markdown action toolbar', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(window.navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    });
    const wrapper = mountMessage('assistant');

    await wrapper.find('[data-mermaid-action="copy-source"]').trigger('click');

    expect(writeText).toHaveBeenCalledWith('graph TD; A-->B;');
    const feedback = wrapper.find('.mermaid-feedback');
    expect(feedback.attributes('data-status')).toBe('success');
    expect(feedback.text()).toBe('Mermaid 源码已复制');
    expect((feedback.element as HTMLElement).hidden).toBe(false);
  });

  it('toggles the Mermaid source panel without changing the copied payload', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(window.navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    });
    const wrapper = mountMessage('assistant');
    const sourcePanel = wrapper.find('[data-mermaid-source-panel]').element as HTMLElement;
    const viewport = wrapper.find('.mermaid-viewport').element as HTMLElement;

    expect(sourcePanel.hidden).toBe(true);
    expect(sourcePanel.textContent).toBe('graph TD; A-->B;');
    expect(viewport.hidden).toBe(false);

    await wrapper.find('[data-mermaid-action="toggle-source"]').trigger('click');
    expect(sourcePanel.hidden).toBe(false);
    expect(wrapper.find('.mermaid-wrapper').attributes('data-mermaid-source-open')).toBe('true');
    expect(viewport.hidden).toBe(true);

    await wrapper.find('[data-mermaid-action="copy-source"]').trigger('click');
    expect(writeText).toHaveBeenCalledWith('graph TD; A-->B;');
  });

  it('shows error feedback when copying Mermaid source fails', async () => {
    const writeText = vi.fn().mockRejectedValue(new Error('clipboard denied'));
    Object.defineProperty(window.navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    });
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const wrapper = mountMessage('assistant');

    await wrapper.find('[data-mermaid-action="copy-source"]').trigger('click');

    expect(errorSpy).toHaveBeenCalled();
    const feedback = wrapper.find('.mermaid-feedback');
    expect(feedback.attributes('data-status')).toBe('error');
    expect(feedback.text()).toBe('复制 Mermaid 源码失败');
  });

  it('shows error feedback when downloading Mermaid SVG fails', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const createObjectUrlSpy = vi.spyOn(URL, 'createObjectURL').mockImplementation(() => {
      throw new Error('blob failure');
    });
    const wrapper = mountMessage('assistant');
    const mermaidContent = wrapper.find('.mermaid-content').element as HTMLElement;
    mermaidContent.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg"><g></g></svg>';

    await wrapper.find('[data-mermaid-action="download-svg"]').trigger('click');

    expect(createObjectUrlSpy).toHaveBeenCalled();
    expect(errorSpy).toHaveBeenCalled();
    const feedback = wrapper.find('.mermaid-feedback');
    expect(feedback.attributes('data-status')).toBe('error');
    expect(feedback.text()).toBe('下载 Mermaid SVG 失败');
  });

  it('routes Mermaid fullscreen actions to MarkdownEnhancements', async () => {
    const wrapper = mountMessage('assistant');
    const mermaidContent = wrapper.find('.mermaid-content').element as HTMLElement;
    mermaidContent.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg"><g></g></svg>';

    await wrapper.find('[data-mermaid-action="fullscreen"]').trigger('click');

    expect(markdownEnhancementExposeMock.openMermaidFullscreen).toHaveBeenCalledTimes(1);
    expect(markdownEnhancementExposeMock.openMermaidFullscreen.mock.calls[0][0]).toContain('<svg');
    expect(markdownEnhancementExposeMock.openMermaidFullscreen.mock.calls[0][1]).toBe('graph TD; A-->B;');
    expect(markdownEnhancementExposeMock.openMermaidFullscreen.mock.calls[0][2]).toEqual({
      closeLabel: '关闭全屏',
    });
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

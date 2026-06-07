import { mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createI18n } from 'vue-i18n';

import MarkdownEnhancements from './MarkdownEnhancements.vue';

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: {
      'mermaid.toolbar': 'Mermaid 图表工具',
      'mermaid.copy_source': '复制源码',
      'mermaid.download_svg': '下载 SVG',
      'mermaid.close_fullscreen': '关闭全屏',
      'mermaid.zoom_in': '放大图表',
      'mermaid.zoom_out': '缩小图表',
      'mermaid.reset_zoom': '重置缩放',
      'mermaid.copy_source_success': 'Mermaid 源码已复制',
      'mermaid.copy_source_failed': '复制 Mermaid 源码失败',
      'mermaid.download_svg_success': 'Mermaid SVG 已开始下载',
      'mermaid.download_svg_failed': '下载 Mermaid SVG 失败',
    },
  },
});

const mountEnhancements = () =>
  mount(MarkdownEnhancements, {
    attachTo: document.body,
    global: {
      plugins: [i18n],
    },
  });

const flushAsyncUi = async (wrapper: ReturnType<typeof mountEnhancements>) => {
  await Promise.resolve();
  await wrapper.vm.$nextTick();
};

describe('MarkdownEnhancements Mermaid fullscreen', () => {
  beforeEach(() => {
    Object.defineProperty(window.navigator, 'clipboard', {
      configurable: true,
      value: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  afterEach(() => {
    document.body.innerHTML = '';
    document.body.style.overflow = '';
    vi.restoreAllMocks();
  });

  it('opens Mermaid fullscreen with zoom, copy, download, and close controls', async () => {
    const wrapper = mountEnhancements();

    wrapper.vm.openMermaidFullscreen(
      '<svg xmlns="http://www.w3.org/2000/svg"><g data-test="diagram"></g></svg>',
      'graph TD; A-->B;',
      { closeLabel: '关闭全屏' },
    );
    await wrapper.vm.$nextTick();

    expect(document.body.style.overflow).toBe('hidden');
    expect(document.querySelector('.mermaid-fullscreen-overlay')).not.toBeNull();
    expect(document.querySelector('[data-mermaid-fullscreen-action="zoom-in"]')).not.toBeNull();
    expect(document.querySelector('[data-mermaid-fullscreen-action="zoom-out"]')).not.toBeNull();
    expect(document.querySelector('[data-mermaid-fullscreen-action="reset-zoom"]')).not.toBeNull();
    expect(document.querySelector('[data-mermaid-fullscreen-action="copy-source"]')).not.toBeNull();
    expect(document.querySelector('[data-mermaid-fullscreen-action="download-svg"]')).not.toBeNull();
    expect(document.querySelector('[data-mermaid-fullscreen-action="close"]')?.getAttribute('aria-label')).toBe('关闭全屏');
    expect(document.querySelector('.mermaid-fullscreen-stage svg')).not.toBeNull();
  });

  it('supports Mermaid fullscreen zoom reset and drag after zooming in', async () => {
    const wrapper = mountEnhancements();

    wrapper.vm.openMermaidFullscreen(
      '<svg xmlns="http://www.w3.org/2000/svg"><g></g></svg>',
      'graph TD; A-->B;',
      { closeLabel: '关闭全屏' },
    );
    await wrapper.vm.$nextTick();

    const viewport = document.querySelector('.mermaid-fullscreen-viewport') as HTMLElement;
    const transformLayer = document.querySelector('.mermaid-fullscreen-transform-layer') as HTMLElement;
    const zoomInButton = document.querySelector('[data-mermaid-fullscreen-action="zoom-in"]') as HTMLElement;
    const resetButton = document.querySelector('[data-mermaid-fullscreen-action="reset-zoom"]') as HTMLElement;

    await zoomInButton.click();
    await wrapper.vm.$nextTick();

    expect(document.querySelector('.mermaid-fullscreen-scale-indicator')?.textContent).toBe('125%');
    expect(transformLayer.style.transform).toContain('scale(1.25)');

    await viewport.dispatchEvent(new PointerEvent('pointerdown', {
      bubbles: true,
      pointerId: 4,
      clientX: 120,
      clientY: 140,
    }));
    await viewport.dispatchEvent(new PointerEvent('pointermove', {
      bubbles: true,
      pointerId: 4,
      clientX: 150,
      clientY: 175,
    }));
    await viewport.dispatchEvent(new PointerEvent('pointerup', {
      bubbles: true,
      pointerId: 4,
      clientX: 150,
      clientY: 175,
    }));
    await wrapper.vm.$nextTick();

    expect(transformLayer.style.transform).toContain('translate(30px, 35px) scale(1.25)');

    await resetButton.click();
    await wrapper.vm.$nextTick();

    expect(document.querySelector('.mermaid-fullscreen-scale-indicator')?.textContent).toBe('100%');
    expect(transformLayer.style.transform).toBe('translate(0px, 0px) scale(1)');
  });

  it('copies Mermaid source and downloads SVG from the fullscreen overlay', async () => {
    const wrapper = mountEnhancements();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(window.navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    });
    const createObjectUrlSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test');
    const revokeObjectUrlSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});

    wrapper.vm.openMermaidFullscreen(
      '<svg xmlns="http://www.w3.org/2000/svg"><g></g></svg>',
      'graph TD; A-->B;',
      { closeLabel: '关闭全屏' },
    );
    await wrapper.vm.$nextTick();

    const appendSpy = vi.spyOn(document.body, 'appendChild');
    const removeSpy = vi.spyOn(document.body, 'removeChild');
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => {});

    (document.querySelector('[data-mermaid-fullscreen-action="copy-source"]') as HTMLElement).click();
    await flushAsyncUi(wrapper);
    expect(writeText).toHaveBeenCalledWith('graph TD; A-->B;');
    expect(document.querySelector('.mermaid-fullscreen-overlay')).not.toBeNull();

    (document.querySelector('[data-mermaid-fullscreen-action="download-svg"]') as HTMLElement).click();
    await flushAsyncUi(wrapper);
    expect(createObjectUrlSpy).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
    expect(appendSpy).toHaveBeenCalled();
    expect(removeSpy).toHaveBeenCalled();
    expect(revokeObjectUrlSpy).toHaveBeenCalledWith('blob:test');
  });

  it('closes Mermaid fullscreen without affecting other overlay state', async () => {
    const wrapper = mountEnhancements();

    wrapper.vm.openLightbox('/test.png', 'diagram');
    await wrapper.vm.$nextTick();
    wrapper.vm.openMermaidFullscreen(
      '<svg xmlns="http://www.w3.org/2000/svg"><g></g></svg>',
      'graph TD; A-->B;',
      { closeLabel: '关闭全屏' },
    );
    await wrapper.vm.$nextTick();

    (document.querySelector('[data-mermaid-fullscreen-action="close"]') as HTMLElement).click();
    await wrapper.vm.$nextTick();

    expect(document.querySelector('.mermaid-fullscreen-overlay')).toBeNull();
    expect(document.querySelector('.lightbox-overlay')).not.toBeNull();
  });
});

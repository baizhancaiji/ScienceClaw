import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import { createI18n } from 'vue-i18n';

import MessageFooter from './MessageFooter.vue';

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      'Collapse message': 'Collapse message',
      'Expand message': 'Expand message',
      'pdf_export.action': 'Export PDF',
      'pdf_export.exporting': 'Exporting PDF',
    },
  },
});

const mountFooter = (props: Record<string, unknown>) => mount(MessageFooter, {
  props: {
    collapsed: false,
    isCopied: false,
    roundFileCount: 0,
    ...props,
  },
  global: {
    plugins: [i18n],
  },
});

describe('MessageFooter', () => {
  it('renders feedback, file count, copy state, and statistics', () => {
    const wrapper = mountFooter({
      collapsed: true,
      isCopied: true,
      roundFileCount: 2,
      statistics: {
        total_duration_ms: 1500,
        tool_call_count: 3,
        input_tokens: 1500,
        output_tokens: 2500,
      },
    });

    expect(wrapper.find('.msg-action-btn--collapsed').exists()).toBe(true);
    expect(wrapper.find('.msg-action-btn--copied').exists()).toBe(true);
    expect(wrapper.text()).toContain('2');
    expect(wrapper.text()).toContain('1.5s');
    expect(wrapper.text()).toContain('3次');
    expect(wrapper.text()).toContain('1.5K');
    expect(wrapper.text()).toContain('2.5K');
  });

  it('emits footer actions without owning parent behavior', async () => {
    const wrapper = mountFooter({ roundFileCount: 1 });

    const buttons = wrapper.findAll('button');
    await buttons[0].trigger('click');
    await buttons[1].trigger('click');
    await buttons[2].trigger('click');
    await buttons[3].trigger('click');

    expect(wrapper.emitted('toggleCollapse')).toHaveLength(1);
    expect(wrapper.emitted('copy')).toHaveLength(1);
    expect(wrapper.emitted('convertToPdf')).toHaveLength(1);
    expect(wrapper.emitted('showFiles')).toHaveLength(1);
  });

  it('uses i18n title and aria for the pdf button', () => {
    const wrapper = mountFooter({});
    const pdfButton = wrapper.findAll('button')[2];

    expect(pdfButton.attributes('title')).toBe('Export PDF');
    expect(pdfButton.attributes('aria-label')).toBe('Export PDF');
  });

  it('disables pdf button while exporting', async () => {
    const wrapper = mountFooter({
      pdfExporting: true,
      pdfDisabled: true,
    });
    const pdfButton = wrapper.findAll('button')[2];

    expect(pdfButton.attributes('disabled')).toBeDefined();
    expect(pdfButton.attributes('title')).toBe('Exporting PDF');
    await pdfButton.trigger('click');
    expect(wrapper.emitted('convertToPdf')).toBeUndefined();
  });
});

import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import MessageFooter from './MessageFooter.vue';

describe('MessageFooter', () => {
  it('renders feedback, file count, copy state, and statistics', () => {
    const wrapper = mount(MessageFooter, {
      props: {
        feedback: 'like',
        isCopied: true,
        roundFileCount: 2,
        statistics: {
          total_duration_ms: 1500,
          tool_call_count: 3,
          input_tokens: 1500,
          output_tokens: 2500,
        },
      },
    });

    expect(wrapper.find('.msg-action-btn--liked').exists()).toBe(true);
    expect(wrapper.find('.msg-action-btn--copied').exists()).toBe(true);
    expect(wrapper.text()).toContain('2');
    expect(wrapper.text()).toContain('1.5s');
    expect(wrapper.text()).toContain('3次');
    expect(wrapper.text()).toContain('1.5K');
    expect(wrapper.text()).toContain('2.5K');
  });

  it('emits footer actions without owning parent behavior', async () => {
    const wrapper = mount(MessageFooter, {
      props: {
        feedback: null,
        isCopied: false,
        roundFileCount: 1,
      },
    });

    const buttons = wrapper.findAll('button');
    await buttons[0].trigger('click');
    await buttons[1].trigger('click');
    await buttons[2].trigger('click');
    await buttons[3].trigger('click');
    await buttons[4].trigger('click');

    expect(wrapper.emitted('toggleFeedback')).toEqual([[ 'like' ], [ 'dislike' ]]);
    expect(wrapper.emitted('copy')).toHaveLength(1);
    expect(wrapper.emitted('convertToPdf')).toHaveLength(1);
    expect(wrapper.emitted('showFiles')).toHaveLength(1);
  });
});

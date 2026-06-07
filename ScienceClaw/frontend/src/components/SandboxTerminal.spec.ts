import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const writeln = vi.fn();
const reset = vi.fn();
const loadAddon = vi.fn();
const open = vi.fn();
const dispose = vi.fn();
const scrollToBottom = vi.fn();
const fit = vi.fn();

vi.mock('@xterm/xterm', () => ({
  Terminal: vi.fn().mockImplementation(() => ({
    writeln,
    reset,
    loadAddon,
    open,
    dispose,
    scrollToBottom,
  })),
}));

vi.mock('@xterm/addon-fit', () => ({
  FitAddon: vi.fn().mockImplementation(() => ({
    fit,
  })),
}));

const resizeObserverObserve = vi.fn();
const resizeObserverDisconnect = vi.fn();

const { default: SandboxTerminal } = await import('./SandboxTerminal.vue');

describe('SandboxTerminal', () => {
  beforeEach(() => {
    vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => {
      cb(0);
      return 1;
    });
    vi.stubGlobal('ResizeObserver', vi.fn().mockImplementation(() => ({
      observe: resizeObserverObserve,
      disconnect: resizeObserverDisconnect,
    })));
    writeln.mockClear();
    reset.mockClear();
    loadAddon.mockClear();
    open.mockClear();
    dispose.mockClear();
    scrollToBottom.mockClear();
    fit.mockClear();
    resizeObserverObserve.mockClear();
    resizeObserverDisconnect.mockClear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('re-renders terminal history when a snapshot replaces entries without changing length', async () => {
    const wrapper = mount(SandboxTerminal, {
      props: {
        active: true,
        history: [
          { toolName: 'exec', command: 'echo old', status: 'calling' },
        ],
      },
    });

    expect(reset).not.toHaveBeenCalled();
    expect(writeln).toHaveBeenCalledWith(expect.stringContaining('echo old'));

    writeln.mockClear();

    await wrapper.setProps({
      history: [
        { toolName: 'exec', command: 'echo new', status: 'calling' },
      ],
    });
    await nextTick();

    expect(reset).toHaveBeenCalledOnce();
    expect(writeln).toHaveBeenCalledWith(expect.stringContaining('echo new'));
    expect(writeln).not.toHaveBeenCalledWith(expect.stringContaining('echo old'));
  });
});

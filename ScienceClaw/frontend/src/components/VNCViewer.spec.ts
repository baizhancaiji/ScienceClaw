import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';

import VNCViewer from './VNCViewer.vue';

type RFBMockInstance = {
  viewOnly: boolean;
  scaleViewport: boolean;
  disconnect: ReturnType<typeof vi.fn>;
  addEventListener: ReturnType<typeof vi.fn>;
  target: Element;
  url: string;
  options: Record<string, unknown>;
};

const { getVNCUrlMock, rfbInstances, RFBMock } = vi.hoisted(() => {
  const instances: RFBMockInstance[] = [];

  class MockRFB {
    public viewOnly = false;
    public scaleViewport = false;
    public disconnect = vi.fn();
    public addEventListener = vi.fn();

    constructor(
      public readonly target: Element,
      public readonly url: string,
      public readonly options: Record<string, unknown>,
    ) {
      instances.push(this);
    }
  }

  return {
    getVNCUrlMock: vi.fn(),
    rfbInstances: instances,
    RFBMock: MockRFB,
  };
});

vi.mock('@/api/agent', () => ({
  getVNCUrl: getVNCUrlMock,
}));

vi.mock('@novnc/novnc/lib/rfb', () => ({
  default: RFBMock,
}));

describe('VNCViewer', () => {
  afterEach(() => {
    rfbInstances.length = 0;
    getVNCUrlMock.mockReset();
  });

  it('updates viewOnly on the existing RFB instance without reconnecting', async () => {
    const wrapper = mount(VNCViewer, {
      props: {
        sessionId: 'session-1',
        enabled: true,
        viewOnly: true,
        directWsUrl: 'ws://sandbox.example/ws',
      },
    });

    await vi.waitFor(() => {
      expect(rfbInstances).toHaveLength(1);
    });

    expect(rfbInstances[0]?.viewOnly).toBe(true);

    await wrapper.setProps({ viewOnly: false });

    expect(rfbInstances).toHaveLength(1);
    expect(rfbInstances[0]?.viewOnly).toBe(false);
    expect(rfbInstances[0]?.disconnect).not.toHaveBeenCalled();
    expect(getVNCUrlMock).not.toHaveBeenCalled();
  });

  it('disconnects the active RFB instance when disabled and on unmount', async () => {
    const wrapper = mount(VNCViewer, {
      props: {
        sessionId: 'session-1',
        enabled: true,
        directWsUrl: 'ws://sandbox.example/ws',
      },
    });

    await vi.waitFor(() => {
      expect(rfbInstances).toHaveLength(1);
    });

    const instance = rfbInstances[0]!;

    await wrapper.setProps({ enabled: false });

    expect(instance.disconnect).toHaveBeenCalledTimes(1);

    await wrapper.unmount();

    expect(instance.disconnect).toHaveBeenCalledTimes(1);
  });
});

import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent, nextTick } from "vue";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("shared state side effects", () => {
  beforeEach(() => {
    vi.resetModules();
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("initializes and persists theme state through localStorage", async () => {
    localStorage.setItem("scienceclaw-theme", "dark");

    const { useTheme } = await import("./useTheme");
    const { initTheme, isDark, toggleTheme } = useTheme();

    initTheme();

    expect(isDark.value).toBe(true);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(localStorage.getItem("scienceclaw-theme")).toBe("dark");

    toggleTheme();

    expect(isDark.value).toBe(false);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
    expect(localStorage.getItem("scienceclaw-theme")).toBe("light");
  });

  it("loads and persists left panel visibility through localStorage", async () => {
    localStorage.setItem("manus-left-panel-state", "true");

    const { useLeftPanel } = await import("./useLeftPanel");
    const { isLeftPanelShow, setLeftPanel } = useLeftPanel();

    expect(isLeftPanelShow.value).toBe(true);

    setLeftPanel(false);
    await nextTick();

    expect(localStorage.getItem("manus-left-panel-state")).toBe("false");
  });

  it("clears the relative time interval on component unmount", async () => {
    vi.useFakeTimers();
    const setIntervalSpy = vi.spyOn(window, "setInterval");
    const clearIntervalSpy = vi.spyOn(window, "clearInterval");
    const { useRelativeTime } = await import("./useTime");

    const wrapper = mount(
      defineComponent({
        setup() {
          useRelativeTime();
          return () => null;
        },
      }),
    );

    expect(setIntervalSpy).toHaveBeenCalledWith(expect.any(Function), 60000);
    const intervalId =
      setIntervalSpy.mock.results[setIntervalSpy.mock.results.length - 1]
        ?.value;

    wrapper.unmount();

    expect(clearIntervalSpy).toHaveBeenCalledWith(intervalId);
  });
});

describe("session notification lifecycle", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("cancels the active notification subscription when the last consumer unmounts", async () => {
    const cancel = vi.fn();
    const subscribeSessionNotifications = vi.fn(async () => cancel);
    vi.doMock("../api/agent", () => ({ subscribeSessionNotifications }));

    const { useSessionNotifications } =
      await import("./useSessionNotifications");
    const wrapper = mount(
      defineComponent({
        setup() {
          const { onSessionUpdated } = useSessionNotifications();
          onSessionUpdated(vi.fn());
          return () => null;
        },
      }),
    );

    await flushPromises();

    expect(subscribeSessionNotifications).toHaveBeenCalledTimes(1);

    wrapper.unmount();

    expect(cancel).toHaveBeenCalledTimes(1);
  });

  it("clears a pending reconnect timer when the last notification consumer unmounts", async () => {
    let closeConnection: (() => void) | undefined;
    const subscribeSessionNotifications = vi.fn(
      async (options: { onClose: () => void }) => {
        closeConnection = options.onClose;
        return vi.fn();
      },
    );
    vi.doMock("../api/agent", () => ({ subscribeSessionNotifications }));

    const { useSessionNotifications } =
      await import("./useSessionNotifications");
    const wrapper = mount(
      defineComponent({
        setup() {
          const { onSessionCreated } = useSessionNotifications();
          onSessionCreated(vi.fn());
          return () => null;
        },
      }),
    );

    await flushPromises();

    expect(subscribeSessionNotifications).toHaveBeenCalledTimes(1);

    closeConnection?.();
    expect(vi.getTimerCount()).toBe(1);

    wrapper.unmount();
    vi.advanceTimersByTime(3000);

    expect(subscribeSessionNotifications).toHaveBeenCalledTimes(1);
    expect(vi.getTimerCount()).toBe(0);
  });
});

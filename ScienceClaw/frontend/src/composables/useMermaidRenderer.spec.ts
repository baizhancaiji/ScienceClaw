import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick, ref } from "vue";

import { useMermaidRenderer, resetMermaidCache } from "./useMermaidRenderer";
import type { MermaidLoaderAdapter } from "../utils/markdownRenderer";
import { resetMermaidLoader } from "../utils/markdownRenderer";

describe("useMermaidRenderer", () => {
  beforeEach(() => {
    resetMermaidLoader();
    resetMermaidCache();
  });

  /** renderMermaidWrapper 内部用 isConnected 校验 DOM 有效性，
   *  测试用的根元素需要挂载到 document 上 */
  const attachedRoots: HTMLElement[] = [];
  afterEach(() => {
    attachedRoots.forEach(r => {
      if (r.parentNode) r.parentNode.removeChild(r);
    });
    attachedRoots.length = 0;
  });
  const attachRoot = (root: HTMLElement) => {
    document.body.appendChild(root);
    attachedRoots.push(root);
    return root;
  };

  const createWrapperRoot = (code: string) => {
    const root = document.createElement("div");
    root.innerHTML = `
      <div class="mermaid-wrapper" data-mermaid-code="${encodeURIComponent(code)}">
        <div class="mermaid-loading"></div>
        <div class="mermaid-content"></div>
      </div>
    `;
    return root;
  };

  const createWrapperRootForCodes = (codes: string[]) => {
    const root = document.createElement("div");
    root.innerHTML = codes.map(code => `
      <div class="mermaid-wrapper" data-mermaid-code="${encodeURIComponent(code)}">
        <div class="mermaid-loading"></div>
        <div class="mermaid-content"></div>
      </div>
    `).join("");
    return root;
  };

  it("creates stable mermaid placeholder ids", () => {
    const { createMermaidPlaceholderId } = useMermaidRenderer({
      markdownRef: ref(null),
      autoRender: false,
    });

    expect(createMermaidPlaceholderId()).toBe("mermaid-0");
    expect(createMermaidPlaceholderId()).toBe("mermaid-1");
  });

  it("loads mermaid, renders wrappers, and writes SVG content", async () => {
    const root = attachRoot(createWrapperRoot("graph TD; A-->B;"));
    const mermaid: MermaidLoaderAdapter = {
      initialize: vi.fn(),
      render: vi
        .fn()
        .mockResolvedValue({ svg: '<svg data-test="diagram"></svg>' }),
    };
    const { renderMermaidDiagrams } = useMermaidRenderer({
      markdownRef: ref(root),
      importMermaid: async () => mermaid,
      autoRender: false,
    });

    await renderMermaidDiagrams();

    expect(mermaid.initialize).toHaveBeenCalledOnce();
    expect(mermaid.render).toHaveBeenCalledWith(
      expect.stringMatching(/^mermaid-svg-/),
      "graph TD; A-->B;",
    );
    expect(
      (root.querySelector(".mermaid-loading") as HTMLElement).style.display,
    ).toBe("none");
    expect(root.querySelector(".mermaid-content")?.innerHTML).toContain(
      'data-test="diagram"',
    );
  });

  it("skips loading mermaid when no wrappers are present", async () => {
    const importMermaid = vi.fn();
    const { renderMermaidDiagrams } = useMermaidRenderer({
      markdownRef: ref(document.createElement("div")),
      importMermaid,
      autoRender: false,
    });

    await renderMermaidDiagrams();

    expect(importMermaid).not.toHaveBeenCalled();
  });

  it("schedules rendering when a mermaid wrapper is inserted after mount", async () => {
    const mermaid: MermaidLoaderAdapter = {
      initialize: vi.fn(),
      render: vi
        .fn()
        .mockResolvedValue({ svg: '<svg data-test="inserted"></svg>' }),
    };

    const wrapper = mount({
      template: '<div ref="root"></div>',
      setup() {
        const root = ref<HTMLElement | null>(null);
        useMermaidRenderer({
          markdownRef: root,
          importMermaid: async () => mermaid,
        });
        return { root };
      },
    });

    const root = wrapper.element as HTMLElement;
    // renderMermaidWrapper 用 isConnected 校验 DOM 有效性，
    // mount() 默认不挂载到 document，需要手动追加
    document.body.appendChild(root);
    attachedRoots.push(root);

    root.innerHTML = `
      <div class="mermaid-wrapper" data-mermaid-code="${encodeURIComponent("graph TD; A-->B;")}">
        <div class="mermaid-loading"></div>
        <div class="mermaid-content"></div>
      </div>
    `;

    await nextTick();
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    expect(mermaid.render).toHaveBeenCalledWith(
      expect.stringMatching(/^mermaid-svg-/),
      "graph TD; A-->B;",
    );
    expect(root.querySelector(".mermaid-content")?.innerHTML).toContain(
      'data-test="inserted"',
    );
  });

  it("refreshes LRU order on cache hit and evicts the oldest entry after 100 items", async () => {
    const mermaid: MermaidLoaderAdapter = {
      initialize: vi.fn(),
      render: vi.fn(async (_id: string, code: string) => ({
        svg: `<svg data-code="${code}"></svg>`,
      })),
    };

    const firstRoot = attachRoot(createWrapperRootForCodes(
      Array.from({ length: 100 }, (_, index) => `graph TD; A${index}-->B${index};`),
    ));
    const firstRenderer = useMermaidRenderer({
      markdownRef: ref(firstRoot),
      importMermaid: async () => mermaid,
      autoRender: false,
    });

    await firstRenderer.renderMermaidDiagrams();
    expect(mermaid.render).toHaveBeenCalledTimes(100);

    const hitRoot = attachRoot(createWrapperRoot("graph TD; A0-->B0;"));
    const hitRenderer = useMermaidRenderer({
      markdownRef: ref(hitRoot),
      importMermaid: async () => mermaid,
      autoRender: false,
    });
    await hitRenderer.renderMermaidDiagrams();
    expect(mermaid.render).toHaveBeenCalledTimes(100);

    const overflowRoot = attachRoot(createWrapperRoot("graph TD; A100-->B100;"));
    const overflowRenderer = useMermaidRenderer({
      markdownRef: ref(overflowRoot),
      importMermaid: async () => mermaid,
      autoRender: false,
    });
    await overflowRenderer.renderMermaidDiagrams();
    expect(mermaid.render).toHaveBeenCalledTimes(101);

    const evictedRoot = attachRoot(createWrapperRoot("graph TD; A1-->B1;"));
    const evictedRenderer = useMermaidRenderer({
      markdownRef: ref(evictedRoot),
      importMermaid: async () => mermaid,
      autoRender: false,
    });
    await evictedRenderer.renderMermaidDiagrams();
    expect(mermaid.render).toHaveBeenCalledTimes(102);

    const retainedRoot = attachRoot(createWrapperRoot("graph TD; A0-->B0;"));
    const retainedRenderer = useMermaidRenderer({
      markdownRef: ref(retainedRoot),
      importMermaid: async () => mermaid,
      autoRender: false,
    });
    await retainedRenderer.renderMermaidDiagrams();
    expect(mermaid.render).toHaveBeenCalledTimes(102);
  });

  it("continues rendering other wrappers when one wrapper fails", async () => {
    const root = attachRoot(createWrapperRootForCodes([
      "graph TD; FAIL",
      "graph TD; OK",
    ]));
    const mermaid: MermaidLoaderAdapter = {
      initialize: vi.fn(),
      render: vi.fn(async (_id: string, code: string) => {
        if (code.includes("FAIL")) {
          throw new Error("render failed");
        }
        return { svg: '<svg data-test="ok"></svg>' };
      }),
    };
    const { renderMermaidDiagrams } = useMermaidRenderer({
      markdownRef: ref(root),
      importMermaid: async () => mermaid,
      autoRender: false,
    });

    await renderMermaidDiagrams();

    const wrappers = root.querySelectorAll(".mermaid-wrapper");
    expect((wrappers[0].querySelector(".mermaid-loading") as HTMLElement).innerHTML).toContain("mermaid-error");
    expect(wrappers[1].querySelector(".mermaid-content")?.innerHTML).toContain('data-test="ok"');
  });

  it("does not write SVG into a wrapper from an outdated render generation", async () => {
    const root = attachRoot(createWrapperRoot("graph TD; OLD"));
    const oldRenderDeferred: {
      resolve?: (value: { svg: string }) => void;
    } = {};
    const mermaid: MermaidLoaderAdapter = {
      initialize: vi.fn(),
      render: vi.fn((_id: string, code: string) => {
        if (code.includes("OLD")) {
          return new Promise<{ svg: string }>((resolve) => {
            oldRenderDeferred.resolve = resolve;
          });
        }
        return Promise.resolve({ svg: '<svg data-test="new"></svg>' });
      }),
    };
    const { renderMermaidDiagrams, scheduleRenderMermaidDiagrams } = useMermaidRenderer({
      markdownRef: ref(root),
      importMermaid: async () => mermaid,
      autoRender: false,
    });

    const oldRenderPromise = renderMermaidDiagrams();
    for (let i = 0; i < 5 && !oldRenderDeferred.resolve; i++) {
      await Promise.resolve();
    }
    if (!oldRenderDeferred.resolve) {
      throw new Error("old render did not start");
    }
    const oldWrapper = root.querySelector(".mermaid-wrapper") as HTMLElement;
    root.innerHTML = `
      <div class="mermaid-wrapper" data-mermaid-code="${encodeURIComponent("graph TD; NEW")}">
        <div class="mermaid-loading"></div>
        <div class="mermaid-content"></div>
      </div>
    `;
    scheduleRenderMermaidDiagrams();
    await nextTick();
    await new Promise((resolve) => setTimeout(resolve, 0));

    oldRenderDeferred.resolve({ svg: '<svg data-test="old"></svg>' });
    await oldRenderPromise;

    expect(oldWrapper.isConnected).toBe(false);
    expect(oldWrapper.querySelector(".mermaid-content")?.innerHTML).toBe("");
    expect(root.querySelector(".mermaid-content")?.innerHTML).toContain('data-test="new"');
  });

  it("rehydrates recreated mermaid wrappers from cache after the markdown root is reattached", async () => {
    const mermaid: MermaidLoaderAdapter = {
      initialize: vi.fn(),
      render: vi
        .fn()
        .mockResolvedValue({ svg: '<svg data-test="cached-diagram"></svg>' }),
    };

    const wrapper = mount({
      template: `
        <div>
          <div v-if="visible" ref="root" v-html="html"></div>
        </div>
      `,
      setup() {
        const root = ref<HTMLElement | null>(null);
        const visible = ref(true);
        const html = ref(`
          <div class="mermaid-wrapper" data-mermaid-code="${encodeURIComponent("graph TD; A-->B;")}">
            <div class="mermaid-loading"></div>
            <div class="mermaid-content"></div>
          </div>
        `);

        useMermaidRenderer({
          markdownRef: root,
          importMermaid: async () => mermaid,
        });

        return {
          root,
          visible,
          html,
        };
      },
    }, {
      attachTo: document.body,
    });

    await nextTick();
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    expect(mermaid.render).toHaveBeenCalledTimes(1);
    expect(wrapper.element.querySelector(".mermaid-content")?.innerHTML).toContain(
      'data-test="cached-diagram"',
    );

    wrapper.vm.visible = false;
    await nextTick();

    wrapper.vm.visible = true;
    await nextTick();
    await new Promise((resolve) => setTimeout(resolve, 0));
    await nextTick();

    expect(mermaid.render).toHaveBeenCalledTimes(1);
    expect(wrapper.element.querySelector(".mermaid-content")?.innerHTML).toContain(
      'data-test="cached-diagram"',
    );

    wrapper.unmount();
  });
});

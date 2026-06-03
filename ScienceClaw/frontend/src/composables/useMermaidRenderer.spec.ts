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
});

import { describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import { useMermaidRenderer } from "./useMermaidRenderer";
import type { MermaidLoaderAdapter } from "../utils/markdownRenderer";

describe("useMermaidRenderer", () => {
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
    const root = createWrapperRoot("graph TD; A-->B;");
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
});

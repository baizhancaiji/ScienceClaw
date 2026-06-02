import { describe, expect, it } from "vitest";

import { useMarkdownRenderer } from "./useMarkdownRenderer";

describe("useMarkdownRenderer", () => {
  it("renders markdown links, code blocks, math, and mermaid placeholders", () => {
    let mathCounter = 0;
    const { renderMarkdown } = useMarkdownRenderer({
      createMermaidPlaceholderId: () => "mermaid-test",
      createMathPlaceholderId: (kind) => `${kind}-${mathCounter++}`,
    });

    const html = renderMarkdown(
      [
        "[Docs](https://example.com)",
        "",
        "$x_1$",
        "",
        "```ts",
        "const value = 1;",
        "```",
        "",
        "```mermaid",
        "graph TD; A-->B;",
        "```",
      ].join("\n"),
    );

    expect(html).toContain('href="https://example.com"');
    expect(html).toContain('class="katex-inline"');
    expect(html).toContain('class="code-block-wrapper');
    expect(html).toContain('data-mermaid-id="mermaid-test"');
    expect(html).toContain('data-mermaid-code="graph%20TD%3B%20A--%3EB%3B"');
  });

  it("falls back to sanitized text when rendering fails before markdown parse", () => {
    const { renderMarkdown } = useMarkdownRenderer({
      createMermaidPlaceholderId: () => {
        throw new Error("id failed");
      },
    });

    const html = renderMarkdown("```mermaid\ngraph TD; A-->B;\n```");

    expect(html).toContain("graph TD; A--&gt;B;");
    expect(html).not.toContain("<script>");
  });
});

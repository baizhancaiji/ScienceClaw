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
    expect(html).toContain('class="mermaid-wrapper"');
    expect(html).toContain('data-mermaid-id="mermaid-test"');
    expect(html).toContain('data-mermaid-code="graph%20TD%3B%20A--%3EB%3B"');
  });

  it("creates mermaid placeholders for mermaid fences", () => {
    const { renderMarkdown } = useMarkdownRenderer({
      createMermaidPlaceholderId: () => "mermaid-test",
    });

    const html = renderMarkdown("```mermaid\ngraph TD; A-->B;\n```");

    expect(html).toContain('class="mermaid-wrapper"');
    expect(html).toContain('data-mermaid-id="mermaid-test"');
    expect(html).toContain('data-mermaid-code="graph%20TD%3B%20A--%3EB%3B"');
    expect(html).not.toContain("<script>");
  });

  it("keeps markdown source fences as copyable code blocks", () => {
    const { renderMarkdown } = useMarkdownRenderer({
      createMermaidPlaceholderId: () => "mermaid-test",
    });

    const html = renderMarkdown(["```md", "# Title", "", "$x$", "```"].join("\n"));

    expect(html).toContain('class="code-block-wrapper');
    expect(html).toContain('<span class="code-block-lang">md</span>');
    expect(html).not.toContain("<h1");
    expect(html).not.toContain('class="katex-inline"');
  });

  it("creates mermaid placeholders for mmd fences", () => {
    const { renderMarkdown } = useMarkdownRenderer({
      createMermaidPlaceholderId: () => "mermaid-test",
    });

    const html = renderMarkdown(["```mmd", "graph TD; A-->B;", "```"].join("\n"));

    expect(html).toContain('class="mermaid-wrapper"');
    expect(html).toContain('data-mermaid-id="mermaid-test"');
    expect(html).toContain('data-mermaid-code="graph%20TD%3B%20A--%3EB%3B"');
  });

  it("creates mermaid placeholders for tilde mermaid fences", () => {
    const { renderMarkdown } = useMarkdownRenderer({
      createMermaidPlaceholderId: () => "mermaid-test",
    });

    const html = renderMarkdown(["~~~mermaid", "graph TD; A-->B;", "~~~"].join("\n"));

    expect(html).toContain('class="mermaid-wrapper"');
    expect(html).toContain('data-mermaid-id="mermaid-test"');
    expect(html).toContain('data-mermaid-code="graph%20TD%3B%20A--%3EB%3B"');
  });

  it("keeps explicit mermaid source fences as copyable code blocks", () => {
    const { renderMarkdown } = useMarkdownRenderer({
      createMermaidPlaceholderId: () => "mermaid-test",
    });

    const html = renderMarkdown(["```mermaid-source", "graph TD; A-->B;", "```"].join("\n"));

    expect(html).toContain('class="code-block-wrapper');
    expect(html).toContain('<span class="code-block-lang">mermaid</span>');
    expect(html).not.toContain('class="mermaid-wrapper"');
  });

  it("keeps mermaid fences as copyable code blocks when diagram rendering is disabled", () => {
    const { renderMarkdown } = useMarkdownRenderer({
      createMermaidPlaceholderId: () => "mermaid-test",
      renderMermaid: false,
    });

    const html = renderMarkdown(["```mermaid", "graph TD; A-->B;", "```"].join("\n"));

    expect(html).toContain('class="code-block-wrapper');
    expect(html).toContain('<span class="code-block-lang">mermaid</span>');
    expect(html).not.toContain('class="mermaid-wrapper"');
    expect(html).not.toContain('data-mermaid-code');
  });
});

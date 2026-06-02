import { describe, expect, it } from "vitest";

import { useMathRenderer } from "./useMathRenderer";

describe("useMathRenderer", () => {
  it("preprocesses and restores math placeholders through the composable boundary", () => {
    let counter = 0;
    const { postprocessMarkdownMath, preprocessMarkdownMath } = useMathRenderer(
      {
        createPlaceholderId: (kind) => `${kind}-${counter++}`,
      },
    );

    const preprocessed = preprocessMarkdownMath(
      "Block $$a+b$$ and inline $x_1$.",
    );

    expect(preprocessed.text).toContain("block-0");
    expect(preprocessed.text).toContain("inline-1");
    expect(preprocessed.mathBlocks.size).toBe(2);
    expect(
      postprocessMarkdownMath("Value inline-1.", preprocessed.mathBlocks),
    ).toContain("katex-inline");
  });

  it("leaves html unchanged when there are no math placeholders", () => {
    const { postprocessMarkdownMath } = useMathRenderer({
      createPlaceholderId: (kind) => kind,
    });

    expect(postprocessMarkdownMath("<p>No math</p>", new Map())).toBe(
      "<p>No math</p>",
    );
  });
});

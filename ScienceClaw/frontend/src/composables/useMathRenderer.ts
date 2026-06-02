import {
  postprocessMath,
  preprocessMath,
  type CreateMathPlaceholderId,
  type PreprocessMathResult,
} from "../utils/markdownRenderer";

export interface UseMathRendererOptions {
  createPlaceholderId: CreateMathPlaceholderId;
  logPrefix?: string;
}

export function useMathRenderer({
  createPlaceholderId,
  logPrefix = "[Markdown]",
}: UseMathRendererOptions) {
  const preprocessMarkdownMath = (text: string): PreprocessMathResult => {
    try {
      return preprocessMath(text, createPlaceholderId);
    } catch (e) {
      console.warn(logPrefix, "Math preprocessing failed:", e);
      return { text, mathBlocks: new Map() };
    }
  };

  const postprocessMarkdownMath = (
    html: string,
    mathBlocks: Map<string, string>,
  ): string => {
    if (mathBlocks.size === 0) {
      return html;
    }

    try {
      return postprocessMath(html, mathBlocks);
    } catch (e) {
      console.warn(logPrefix, "Math postprocessing failed:", e);
      return html;
    }
  };

  return {
    postprocessMarkdownMath,
    preprocessMarkdownMath,
  };
}

import DOMPurify from "dompurify";
import hljs from "highlight.js/lib/core";
import bash from "highlight.js/lib/languages/bash";
import css from "highlight.js/lib/languages/css";
import go from "highlight.js/lib/languages/go";
import java from "highlight.js/lib/languages/java";
import javascript from "highlight.js/lib/languages/javascript";
import json from "highlight.js/lib/languages/json";
import markdown from "highlight.js/lib/languages/markdown";
import plaintext from "highlight.js/lib/languages/plaintext";
import python from "highlight.js/lib/languages/python";
import shell from "highlight.js/lib/languages/shell";
import typescript from "highlight.js/lib/languages/typescript";
import xml from "highlight.js/lib/languages/xml";
import { marked } from "marked";

import { domPurifyConfig } from "../utils/content";
import { formatMarkdown } from "../utils/markdownFormatter";
import {
  normalizeMarkdownCodeToken,
  renderHighlightedCodeBlock,
  renderMarkdownLink,
  renderMermaidPlaceholder,
  type CreateMathPlaceholderId,
} from "../utils/markdownRenderer";
import { useMathRenderer } from "./useMathRenderer";

export interface UseMarkdownRendererOptions {
  createMermaidPlaceholderId: () => string;
  createMathPlaceholderId?: CreateMathPlaceholderId;
  logPrefix?: string;
}

const registerHighlightLanguages = () => {
  hljs.registerLanguage("bash", bash);
  hljs.registerLanguage("css", css);
  hljs.registerLanguage("go", go);
  hljs.registerLanguage("html", xml);
  hljs.registerLanguage("java", java);
  hljs.registerLanguage("javascript", javascript);
  hljs.registerLanguage("js", javascript);
  hljs.registerLanguage("json", json);
  hljs.registerLanguage("markdown", markdown);
  hljs.registerLanguage("md", markdown);
  hljs.registerLanguage("plaintext", plaintext);
  hljs.registerLanguage("python", python);
  hljs.registerLanguage("py", python);
  hljs.registerLanguage("shell", shell);
  hljs.registerLanguage("sh", shell);
  hljs.registerLanguage("ts", typescript);
  hljs.registerLanguage("typescript", typescript);
  hljs.registerLanguage("xml", xml);
};

registerHighlightLanguages();

export function useMarkdownRenderer({
  createMermaidPlaceholderId,
  createMathPlaceholderId,
  logPrefix = "[Markdown]",
}: UseMarkdownRendererOptions) {
  let mathCounter = 0;
  const { postprocessMarkdownMath, preprocessMarkdownMath } = useMathRenderer({
    createPlaceholderId:
      createMathPlaceholderId ??
      ((kind) =>
        kind === "block"
          ? `MATH_BLOCK_${mathCounter++}`
          : `MATH_INLINE_${mathCounter++}`),
    logPrefix,
  });

  const renderer = new marked.Renderer();

  renderer.code = function (
    token: { text: string; lang?: string } | string,
    language?: string,
  ) {
    let code: string;
    let lang: string;

    try {
      const normalized = normalizeMarkdownCodeToken(token, language);
      code = normalized.code;
      lang = normalized.lang;
    } catch (e) {
      console.error(logPrefix, "Code block render error:", e);
      code = "";
      lang = "plaintext";
    }

    if (lang === "mermaid") {
      return renderMermaidPlaceholder({
        id: createMermaidPlaceholderId(),
        code,
      });
    }

    let highlightedCode = code;

    if (lang && hljs.getLanguage(lang)) {
      try {
        highlightedCode = hljs.highlight(code, { language: lang }).value;
      } catch {
        // Keep the raw code if highlight.js cannot parse a registered language.
      }
    } else {
      highlightedCode = hljs.highlightAuto(code).value;
    }

    return renderHighlightedCodeBlock({ code, highlightedCode, lang });
  };

  renderer.link = function (
    token: { href: string; title?: string | null; text: string } | string,
    title?: string | null,
    text?: string,
  ) {
    return renderMarkdownLink(token, title, text);
  };

  const renderMarkdown = (text: string): string => {
    if (typeof text !== "string") return "";

    try {
      let formatted = formatMarkdown(text);
      const { text: preprocessed, mathBlocks } =
        preprocessMarkdownMath(formatted);
      formatted = preprocessed;

      let html = marked(formatted, {
        renderer,
        breaks: true,
        gfm: true,
      }) as string;

      html = postprocessMarkdownMath(html, mathBlocks);
      return DOMPurify.sanitize(html, domPurifyConfig);
    } catch (e) {
      console.error(logPrefix, "Markdown rendering failed:", e);
      return DOMPurify.sanitize(text, domPurifyConfig);
    }
  };

  return {
    renderMarkdown,
  };
}

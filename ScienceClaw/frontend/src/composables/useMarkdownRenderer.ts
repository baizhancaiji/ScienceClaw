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

import { configureChatDomPurify, domPurifyConfig } from "../utils/content";
import { formatMarkdown } from "../utils/markdownFormatter";
import {
  normalizeMarkdownCodeToken,
  renderHighlightedCodeBlock,
  renderMarkdownLink,
  renderMermaidPlaceholder,
  type MermaidToolbarLabels,
  type CreateMathPlaceholderId,
} from "../utils/markdownRenderer";
import { useMathRenderer } from "./useMathRenderer";

export interface UseMarkdownRendererOptions {
  createMermaidPlaceholderId: () => string;
  createMathPlaceholderId?: CreateMathPlaceholderId;
  logPrefix?: string;
  renderMermaid?: boolean;
  getMermaidLabels?: () => MermaidToolbarLabels;
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
configureChatDomPurify();

const MERMAID_DIAGRAM_LANGUAGES = new Set(["mermaid", "mmd"]);
const MERMAID_SOURCE_LANGUAGES = new Set([
  "mermaid-source",
  "mmd-source",
  "literal-mermaid",
]);

/**
 * 全局 Markdown 渲染结果缓存
 * - 历史会话加载时，同一消息多次进入页面不会重复走 marked.parse + hljs.highlight + DOMPurify
 * - LRU 策略，避免内存泄漏
 * - key 格式: `{renderMermaid}:{text}` — 同文本不同渲染模式（user/assistant）分开缓存
 */
const MARKDOWN_CACHE_MAX_SIZE = 200;
const markdownRenderCache = new Map<string, string>();

const getCacheKey = (text: string, renderVariant: string) =>
  `${renderVariant}:${text}`;

const getCachedMarkdown = (key: string): string | undefined => markdownRenderCache.get(key);
const setCachedMarkdown = (key: string, html: string): void => {
  if (markdownRenderCache.size >= MARKDOWN_CACHE_MAX_SIZE) {
    // 删除最早的条目（Map 保持插入顺序）
    const firstKey = markdownRenderCache.keys().next().value;
    if (firstKey !== undefined) markdownRenderCache.delete(firstKey);
  }
  markdownRenderCache.set(key, html);
};

export function useMarkdownRenderer({
  createMermaidPlaceholderId,
  createMathPlaceholderId,
  logPrefix = "[Markdown]",
  renderMermaid = true,
  getMermaidLabels = () => ({
    toolbar: "Mermaid diagram tools",
    fullscreen: "Fullscreen",
    copySource: "Copy Mermaid source",
    downloadSvg: "Download SVG",
    zoomIn: "Zoom in",
    zoomOut: "Zoom out",
    resetZoom: "Reset zoom",
    showSource: "Show source",
  }),
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

    const normalizedLang = lang.trim().toLowerCase();

    if (renderMermaid && MERMAID_DIAGRAM_LANGUAGES.has(normalizedLang)) {
      return renderMermaidPlaceholder({
        id: createMermaidPlaceholderId(),
        code,
        labels: getMermaidLabels(),
      });
    }

    if (MERMAID_SOURCE_LANGUAGES.has(normalizedLang)) {
      lang = "mermaid";
    }

    let highlightedCode = code;

    if (lang && hljs.getLanguage(lang)) {
      try {
        highlightedCode = hljs.highlight(code, { language: lang }).value;
      } catch {
        // Keep the raw code if highlight.js cannot parse a registered language.
      }
    }
    // 不再对未知语言调用 highlightAuto — 它对大段代码非常耗时，
    // 且结果对未注册语言通常没有实质改善

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
    const mermaidLabels = getMermaidLabels();
    const renderVariant = renderMermaid
      ? `mermaid:${[
        mermaidLabels.toolbar,
        mermaidLabels.fullscreen,
        mermaidLabels.copySource,
        mermaidLabels.downloadSvg,
        mermaidLabels.zoomIn,
        mermaidLabels.zoomOut,
        mermaidLabels.resetZoom,
        mermaidLabels.showSource,
      ].join('|')}`
      : 'plain';

    // 全局缓存命中：相同 markdown 文本 + 相同渲染模式直接返回已渲染 HTML
    const cacheKey = getCacheKey(text, renderVariant);
    const cached = getCachedMarkdown(cacheKey);
    if (cached !== undefined) return cached;

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
      const result = DOMPurify.sanitize(html, domPurifyConfig);
      setCachedMarkdown(cacheKey, result);
      return result;
    } catch (e) {
      console.error(logPrefix, "Markdown rendering failed:", e);
      const fallback = DOMPurify.sanitize(text, domPurifyConfig);
      setCachedMarkdown(cacheKey, fallback);
      return fallback;
    }
  };

  return {
    renderMarkdown,
  };
}

import { nextTick, onMounted, watch, type Ref } from "vue";

import {
  createMermaidLoader,
  renderMermaidWrapper,
  type ImportMermaid,
} from "../utils/markdownRenderer";

export interface UseMermaidRendererOptions {
  markdownRef: Ref<HTMLElement | null>;
  getContent?: () => unknown;
  importMermaid?: ImportMermaid;
  logPrefix?: string;
  autoRender?: boolean;
}

export function useMermaidRenderer({
  markdownRef,
  getContent,
  importMermaid = () => import("mermaid").then((module) => module.default),
  logPrefix = "[Mermaid]",
  autoRender = true,
}: UseMermaidRendererOptions) {
  const mermaidCache = new Map<string, string>();
  let mermaidCounter = 0;
  const { initMermaid } = createMermaidLoader(importMermaid, logPrefix);

  const createMermaidPlaceholderId = () => `mermaid-${mermaidCounter++}`;

  const renderMermaidDiagrams = async () => {
    if (!markdownRef.value) {
      console.log(logPrefix, "markdownRef not ready");
      return;
    }

    const mermaidWrappers =
      markdownRef.value.querySelectorAll(".mermaid-wrapper");
    if (mermaidWrappers.length === 0) {
      console.log(logPrefix, "No mermaid diagrams found");
      return;
    }

    console.log(logPrefix, "Found", mermaidWrappers.length, "mermaid diagrams");
    const mermaid = await initMermaid();

    for (let i = 0; i < mermaidWrappers.length; i++) {
      await renderMermaidWrapper({
        wrapper: mermaidWrappers[i],
        index: i,
        mermaid,
        cache: mermaidCache,
        logPrefix,
      });
    }
  };

  const scheduleRenderMermaidDiagrams = () => {
    nextTick(() => {
      if (markdownRef.value) {
        renderMermaidDiagrams();
      }
    });
  };

  if (autoRender) {
    if (getContent) {
      watch(getContent, scheduleRenderMermaidDiagrams);
    }

    onMounted(scheduleRenderMermaidDiagrams);
  }

  return {
    createMermaidPlaceholderId,
    renderMermaidDiagrams,
    scheduleRenderMermaidDiagrams,
  };
}

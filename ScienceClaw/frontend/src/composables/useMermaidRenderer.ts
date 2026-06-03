import { nextTick, onBeforeUnmount, onMounted, watch, type Ref } from "vue";

import {
  createMermaidLoader,
  renderMermaidWrapper,
  type ImportMermaid,
} from "../utils/markdownRenderer";

/**
 * 全局 Mermaid SVG 缓存
 * - 跨组件实例复用：同一段 mermaid 代码无论在哪个 ChatMessage 实例中，
 *   只要代码相同就复用已渲染的 SVG，不再重复调用 mermaid.render()
 * - 切换会话再回来也直接命中
 */
const GLOBAL_MERMAID_CACHE = new Map<string, string>();

/** 测试用：重置全局 mermaid SVG 缓存 */
export const resetMermaidCache = () => {
  GLOBAL_MERMAID_CACHE.clear();
};

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
  const mermaidCache = GLOBAL_MERMAID_CACHE;
  let mermaidCounter = 0;
  let renderScheduled = false;
  let mutationObserver: MutationObserver | null = null;
  /** 防抖最终渲染定时器：流式结束后保证至少一次有效渲染 */
  let finalRenderTimer: ReturnType<typeof setTimeout> | null = null;
  /** 渲染代际计数器：用于检测并中止过期渲染 */
  let renderGeneration = 0;
  const { initMermaid } = createMermaidLoader(importMermaid, logPrefix);

  const createMermaidPlaceholderId = () => `mermaid-${mermaidCounter++}`;

  const renderMermaidDiagrams = async () => {
    if (!markdownRef.value) {
      return;
    }

    // 快照当前渲染代际，若后续代际递增说明有更新内容，当前渲染应中止
    const currentGen = renderGeneration;

    const mermaidWrappers =
      markdownRef.value.querySelectorAll(".mermaid-wrapper");
    if (mermaidWrappers.length === 0) {
      return;
    }

    const mermaid = await initMermaid();

    for (let i = 0; i < mermaidWrappers.length; i++) {
      // 代际不一致 → 内容已更新，中止当前过期渲染
      if (currentGen !== renderGeneration) return;
      // DOM 有效性校验：跳过已脱离文档树的僵尸节点
      if (!markdownRef.value?.contains(mermaidWrappers[i])) continue;

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
    if (renderScheduled) {
      return;
    }

    renderScheduled = true;
    renderGeneration++;

    nextTick(() => {
      renderScheduled = false;
      if (markdownRef.value) {
        renderMermaidDiagrams();
      }
    });
  };

  /**
   * 防抖最终渲染：流式输出期间内容高频变化，nextTick 渲染容易踩中竞态窗口
   * 导致 DOM 被替换、SVG 写入僵尸节点。此定时器在最后一次内容变更后 500ms
   * 触发一次兜底渲染，此时 DOM 已稳定，保证图表一定能渲染出来。
   */
  const scheduleFinalRender = () => {
    if (finalRenderTimer) clearTimeout(finalRenderTimer);
    finalRenderTimer = setTimeout(() => {
      finalRenderTimer = null;
      renderGeneration++;
      if (markdownRef.value) {
        renderMermaidDiagrams();
      }
    }, 500);
  };

  const setupMermaidObserver = () => {
    if (
      !markdownRef.value ||
      typeof MutationObserver === "undefined" ||
      mutationObserver
    ) {
      return;
    }

    mutationObserver = new MutationObserver((mutations) => {
      const hasMermaidWrapper = mutations.some((mutation) =>
        Array.from(mutation.addedNodes).some((node) => {
          if (!(node instanceof Element)) {
            return false;
          }
          return (
            node.matches(".mermaid-wrapper") ||
            node.querySelector(".mermaid-wrapper") !== null
          );
        }),
      );

      if (hasMermaidWrapper) {
        scheduleRenderMermaidDiagrams();
      }
    });

    mutationObserver.observe(markdownRef.value, {
      childList: true,
      subtree: true,
    });
  };

  if (autoRender) {
    if (getContent) {
      watch(getContent, () => {
        scheduleRenderMermaidDiagrams();
        scheduleFinalRender();
      });
    }

    onMounted(() => {
      setupMermaidObserver();
      scheduleRenderMermaidDiagrams();
    });

    onBeforeUnmount(() => {
      mutationObserver?.disconnect();
      mutationObserver = null;
      if (finalRenderTimer) {
        clearTimeout(finalRenderTimer);
        finalRenderTimer = null;
      }
    });
  }

  return {
    createMermaidPlaceholderId,
    renderMermaidDiagrams,
    scheduleRenderMermaidDiagrams,
  };
}

<template>
  <div
    v-if="message.type === 'user'"
    :data-message-key="messageKey"
    :data-message-keys="messageKeysAttr"
    :class="[
      'msg-enter-right flex w-full flex-col items-end justify-end gap-1 group mt-4',
      messageFlashClass,
    ]"
  >
    <div class="flex items-end mb-0.5">
      <div
        class="transition-opacity duration-200 text-[11px] text-[var(--text-tertiary)] opacity-40 group-hover:opacity-100 tabular-nums"
      >
        {{ relativeTime(message.content.timestamp) }}
      </div>
    </div>
    <div class="flex max-w-[85%] relative flex-col gap-2 items-end">
      <div
        class="relative flex flex-col items-center rounded-2xl overflow-hidden bg-gradient-to-br from-blue-500 to-indigo-600 text-white p-3.5 ltr:rounded-br-sm rtl:rounded-bl-sm shadow-lg shadow-blue-500/15"
      >
        <div
          v-html="escapeUserText(messageContent.content)"
          class="w-full text-white/95 whitespace-pre-wrap break-words"
        ></div>
      </div>
    </div>
  </div>
  <div
    v-else-if="message.type === 'assistant'"
    :data-message-key="messageKey"
    :data-message-keys="messageKeysAttr"
    :class="[
      'msg-enter-left flex flex-col gap-2 w-full group mt-3',
      messageFlashClass,
    ]"
  >
    <!-- Header: avatar + name + time -->
    <div class="flex items-center justify-between h-7">
      <div class="flex items-center gap-2">
        <div
          class="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 via-red-500 to-amber-500 p-[3px] shadow-sm"
        >
          <div
            class="w-full h-full rounded-[5px] bg-white dark:bg-[#1e1e1e] flex items-center justify-center overflow-hidden"
          >
            <RobotAvatar class="w-full h-full" :interactive="false" />
          </div>
        </div>
        <span
          class="font-sans font-bold text-xs bg-clip-text text-transparent bg-gradient-to-r from-blue-500 via-red-500 to-amber-500"
          >{{ botName }}</span
        >
      </div>
      <div
        class="transition-opacity duration-200 text-[11px] text-[var(--text-tertiary)] opacity-40 group-hover:opacity-100 tabular-nums"
      >
        {{ relativeTime(message.content.timestamp) }}
      </div>
    </div>
    <!-- Answer card -->
    <div
      class="relative rounded-2xl bg-white dark:bg-[#1e1e1e] border border-gray-100 dark:border-gray-800 shadow-sm overflow-hidden"
    >
      <div
        class="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-blue-500 via-red-400 to-amber-400"
      ></div>
      <div
        v-if="isCollapsed"
        class="px-4 py-3 text-sm text-[var(--text-secondary)] leading-relaxed"
      >
        {{ collapsedPreview }}
      </div>
      <div
        v-else
        ref="markdownRef"
        class="p-4 markdown-content text-[15px] text-[var(--text-primary)] leading-relaxed"
        @click="handleMarkdownClick"
        @pointerdown="handleMermaidPointerDown"
        @pointermove="handleMermaidPointerMove"
        @pointerup="handleMermaidPointerEnd"
        @pointercancel="handleMermaidPointerEnd"
      >
        <template
          v-for="(part, index) in parseContent(messageContent.content)"
          :key="index"
        >
          <div v-if="part.type === 'html'" v-html="part.content"></div>
          <molecule-viewer
            v-else-if="part.type === 'molecule'"
            :src="part.src || ''"
            class="w-full my-2"
          />
          <image-viewer
            v-else-if="part.type === 'image'"
            :src="part.src || ''"
            :alt="part.alt"
            class="w-full my-2"
          />
          <html-viewer
            v-else-if="part.type === 'html-file'"
            :src="part.src || ''"
            class="w-full my-2"
          />
          <suggested-questions
            v-else-if="part.type === 'questions'"
            :questions="part.questions || []"
            @click="emit('suggestionClick', $event)"
          />
        </template>
      </div>
    </div>

    <MessageFooter
      v-if="!(isLast && isLoading)"
      :collapsed="isCollapsed"
      :is-copied="isCopied"
      :round-file-count="roundFiles.length"
      :statistics="messageContent.statistics"
      :pdf-exporting="pdfExport.exporting.value"
      :pdf-disabled="!props.sessionId || pdfExport.exporting.value"
      @toggle-collapse="toggleCollapse"
      @copy="copyMessage"
      @convert-to-pdf="handleConvertToPdf"
      @show-files="showFileListPanel()"
    />
  </div>
  <div v-else-if="message.type === 'tool'" class="hidden"></div>
  <div v-else-if="message.type === 'step'" class="hidden"></div>
  <AttachmentsMessage
    v-else-if="message.type === 'attachments'"
    :content="attachmentsContent"
  />

  <!-- Markdown 增强功能组件 -->
  <MarkdownEnhancements ref="markdownEnhancementsRef" />
</template>

<script setup lang="ts">
import { Message, MessageContent, AttachmentsContent } from "../types/message";
import { computed, onBeforeUnmount, ref } from "vue";
import { useI18n } from "vue-i18n";
import { ToolContent } from "../types/message";
import { useRelativeTime } from "../composables/useTime";
import { useMarkdownRenderer } from "../composables/useMarkdownRenderer";
import { useMermaidRenderer } from "../composables/useMermaidRenderer";
import AttachmentsMessage from "./AttachmentsMessage.vue";
import ImageViewer from "./ImageViewer.vue";
import HtmlViewer from "./HtmlViewer.vue";
import MoleculeViewer from "./MoleculeViewer.vue";
import SuggestedQuestions from "./SuggestedQuestions.vue";
import { transformSrc } from "../utils/content";
import MarkdownEnhancements from "./MarkdownEnhancements.vue";
import MessageFooter from "./MessageFooter.vue";
import { useFilePanel } from "../composables/useFilePanel";
import { usePdfExport } from "../composables/usePdfExport";
import { parseChatMessageContent } from "../utils/chatMessageContent";
import { showErrorToast } from "../utils/toast";

import RobotAvatar from "./icons/RobotAvatar.vue";

// Markdown 增强组件引用
const markdownEnhancementsRef = ref<InstanceType<
  typeof MarkdownEnhancements
> | null>(null);
const markdownRef = ref<HTMLElement | null>(null);
const { locale, t } = useI18n();
const pdfExport = usePdfExport(t);

const props = defineProps<{
  message: Message;
  sessionId?: string;
  mode?: string;
  isLast?: boolean;
  isLoading?: boolean;
  messageKey?: string;
  messageKeys?: string[];
  flashToken?: number;
}>();

const botName = computed(() => {
  if (props.mode === "skills") {
    return "ScienceClaw";
  }
  return "ScienceClaw";
});

const emit = defineEmits<{
  (e: "toolClick", tool: ToolContent): void;
  (e: "suggestionClick", question: string): void;
}>();

// Feedback state
const isCollapsed = ref(false);
const isCopied = ref(false);

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value;
};

const copyMessage = async () => {
  try {
    const text = messageContent.value?.content || "";
    if (!text) return;
    await navigator.clipboard.writeText(text);
    isCopied.value = true;
    setTimeout(() => {
      isCopied.value = false;
    }, 2000);
  } catch (err) {
    console.error("Failed to copy:", err);
  }
};

// 转成PDF
const handleConvertToPdf = async () => {
  if (!props.sessionId || !markdownRef.value) {
    showErrorToast(t("pdf_export.unavailable"));
    return;
  }
  await pdfExport.exportPdf(props.sessionId, markdownRef.value, String(locale.value));
};

// 本轮文件
const roundFiles = computed(() => messageContent.value.round_files || []);
const { showFileListPanel } = useFilePanel();

interface MermaidViewState {
  scale: number;
  x: number;
  y: number;
  dragging: boolean;
  dragPointerId: number | null;
  dragStartX: number;
  dragStartY: number;
  originX: number;
  originY: number;
}

const MERMAID_MIN_SCALE = 0.3;
const MERMAID_MAX_SCALE = 3;
const MERMAID_SCALE_STEP = 0.25;
const mermaidViewStates = new WeakMap<HTMLElement, MermaidViewState>();

const clampMermaidScale = (scale: number) =>
  Math.min(MERMAID_MAX_SCALE, Math.max(MERMAID_MIN_SCALE, scale));

const getMermaidViewState = (wrapper: HTMLElement): MermaidViewState => {
  const existing = mermaidViewStates.get(wrapper);
  if (existing) {
    return existing;
  }

  const initialState: MermaidViewState = {
    scale: 1,
    x: 0,
    y: 0,
    dragging: false,
    dragPointerId: null,
    dragStartX: 0,
    dragStartY: 0,
    originX: 0,
    originY: 0,
  };
  mermaidViewStates.set(wrapper, initialState);
  return initialState;
};

const syncMermaidView = (wrapper: HTMLElement) => {
  const state = getMermaidViewState(wrapper);
  const transformLayer = wrapper.querySelector(".mermaid-transform-layer") as HTMLElement | null;
  const viewport = wrapper.querySelector(".mermaid-viewport") as HTMLElement | null;
  const scaleIndicator = wrapper.querySelector(".mermaid-scale-indicator") as HTMLElement | null;

  if (transformLayer) {
    transformLayer.style.transformOrigin = "center top";
    transformLayer.style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
  }

  if (viewport) {
    viewport.dataset.mermaidScale = state.scale.toFixed(2);
    viewport.dataset.mermaidDragging = state.dragging ? "true" : "false";
  }

  if (scaleIndicator) {
    scaleIndicator.textContent = `${Math.round(state.scale * 100)}%`;
  }
};

const setMermaidScale = (wrapper: HTMLElement, nextScale: number) => {
  const state = getMermaidViewState(wrapper);
  state.scale = clampMermaidScale(nextScale);
  if (state.scale <= 1) {
    state.x = 0;
    state.y = 0;
    state.dragging = false;
    state.dragPointerId = null;
  }
  syncMermaidView(wrapper);
};

const resetMermaidView = (wrapper: HTMLElement) => {
  const state = getMermaidViewState(wrapper);
  state.scale = 1;
  state.x = 0;
  state.y = 0;
  state.dragging = false;
  state.dragPointerId = null;
  syncMermaidView(wrapper);
};

const stopMermaidDrag = (wrapper: HTMLElement) => {
  const viewport = wrapper.querySelector(".mermaid-viewport") as HTMLElement | null;
  const state = getMermaidViewState(wrapper);
  if (!state.dragging) {
    return;
  }
  const pointerId = state.dragPointerId;
  state.dragging = false;
  state.dragPointerId = null;
  if (viewport && pointerId !== null) {
    viewport.releasePointerCapture?.(pointerId);
  }
  syncMermaidView(wrapper);
};

const handleMermaidPointerDown = (event: PointerEvent) => {
  const target = event.target as HTMLElement | null;
  const viewport = target?.closest(".mermaid-viewport") as HTMLElement | null;
  if (!viewport) {
    return;
  }
  const wrapper = viewport.closest(".mermaid-wrapper") as HTMLElement | null;
  if (!wrapper) {
    return;
  }
  const state = getMermaidViewState(wrapper);
  if (state.scale <= 1) {
    return;
  }

  state.dragging = true;
  state.dragPointerId = event.pointerId;
  state.dragStartX = event.clientX;
  state.dragStartY = event.clientY;
  state.originX = state.x;
  state.originY = state.y;
  viewport.setPointerCapture?.(event.pointerId);
  syncMermaidView(wrapper);
  event.preventDefault();
};

const handleMermaidPointerMove = (event: PointerEvent) => {
  const target = event.target as HTMLElement | null;
  const viewport = target?.closest(".mermaid-viewport") as HTMLElement | null;
  if (!viewport) {
    return;
  }
  const wrapper = viewport.closest(".mermaid-wrapper") as HTMLElement | null;
  if (!wrapper) {
    return;
  }
  const state = getMermaidViewState(wrapper);
  if (!state.dragging || state.dragPointerId !== event.pointerId) {
    return;
  }

  state.x = state.originX + (event.clientX - state.dragStartX);
  state.y = state.originY + (event.clientY - state.dragStartY);
  syncMermaidView(wrapper);
  event.preventDefault();
};

const handleMermaidPointerEnd = (event: PointerEvent) => {
  const target = event.target as HTMLElement | null;
  const viewport = target?.closest(".mermaid-viewport") as HTMLElement | null;
  const wrapper = viewport?.closest(".mermaid-wrapper") as HTMLElement | null;
  if (!wrapper) {
    return;
  }
  const state = getMermaidViewState(wrapper);
  if (state.dragPointerId !== event.pointerId) {
    return;
  }
  stopMermaidDrag(wrapper);
};

// 处理 Markdown 内容区域的点击事件（图片 Lightbox + 代码块全屏）
const handleMarkdownClick = async (event: MouseEvent) => {
  const target = event.target as HTMLElement;

  // 点击图片 - 打开 Lightbox
  if (target.tagName === "IMG") {
    const img = target as HTMLImageElement;
    const src = img.getAttribute("src") || "";
    const alt = img.getAttribute("alt") || "";
    if (src && markdownEnhancementsRef.value) {
      markdownEnhancementsRef.value.openLightbox(src, alt);
    }
    return;
  }

  // 点击代码块全屏按钮
  const fullscreenBtn = target.closest(".code-block-fullscreen");
  if (fullscreenBtn) {
    const wrapper = fullscreenBtn.closest(".code-block-wrapper");
    if (wrapper) {
      const codeEl = wrapper.querySelector("code");
      const preEl = wrapper.querySelector("pre");
      const langEl = wrapper.querySelector(".code-block-lang");

      if (codeEl && preEl && markdownEnhancementsRef.value) {
        const html = codeEl.innerHTML;
        const lang = langEl?.textContent || "plaintext";
        const rawCode = preEl.textContent || "";
        markdownEnhancementsRef.value.openCodeFullscreen(html, lang, rawCode);
      }
    }
    return;
  }

  const mermaidActionButton = target.closest("[data-mermaid-action]");
  if (mermaidActionButton) {
    const wrapper = mermaidActionButton.closest(".mermaid-wrapper") as HTMLElement | null;
    if (!wrapper) {
      return;
    }

    const action = mermaidActionButton.getAttribute("data-mermaid-action");
    const encodedCode = wrapper.getAttribute("data-mermaid-code") || "";
    const source = decodeURIComponent(encodedCode);
    const svgEl = wrapper.querySelector(".mermaid-content svg") as SVGElement | null;

    if (action === "copy-source") {
      if (!source) {
        return;
      }
      try {
        await navigator.clipboard.writeText(source);
        wrapper.setAttribute("data-mermaid-copy-state", "success");
      } catch (error) {
        console.error("Failed to copy Mermaid source:", error);
        wrapper.setAttribute("data-mermaid-copy-state", "error");
      }
      window.setTimeout(() => {
        if (wrapper.isConnected) {
          wrapper.removeAttribute("data-mermaid-copy-state");
        }
      }, 2000);
      return;
    }

    if (action === "zoom-in") {
      setMermaidScale(wrapper, getMermaidViewState(wrapper).scale + MERMAID_SCALE_STEP);
      return;
    }

    if (action === "zoom-out") {
      setMermaidScale(wrapper, getMermaidViewState(wrapper).scale - MERMAID_SCALE_STEP);
      return;
    }

    if (action === "reset-zoom") {
      resetMermaidView(wrapper);
      return;
    }

    if (!svgEl) {
      return;
    }

    if (action === "download-svg") {
      try {
        const serializer = new XMLSerializer();
        const svgNode = svgEl.cloneNode(true) as SVGElement;
        if (!svgNode.getAttribute("xmlns")) {
          svgNode.setAttribute("xmlns", "http://www.w3.org/2000/svg");
        }
        const svgMarkup = serializer.serializeToString(svgNode);
        const blob = new Blob([svgMarkup], {
          type: "image/svg+xml;charset=utf-8",
        });
        const objectUrl = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = objectUrl;
        link.download = `${wrapper.getAttribute("data-mermaid-id") || "mermaid-diagram"}.svg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(objectUrl);
      } catch (error) {
        console.error("Failed to download Mermaid SVG:", error);
      }
      return;
    }

    if (action === "fullscreen" && markdownEnhancementsRef.value) {
      markdownEnhancementsRef.value.openMermaidFullscreen(svgEl.outerHTML, source, {
        closeLabel: t("mermaid.close_fullscreen"),
      });
    }
  }
};

// For backward compatibility
const messageContent = computed(() => props.message.content as MessageContent);
const attachmentsContent = computed(
  () => props.message.content as AttachmentsContent,
);
const collapsedPreview = computed(() => {
  const text = messageContent.value?.content?.replace(/\s+/g, " ").trim() || "";
  if (!text) {
    return t("Message collapsed");
  }
  return text.length > 140 ? `${text.slice(0, 140)}...` : text;
});
const messageFlashClass = computed(() =>
  props.flashToken ? "session-search-hit-flash" : "",
);
const messageKeysAttr = computed(
  () => `|${(props.messageKeys ?? []).join("|")}|`,
);

const { relativeTime } = useRelativeTime();

// 只有 assistant 消息才需要 Mermaid 渲染能力（autoRender = true）
// user/tool/step 消息不需要，避免创建无用的 MutationObserver 和 watcher
const isAssistant = props.message.type === "assistant";

const { createMermaidPlaceholderId } = useMermaidRenderer({
  markdownRef,
  getContent: isAssistant ? () => messageContent.value?.content : undefined,
  autoRender: isAssistant,
});

// 共用一个 markdown 渲染器，assistant 消息渲染 mermaid，user 消息不渲染
const { renderMarkdown } = useMarkdownRenderer({
  createMermaidPlaceholderId,
  renderMermaid: isAssistant,
  getMermaidLabels: () => ({
    toolbar: t("mermaid.toolbar"),
    fullscreen: t("mermaid.fullscreen"),
    copySource: t("mermaid.copy_source"),
    downloadSvg: t("mermaid.download_svg"),
    zoomIn: t("mermaid.zoom_in"),
    zoomOut: t("mermaid.zoom_out"),
    resetZoom: t("mermaid.reset_zoom"),
  }),
});

// 用户消息：纯文本显示，不渲染 Markdown/Mermaid/公式
// 只做 HTML 转义 + 换行保留，避免用户输入的语法被误渲染
const escapeUserText = (text: string): string => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML.replace(/\n/g, '<br>');
};

// assistant 消息解析：走完整 Markdown 渲染管线
let _lastParsedContent = "";
let _lastParsedResult: ReturnType<typeof parseChatMessageContent> | null = null;

const parseContent = (markdown: string) => {
  if (markdown === _lastParsedContent && _lastParsedResult) {
    return _lastParsedResult;
  }
  const result = parseChatMessageContent(markdown, {
    renderMarkdown,
    transformSrc,
  });
  _lastParsedContent = markdown;
  _lastParsedResult = result;
  return result;
};

onBeforeUnmount(() => {
  if (!markdownRef.value) {
    return;
  }
  Array.from(markdownRef.value.querySelectorAll(".mermaid-wrapper")).forEach(node => {
    stopMermaidDrag(node as HTMLElement);
  });
});
</script>

<style src="../assets/chat-message-renderer.css"></style>

<style>
.duration-300 {
  animation-duration: 0.3s;
  transition-duration: 0.3s;
}

.msg-enter-left {
  animation: msgSlideLeft 0.3s ease-out both;
}
.msg-enter-right {
  animation: msgSlideRight 0.3s ease-out both;
}

@keyframes msgSlideLeft {
  from {
    opacity: 0;
    transform: translateX(-8px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
@keyframes msgSlideRight {
  from {
    opacity: 0;
    transform: translateX(8px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.session-search-hit-flash {
  animation: session-search-hit-flash 1s ease-in-out 2;
}

@keyframes session-search-hit-flash {
  0% {
    box-shadow: 0 0 0 0 rgba(79, 70, 229, 0);
  }
  25% {
    box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.5);
  }
  50% {
    box-shadow: 0 0 0 0 rgba(79, 70, 229, 0);
  }
  75% {
    box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.45);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(96, 165, 250, 0);
  }
}
</style>

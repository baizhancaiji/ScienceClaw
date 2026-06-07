<template>
  <!-- 图片 Lightbox -->
  <Teleport to="body">
    <Transition name="lightbox">
      <div
        v-if="lightboxVisible"
        class="lightbox-overlay"
        @click="closeLightbox"
        @keydown.esc="closeLightbox"
      >
        <div class="lightbox-container" @click.stop>
          <!-- 关闭按钮 -->
          <button class="lightbox-close" @click="closeLightbox" title="关闭 (Esc)">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>

          <!-- 缩放控制 -->
          <div class="lightbox-controls">
            <button @click="zoomOut" title="缩小 (-)" class="lightbox-control-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="8" y1="11" x2="14" y2="11"></line>
              </svg>
            </button>
            <span class="lightbox-zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
            <button @click="zoomIn" title="放大 (+)" class="lightbox-control-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="11" y1="8" x2="11" y2="14"></line>
                <line x1="8" y1="11" x2="14" y2="11"></line>
              </svg>
            </button>
            <button @click="resetZoom" title="重置 (0)" class="lightbox-control-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3.5 3.5v6h6"></path>
                <path d="M20.5 20.5v-6h-6"></path>
                <path d="M4 12a8 8 0 0 1 14-5.3"></path>
                <path d="M20 12a8 8 0 0 1-14 5.3"></path>
              </svg>
            </button>
          </div>

          <!-- 图片容器 -->
          <div
            class="lightbox-image-wrapper"
            @mousedown="startDrag"
            @mousemove="onDrag"
            @mouseup="endDrag"
            @mouseleave="endDrag"
            @wheel.prevent="onWheel"
          >
            <img
              ref="lightboxImage"
              :src="lightboxSrc"
              :alt="lightboxAlt"
              class="lightbox-image"
              :style="imageStyle"
              draggable="false"
            />
          </div>

          <!-- 图片信息 -->
          <div class="lightbox-info" v-if="lightboxAlt">
            {{ lightboxAlt }}
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 代码块全屏 -->
  <Teleport to="body">
    <Transition name="fullscreen">
      <div
        v-if="codeFullscreenVisible"
        class="code-fullscreen-overlay"
        @keydown.esc="closeCodeFullscreen"
      >
        <div class="code-fullscreen-container">
          <!-- 头部 -->
          <div class="code-fullscreen-header">
            <div class="code-fullscreen-lang">
              <span class="code-fullscreen-dot"></span>
              {{ codeFullscreenLang }}
            </div>
            <div class="code-fullscreen-actions">
              <button @click="copyCodeFullscreen" class="code-fullscreen-btn" :class="{ 'code-fullscreen-btn--copied': codeCopied }">
                <svg v-if="!codeCopied" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                {{ codeCopied ? '已复制' : '复制代码' }}
              </button>
              <button @click="closeCodeFullscreen" class="code-fullscreen-btn code-fullscreen-btn--close">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                退出全屏 (Esc)
              </button>
            </div>
          </div>

          <!-- 代码内容 -->
          <div class="code-fullscreen-content">
            <pre class="code-fullscreen-pre"><code class="hljs" v-html="codeFullscreenHtml"></code></pre>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- Mermaid 全屏 -->
  <Teleport to="body">
    <Transition name="fullscreen">
      <div
        v-if="mermaidFullscreenVisible"
        class="mermaid-fullscreen-overlay"
        @keydown.esc="closeMermaidFullscreen"
      >
        <div class="mermaid-fullscreen-container">
          <div class="mermaid-fullscreen-header">
            <div
              class="mermaid-fullscreen-toolbar"
              role="toolbar"
              :aria-label="t('mermaid.toolbar')"
            >
              <button
                class="mermaid-fullscreen-btn"
                type="button"
                :title="t('mermaid.zoom_out')"
                :aria-label="t('mermaid.zoom_out')"
                data-mermaid-fullscreen-action="zoom-out"
                @click="zoomOutMermaidFullscreen"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="8" y1="11" x2="14" y2="11"></line>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </button>
              <span class="mermaid-fullscreen-scale-indicator">{{ mermaidFullscreenScaleLabel }}</span>
              <button
                class="mermaid-fullscreen-btn"
                type="button"
                :title="t('mermaid.zoom_in')"
                :aria-label="t('mermaid.zoom_in')"
                data-mermaid-fullscreen-action="zoom-in"
                @click="zoomInMermaidFullscreen"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="11" y1="8" x2="11" y2="14"></line>
                  <line x1="8" y1="11" x2="14" y2="11"></line>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </button>
              <button
                class="mermaid-fullscreen-btn"
                type="button"
                :title="t('mermaid.reset_zoom')"
                :aria-label="t('mermaid.reset_zoom')"
                data-mermaid-fullscreen-action="reset-zoom"
                @click="resetMermaidFullscreenView"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3.5 3.5v6h6"></path>
                  <path d="M20.5 20.5v-6h-6"></path>
                  <path d="M4 12a8 8 0 0 1 14-5.3"></path>
                  <path d="M20 12a8 8 0 0 1-14 5.3"></path>
                </svg>
              </button>
              <button
                class="mermaid-fullscreen-btn"
                type="button"
                :title="t('mermaid.copy_source')"
                :aria-label="t('mermaid.copy_source')"
                data-mermaid-fullscreen-action="copy-source"
                @click="copyMermaidFullscreenSource"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
              </button>
              <button
                class="mermaid-fullscreen-btn"
                type="button"
                :title="t('mermaid.download_svg')"
                :aria-label="t('mermaid.download_svg')"
                data-mermaid-fullscreen-action="download-svg"
                @click="downloadMermaidFullscreenSvg"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
              </button>
            </div>
            <button
              class="mermaid-fullscreen-close"
              type="button"
              :title="mermaidFullscreenCloseLabel"
              :aria-label="mermaidFullscreenCloseLabel"
              data-mermaid-fullscreen-action="close"
              @click="closeMermaidFullscreen"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div
            v-if="mermaidFullscreenFeedback"
            class="mermaid-fullscreen-feedback"
            :data-status="mermaidFullscreenFeedbackStatus"
            role="status"
          >
            {{ mermaidFullscreenFeedback }}
          </div>
          <div class="mermaid-fullscreen-content">
            <div
              ref="mermaidFullscreenViewport"
              class="mermaid-fullscreen-viewport"
              :data-mermaid-scale="mermaidFullscreenState.scale.toFixed(2)"
              :data-mermaid-dragging="mermaidFullscreenState.dragging ? 'true' : 'false'"
              @pointerdown="startMermaidFullscreenDrag"
              @pointermove="onMermaidFullscreenDrag"
              @pointerup="endMermaidFullscreenDrag"
              @pointercancel="endMermaidFullscreenDrag"
            >
              <div
                class="mermaid-fullscreen-transform-layer"
                :style="mermaidFullscreenTransformStyle"
              >
                <div
                  ref="mermaidFullscreenStage"
                  class="mermaid-fullscreen-stage"
                  v-html="mermaidFullscreenSvg"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 文字选中菜单 -->
  <Teleport to="body">
    <Transition name="selection-menu">
      <div
        v-if="selectionMenuVisible"
        class="selection-menu"
        :style="selectionMenuStyle"
      >
        <button @click="copySelection" class="selection-menu-btn" title="复制">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <span>复制</span>
        </button>
        <button @click="searchSelection" class="selection-menu-btn" title="搜索">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <span>搜索</span>
        </button>
        <button @click="translateSelection" class="selection-menu-btn" title="翻译">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 8l6 6"></path>
            <path d="M4 14l6-6 2-3"></path>
            <path d="M2 5h12"></path>
            <path d="M7 2v3"></path>
            <path d="M22 22l-5-10-5 10"></path>
            <path d="M14 18h6"></path>
          </svg>
          <span>翻译</span>
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import { useI18n } from 'vue-i18n';

interface MermaidFullscreenOptions {
  closeLabel?: string;
}

interface MermaidFullscreenViewState {
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
const MERMAID_FULLSCREEN_FEEDBACK_DURATION_MS = 2000;

const { t } = useI18n();

// ==================== Lightbox ====================
const lightboxVisible = ref(false);
const lightboxSrc = ref('');
const lightboxAlt = ref('');
const zoomLevel = ref(1);
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const imagePosition = ref({ x: 0, y: 0 });
const lightboxImage = ref<HTMLImageElement | null>(null);

const imageStyle = computed(() => ({
  transform: `translate(${imagePosition.value.x}px, ${imagePosition.value.y}px) scale(${zoomLevel.value})`,
  transition: isDragging.value ? 'none' : 'transform 0.2s ease-out',
}));

const openLightbox = (src: string, alt: string = '') => {
  lightboxSrc.value = src;
  lightboxAlt.value = alt;
  lightboxVisible.value = true;
  zoomLevel.value = 1;
  imagePosition.value = { x: 0, y: 0 };
  document.body.style.overflow = 'hidden';
};

const closeLightbox = () => {
  lightboxVisible.value = false;
  document.body.style.overflow = '';
};

const zoomIn = () => {
  if (zoomLevel.value < 5) {
    zoomLevel.value = Math.min(5, zoomLevel.value + 0.25);
  }
};

const zoomOut = () => {
  if (zoomLevel.value > 0.25) {
    zoomLevel.value = Math.max(0.25, zoomLevel.value - 0.25);
    if (zoomLevel.value <= 1) {
      imagePosition.value = { x: 0, y: 0 };
    }
  }
};

const resetZoom = () => {
  zoomLevel.value = 1;
  imagePosition.value = { x: 0, y: 0 };
};

const startDrag = (e: MouseEvent) => {
  if (zoomLevel.value > 1) {
    isDragging.value = true;
    dragStart.value = {
      x: e.clientX - imagePosition.value.x,
      y: e.clientY - imagePosition.value.y,
    };
  }
};

const onDrag = (e: MouseEvent) => {
  if (isDragging.value) {
    imagePosition.value = {
      x: e.clientX - dragStart.value.x,
      y: e.clientY - dragStart.value.y,
    };
  }
};

const endDrag = () => {
  isDragging.value = false;
};

const onWheel = (e: WheelEvent) => {
  if (e.deltaY < 0) {
    zoomIn();
  } else {
    zoomOut();
  }
};

// ==================== Code Fullscreen ====================
const codeFullscreenVisible = ref(false);
const codeFullscreenHtml = ref('');
const codeFullscreenLang = ref('plaintext');
const codeFullscreenRaw = ref('');
const codeCopied = ref(false);
const mermaidFullscreenVisible = ref(false);
const mermaidFullscreenSvg = ref('');
const mermaidFullscreenSource = ref('');
const mermaidFullscreenCloseLabel = ref('Close');
const mermaidFullscreenFeedback = ref('');
const mermaidFullscreenFeedbackStatus = ref<'success' | 'error' | ''>('');
const mermaidFullscreenViewport = ref<HTMLElement | null>(null);
const mermaidFullscreenStage = ref<HTMLElement | null>(null);
let mermaidFullscreenFeedbackTimer: ReturnType<typeof setTimeout> | null = null;

const createMermaidFullscreenState = (): MermaidFullscreenViewState => ({
  scale: 1,
  x: 0,
  y: 0,
  dragging: false,
  dragPointerId: null,
  dragStartX: 0,
  dragStartY: 0,
  originX: 0,
  originY: 0,
});

const mermaidFullscreenState = reactive<MermaidFullscreenViewState>(
  createMermaidFullscreenState(),
);

const mermaidFullscreenScaleLabel = computed(
  () => `${Math.round(mermaidFullscreenState.scale * 100)}%`,
);

const mermaidFullscreenTransformStyle = computed(() => ({
  transformOrigin: 'center top',
  transform: `translate(${mermaidFullscreenState.x}px, ${mermaidFullscreenState.y}px) scale(${mermaidFullscreenState.scale})`,
  transition: mermaidFullscreenState.dragging ? 'none' : 'transform 0.2s ease',
}));

const openCodeFullscreen = (html: string, lang: string, rawCode: string) => {
  codeFullscreenHtml.value = html;
  codeFullscreenLang.value = lang || 'plaintext';
  codeFullscreenRaw.value = rawCode;
  codeFullscreenVisible.value = true;
  codeCopied.value = false;
  document.body.style.overflow = 'hidden';
};

const closeCodeFullscreen = () => {
  codeFullscreenVisible.value = false;
  document.body.style.overflow = '';
};

const copyCodeFullscreen = async () => {
  try {
    await navigator.clipboard.writeText(codeFullscreenRaw.value);
    codeCopied.value = true;
    setTimeout(() => {
      codeCopied.value = false;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy:', err);
  }
};

const openMermaidFullscreen = (
  svg: string,
  source: string,
  options?: MermaidFullscreenOptions,
) => {
  mermaidFullscreenSvg.value = svg;
  mermaidFullscreenSource.value = source;
  mermaidFullscreenCloseLabel.value = options?.closeLabel || 'Close';
  resetMermaidFullscreenView();
  clearMermaidFullscreenFeedback();
  mermaidFullscreenVisible.value = true;
  document.body.style.overflow = 'hidden';
};

const closeMermaidFullscreen = () => {
  stopMermaidFullscreenDrag();
  mermaidFullscreenVisible.value = false;
  mermaidFullscreenSvg.value = '';
  mermaidFullscreenSource.value = '';
  clearMermaidFullscreenFeedback();
  resetMermaidFullscreenView();
  document.body.style.overflow = '';
};

const clampMermaidFullscreenScale = (scale: number) =>
  Math.min(MERMAID_MAX_SCALE, Math.max(MERMAID_MIN_SCALE, scale));

const clearMermaidFullscreenFeedback = () => {
  if (mermaidFullscreenFeedbackTimer) {
    clearTimeout(mermaidFullscreenFeedbackTimer);
    mermaidFullscreenFeedbackTimer = null;
  }
  mermaidFullscreenFeedback.value = '';
  mermaidFullscreenFeedbackStatus.value = '';
};

const setMermaidFullscreenFeedback = (
  message: string,
  status: 'success' | 'error',
) => {
  clearMermaidFullscreenFeedback();
  mermaidFullscreenFeedback.value = message;
  mermaidFullscreenFeedbackStatus.value = status;
  mermaidFullscreenFeedbackTimer = setTimeout(() => {
    mermaidFullscreenFeedback.value = '';
    mermaidFullscreenFeedbackStatus.value = '';
    mermaidFullscreenFeedbackTimer = null;
  }, MERMAID_FULLSCREEN_FEEDBACK_DURATION_MS);
};

const setMermaidFullscreenScale = (nextScale: number) => {
  mermaidFullscreenState.scale = clampMermaidFullscreenScale(nextScale);
  if (mermaidFullscreenState.scale <= 1) {
    mermaidFullscreenState.x = 0;
    mermaidFullscreenState.y = 0;
    mermaidFullscreenState.dragging = false;
    mermaidFullscreenState.dragPointerId = null;
  }
};

const resetMermaidFullscreenView = () => {
  Object.assign(mermaidFullscreenState, createMermaidFullscreenState());
};

const zoomInMermaidFullscreen = () => {
  setMermaidFullscreenScale(
    mermaidFullscreenState.scale + MERMAID_SCALE_STEP,
  );
};

const zoomOutMermaidFullscreen = () => {
  setMermaidFullscreenScale(
    mermaidFullscreenState.scale - MERMAID_SCALE_STEP,
  );
};

const stopMermaidFullscreenDrag = () => {
  if (!mermaidFullscreenState.dragging) {
    return;
  }
  const pointerId = mermaidFullscreenState.dragPointerId;
  mermaidFullscreenState.dragging = false;
  mermaidFullscreenState.dragPointerId = null;
  if (mermaidFullscreenViewport.value && pointerId !== null) {
    mermaidFullscreenViewport.value.releasePointerCapture?.(pointerId);
  }
};

const startMermaidFullscreenDrag = (event: PointerEvent) => {
  if (mermaidFullscreenState.scale <= 1) {
    return;
  }
  mermaidFullscreenState.dragging = true;
  mermaidFullscreenState.dragPointerId = event.pointerId;
  mermaidFullscreenState.dragStartX = event.clientX;
  mermaidFullscreenState.dragStartY = event.clientY;
  mermaidFullscreenState.originX = mermaidFullscreenState.x;
  mermaidFullscreenState.originY = mermaidFullscreenState.y;
  mermaidFullscreenViewport.value?.setPointerCapture?.(event.pointerId);
  event.preventDefault();
};

const onMermaidFullscreenDrag = (event: PointerEvent) => {
  if (
    !mermaidFullscreenState.dragging ||
    mermaidFullscreenState.dragPointerId !== event.pointerId
  ) {
    return;
  }
  mermaidFullscreenState.x =
    mermaidFullscreenState.originX +
    (event.clientX - mermaidFullscreenState.dragStartX);
  mermaidFullscreenState.y =
    mermaidFullscreenState.originY +
    (event.clientY - mermaidFullscreenState.dragStartY);
  event.preventDefault();
};

const endMermaidFullscreenDrag = (event: PointerEvent) => {
  if (mermaidFullscreenState.dragPointerId !== event.pointerId) {
    return;
  }
  stopMermaidFullscreenDrag();
};

const copyMermaidFullscreenSource = async () => {
  if (!mermaidFullscreenSource.value) {
    return;
  }
  try {
    await navigator.clipboard.writeText(mermaidFullscreenSource.value);
    setMermaidFullscreenFeedback(t('mermaid.copy_source_success'), 'success');
  } catch (error) {
    console.error('Failed to copy Mermaid source:', error);
    setMermaidFullscreenFeedback(t('mermaid.copy_source_failed'), 'error');
  }
};

const downloadMermaidFullscreenSvg = async () => {
  const svgEl = mermaidFullscreenStage.value?.querySelector('svg') as
    | SVGElement
    | null;
  if (!svgEl) {
    setMermaidFullscreenFeedback(t('mermaid.download_svg_failed'), 'error');
    return;
  }

  try {
    const serializer = new XMLSerializer();
    const svgNode = svgEl.cloneNode(true) as SVGElement;
    if (!svgNode.getAttribute('xmlns')) {
      svgNode.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    }
    const svgMarkup = serializer.serializeToString(svgNode);
    const blob = new Blob([svgMarkup], {
      type: 'image/svg+xml;charset=utf-8',
    });
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = 'mermaid-diagram.svg';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(objectUrl);
    setMermaidFullscreenFeedback(t('mermaid.download_svg_success'), 'success');
  } catch (error) {
    console.error('Failed to download Mermaid SVG:', error);
    setMermaidFullscreenFeedback(t('mermaid.download_svg_failed'), 'error');
  }
};

// ==================== Selection Menu ====================
const selectionMenuVisible = ref(false);
const selectionMenuStyle = ref({ top: '0px', left: '0px' });
let selectedText = '';
let hideTimeout: ReturnType<typeof setTimeout> | null = null;

const showSelectionMenu = (x: number, y: number, text: string) => {
  if (hideTimeout) {
    clearTimeout(hideTimeout);
  }
  selectedText = text;

  // 计算菜单位置，确保不超出视口
  const menuWidth = 150;
  const menuHeight = 40;
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;

  let left = x;
  let top = y + 10;

  if (left + menuWidth > viewportWidth) {
    left = viewportWidth - menuWidth - 10;
  }
  if (top + menuHeight > viewportHeight) {
    top = y - menuHeight - 10;
  }

  selectionMenuStyle.value = {
    top: `${top}px`,
    left: `${left}px`,
  };
  selectionMenuVisible.value = true;
};

const hideSelectionMenu = () => {
  hideTimeout = setTimeout(() => {
    selectionMenuVisible.value = false;
  }, 100);
};

const copySelection = async () => {
  try {
    await navigator.clipboard.writeText(selectedText);
    selectionMenuVisible.value = false;
  } catch (err) {
    console.error('Failed to copy:', err);
  }
};

const searchSelection = () => {
  const query = encodeURIComponent(selectedText);
  window.open(`https://www.google.com/search?q=${query}`, '_blank');
  selectionMenuVisible.value = false;
};

const translateSelection = () => {
  const query = encodeURIComponent(selectedText);
  window.open(`https://translate.google.com/?text=${query}`, '_blank');
  selectionMenuVisible.value = false;
};

// ==================== 事件监听 ====================
const handleSelection = () => {
  const selection = window.getSelection();
  if (selection && selection.toString().trim()) {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    showSelectionMenu(rect.left + rect.width / 2, rect.bottom, selection.toString().trim());
  } else {
    hideSelectionMenu();
  }
};

const handleKeydown = (e: KeyboardEvent) => {
  if (lightboxVisible.value) {
    if (e.key === 'Escape') closeLightbox();
    if (e.key === '+' || e.key === '=') zoomIn();
    if (e.key === '-') zoomOut();
    if (e.key === '0') resetZoom();
  }
  if (codeFullscreenVisible.value && e.key === 'Escape') {
    closeCodeFullscreen();
  }
  if (mermaidFullscreenVisible.value) {
    if (e.key === 'Escape') {
      closeMermaidFullscreen();
    }
    if (e.key === '+' || e.key === '=') {
      zoomInMermaidFullscreen();
    }
    if (e.key === '-') {
      zoomOutMermaidFullscreen();
    }
    if (e.key === '0') {
      resetMermaidFullscreenView();
    }
  }
};

onMounted(() => {
  document.addEventListener('selectionchange', handleSelection);
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('selectionchange', handleSelection);
  document.removeEventListener('keydown', handleKeydown);
  if (hideTimeout) {
    clearTimeout(hideTimeout);
  }
  clearMermaidFullscreenFeedback();
});

// 暴露方法给父组件
defineExpose({
  openLightbox,
  closeLightbox,
  openCodeFullscreen,
  closeCodeFullscreen,
  openMermaidFullscreen,
  closeMermaidFullscreen,
});
</script>

<style scoped>
/* ==================== Lightbox ==================== */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.lightbox-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.lightbox-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 10;
}

.lightbox-close:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

.lightbox-controls {
  position: absolute;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(0, 0, 0, 0.6);
  padding: 8px 16px;
  border-radius: 30px;
  backdrop-filter: blur(10px);
  z-index: 10;
}

.lightbox-control-btn {
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.lightbox-control-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.lightbox-zoom-level {
  color: white;
  font-size: 13px;
  font-weight: 500;
  min-width: 50px;
  text-align: center;
}

.lightbox-image-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  overflow: hidden;
}

.lightbox-image-wrapper:active {
  cursor: grabbing;
}

.lightbox-image {
  max-width: 95%;
  max-height: 85%;
  object-fit: contain;
  user-select: none;
  border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.lightbox-info {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  text-align: center;
  max-width: 80%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ==================== Code Fullscreen ==================== */
.code-fullscreen-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: var(--chat-code-surface);
  display: flex;
  flex-direction: column;
}

.code-fullscreen-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.code-fullscreen-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--chat-code-fullscreen-header);
  border-bottom: 1px solid var(--chat-code-fullscreen-border);
}

.code-fullscreen-lang {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--chat-code-control-text);
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.code-fullscreen-dot {
  width: 10px;
  height: 10px;
  background: linear-gradient(135deg, var(--chat-state-success-from), var(--chat-state-success-to));
  border-radius: 50%;
  box-shadow: 0 0 10px var(--chat-state-success-shadow);
}

.code-fullscreen-actions {
  display: flex;
  gap: 10px;
}

.code-fullscreen-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: var(--chat-code-fullscreen-control-text);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.code-fullscreen-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.code-fullscreen-btn--copied {
  color: var(--chat-state-success-from);
}

.code-fullscreen-btn--close {
  background: var(--chat-state-error-surface);
  color: var(--chat-state-error-text);
}

.code-fullscreen-btn--close:hover {
  background: var(--chat-state-error-surface-strong);
}

.code-fullscreen-content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

.code-fullscreen-pre {
  margin: 0;
  font-size: 16px;
  line-height: 1.7;
}

.code-fullscreen-pre code {
  font-family: 'Fira Code', 'JetBrains Mono', 'SF Mono', Consolas, Monaco, monospace;
}

.mermaid-fullscreen-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(15, 23, 42, 0.9);
  display: flex;
  align-items: stretch;
  justify-content: center;
  backdrop-filter: blur(8px);
}

.mermaid-fullscreen-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.mermaid-fullscreen-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px 0;
  flex-wrap: wrap;
}

.mermaid-fullscreen-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.mermaid-fullscreen-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}

.mermaid-fullscreen-btn:hover,
.mermaid-fullscreen-close:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.mermaid-fullscreen-scale-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 60px;
  height: 40px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.18);
  color: #fff;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.mermaid-fullscreen-close {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.mermaid-fullscreen-feedback {
  margin: 12px 20px 0;
  padding: 12px 14px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.4;
  border: 1px solid transparent;
}

.mermaid-fullscreen-feedback[data-status='success'] {
  background: var(--chat-state-success-surface);
  border-color: var(--chat-state-success-border);
  color: var(--chat-state-success-text);
}

.mermaid-fullscreen-feedback[data-status='error'] {
  background: var(--chat-state-error-surface);
  border-color: var(--chat-state-error-border);
  color: var(--chat-state-error-text);
}

.mermaid-fullscreen-content {
  flex: 1;
  min-height: 0;
  padding: 20px 24px 28px;
}

.mermaid-fullscreen-viewport {
  width: 100%;
  height: 100%;
  overflow: auto;
  border-radius: 12px;
  background: #fff;
  padding: 24px;
  touch-action: none;
}

.mermaid-fullscreen-viewport[data-mermaid-scale]:not([data-mermaid-scale='1.00']) {
  cursor: grab;
}

.mermaid-fullscreen-viewport[data-mermaid-dragging='true'] {
  cursor: grabbing;
}

.mermaid-fullscreen-transform-layer {
  min-width: fit-content;
  will-change: transform;
}

.mermaid-fullscreen-stage {
  min-width: fit-content;
}

.mermaid-fullscreen-stage :deep(svg) {
  display: block;
  max-width: none;
  margin: 0 auto;
}

/* ==================== Selection Menu ==================== */
.selection-menu {
  position: fixed;
  z-index: 10000;
  display: flex;
  gap: 2px;
  padding: 6px;
  background: var(--chat-selection-surface);
  border-radius: 10px;
  box-shadow:
    0 10px 25px -5px rgba(0, 0, 0, 0.15),
    0 4px 10px -3px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--chat-selection-border);
  animation: selectionMenuIn 0.15s ease-out;
}

@keyframes selectionMenuIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.selection-menu-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--chat-selection-text);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.selection-menu-btn:hover {
  background: linear-gradient(135deg, var(--chat-selection-hover-bg-from), var(--chat-selection-hover-bg-to));
  color: var(--chat-selection-hover-text);
}

.selection-menu-btn:active {
  transform: scale(0.95);
}

/* ==================== Transitions ==================== */
.lightbox-enter-active,
.lightbox-leave-active,
.fullscreen-enter-active,
.fullscreen-leave-active {
  transition: all 0.3s ease;
}

.lightbox-enter-from,
.lightbox-leave-to,
.fullscreen-enter-from,
.fullscreen-leave-to {
  opacity: 0;
}

.lightbox-enter-from .lightbox-image,
.lightbox-leave-to .lightbox-image {
  transform: scale(0.9);
}

.selection-menu-enter-active,
.selection-menu-leave-active {
  transition: all 0.15s ease;
}

.selection-menu-enter-from,
.selection-menu-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>

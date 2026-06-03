<template>
  <div class="msg-footer-bar">
    <!-- 操作按钮组 - 圆角胶囊风格 -->
    <div class="msg-actions-capsule">
      <button
        class="msg-action-btn"
        :class="{ 'msg-action-btn--liked': feedback === 'like' }"
        @click="emit('toggleFeedback', 'like')"
        :title="feedback === 'like' ? '取消' : '有帮助'"
      >
        <ThumbsUpIcon class="w-4 h-4" :class="{ 'fill-current': feedback === 'like' }" />
      </button>
      <button
        class="msg-action-btn"
        :class="{ 'msg-action-btn--disliked': feedback === 'dislike' }"
        @click="emit('toggleFeedback', 'dislike')"
        :title="feedback === 'dislike' ? '取消' : '无帮助'"
      >
        <ThumbsDownIcon class="w-4 h-4" :class="{ 'fill-current': feedback === 'dislike' }" />
      </button>
      <div class="msg-action-divider"></div>
      <button
        class="msg-action-btn"
        :class="{ 'msg-action-btn--copied': isCopied }"
        @click="emit('copy')"
        :title="isCopied ? '已复制' : '复制'"
      >
        <CheckIcon v-if="isCopied" class="w-4 h-4" />
        <CopyIcon v-else class="w-4 h-4" />
      </button>
      <button
        class="msg-action-btn"
        :disabled="pdfDisabled || pdfExporting"
        @click="emit('convertToPdf')"
        :title="pdfExporting ? t('pdf_export.exporting') : t('pdf_export.action')"
        :aria-label="pdfExporting ? t('pdf_export.exporting') : t('pdf_export.action')"
      >
        <LoaderCircleIcon v-if="pdfExporting" class="w-4 h-4 animate-spin" />
        <PdfIcon v-else :size="16" />
      </button>
      <template v-if="roundFileCount > 0">
        <div class="msg-action-divider"></div>
        <button
          class="msg-action-btn msg-action-btn--files"
          @click="emit('showFiles')"
          :title="`查看本轮对话文件 (${roundFileCount})`"
        >
          <FolderOpen class="w-4 h-4" />
          <span class="text-[11px] font-medium ml-0.5 tabular-nums">{{ roundFileCount }}</span>
        </button>
      </template>
    </div>

    <!-- 统计信息组 - 统一胶囊风格 -->
    <div v-if="hasStatistics" class="msg-stats-capsule">
      <!-- Duration -->
      <span v-if="statistics?.total_duration_ms" class="msg-stat-tag msg-stat-tag--time msg-stat-with-tooltip" :data-tooltip="`耗时: ${formatDuration(statistics.total_duration_ms)}`">
        <ClockIcon class="w-3.5 h-3.5" />
        <span class="tabular-nums">{{ formatDuration(statistics.total_duration_ms) }}</span>
      </span>
      <!-- Divider after duration (if any item follows) -->
      <div v-if="statistics?.total_duration_ms && (statistics?.tool_call_count || statistics?.input_tokens || statistics?.output_tokens)" class="msg-stat-divider"></div>
      <!-- Tool calls -->
      <span v-if="statistics?.tool_call_count" class="msg-stat-tag msg-stat-tag--tools msg-stat-with-tooltip" :data-tooltip="`工具调用次数: ${statistics.tool_call_count}次`">
        <WrenchIcon class="w-3.5 h-3.5" />
        <span class="tabular-nums">{{ statistics.tool_call_count }}次</span>
      </span>
      <!-- Divider after tool_call (if tokens follow) -->
      <div v-if="statistics?.tool_call_count && (statistics?.input_tokens || statistics?.output_tokens)" class="msg-stat-divider"></div>
      <!-- Tokens: Input ↓ / Output ↑ -->
      <span v-if="statistics?.input_tokens || statistics?.output_tokens" class="msg-stat-tag msg-stat-tag--tokens msg-stat-with-tooltip" :data-tooltip="`输入Token: ${statistics.input_tokens || 0} | 输出Token: ${statistics.output_tokens || 0}`">
        <ArrowDownIcon class="w-3.5 h-3.5 opacity-70" />
        <span class="tabular-nums">{{ formatTokenCount(statistics.input_tokens || 0) }}</span>
        <span class="opacity-40 mx-0.5">·</span>
        <ArrowUpIcon class="w-3.5 h-3.5 opacity-70" />
        <span class="tabular-nums">{{ formatTokenCount(statistics.output_tokens || 0) }}</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  ArrowDownIcon,
  ArrowUpIcon,
  CheckIcon,
  ClockIcon,
  CopyIcon,
  FolderOpen,
  LoaderCircleIcon,
  ThumbsDownIcon,
  ThumbsUpIcon,
  WrenchIcon,
} from 'lucide-vue-next';
import { useI18n } from 'vue-i18n';
import PdfIcon from './icons/PdfIcon.vue';
import type { StatisticsData } from '../types/event';

type FeedbackType = 'like' | 'dislike';

const props = defineProps<{
  feedback: FeedbackType | null;
  isCopied: boolean;
  roundFileCount: number;
  statistics?: StatisticsData;
  pdfExporting?: boolean;
  pdfDisabled?: boolean;
}>();

const { t } = useI18n();

const emit = defineEmits<{
  (e: 'toggleFeedback', feedback: FeedbackType): void;
  (e: 'copy'): void;
  (e: 'convertToPdf'): void;
  (e: 'showFiles'): void;
}>();

const hasStatistics = computed(() => Boolean(
  props.statistics && (
    props.statistics.total_duration_ms
    || props.statistics.tool_call_count
    || props.statistics.input_tokens
    || props.statistics.output_tokens
  ),
));

// 格式化耗时
const formatDuration = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const mins = Math.floor(ms / 60000);
  const secs = ((ms % 60000) / 1000).toFixed(0);
  return `${mins}m ${secs}s`;
};

// 格式化 token 数量
const formatTokenCount = (count: number): string => {
  if (count < 1000) return `${count}`;
  return `${(count / 1000).toFixed(1)}K`;
};
</script>

<style>
/* 底部操作栏 */
.msg-footer-bar {
  @apply mt-1.5 flex items-center gap-2 opacity-60 transition-opacity duration-200;
}

.group:hover .msg-footer-bar {
  @apply opacity-100;
}

.msg-actions-capsule {
  @apply inline-flex items-center gap-0.5 h-9 px-1.5;
  @apply bg-gray-100/80 dark:bg-gray-800/60;
  @apply backdrop-blur-sm;
  @apply border border-gray-200/50 dark:border-gray-700/50;
  @apply rounded-full;
}

.msg-action-btn {
  @apply relative flex items-center justify-center;
  @apply w-7 h-7 rounded-md;
  @apply text-gray-400 dark:text-gray-500;
  @apply hover:bg-gray-200/60 dark:hover:bg-gray-700/60;
  @apply hover:text-gray-600 dark:hover:text-gray-300;
  @apply transition-all duration-150;
  @apply active:scale-95;
}

.msg-action-btn--liked {
  @apply bg-green-100/80 dark:bg-green-900/30;
  @apply text-green-600 dark:text-green-400;
  @apply hover:bg-green-200/80 dark:hover:bg-green-900/40;
}

.msg-action-btn--disliked {
  @apply bg-red-100/80 dark:bg-red-900/30;
  @apply text-red-600 dark:text-red-400;
  @apply hover:bg-red-200/80 dark:hover:bg-red-900/40;
}

.msg-action-btn--copied {
  @apply text-green-600 dark:text-green-400;
}

.msg-action-btn--files {
  @apply flex items-center gap-0;
  @apply w-auto px-1.5;
  @apply text-blue-600 dark:text-blue-400;
  @apply hover:bg-blue-100/80 dark:hover:bg-blue-900/30;
}

.msg-action-divider {
  @apply w-px h-4 mx-0.5;
  @apply bg-gray-300/60 dark:bg-gray-600/60;
}

.msg-stats-capsule {
  @apply inline-flex items-center gap-0 h-9 px-2;
  @apply bg-gray-100/80 dark:bg-gray-800/60;
  @apply backdrop-blur-sm;
  @apply border border-gray-200/50 dark:border-gray-700/50;
  @apply rounded-full;
}

.msg-stat-tag {
  @apply inline-flex items-center gap-1;
  @apply text-[12px] font-medium;
}

.msg-stat-tag--time { @apply text-blue-600 dark:text-blue-400; }
.msg-stat-tag--tools { @apply text-emerald-600 dark:text-emerald-400; }
.msg-stat-tag--tokens { @apply text-violet-600 dark:text-violet-400; }

.msg-stat-with-tooltip {
  position: relative;
  cursor: default;
}

.msg-stat-with-tooltip::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
  white-space: nowrap;
  color: #fff;
  background: rgba(30, 41, 59, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0.2s ease;
  z-index: 100;
  pointer-events: none;
}

.dark .msg-stat-with-tooltip::after {
  background: rgba(51, 65, 85, 0.95);
}

.msg-stat-with-tooltip::before {
  content: '';
  position: absolute;
  bottom: calc(100% + 2px);
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(30, 41, 59, 0.95);
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0.2s ease;
  z-index: 100;
}

.dark .msg-stat-with-tooltip::before {
  border-top-color: rgba(51, 65, 85, 0.95);
}

.msg-stat-with-tooltip:hover::after,
.msg-stat-with-tooltip:hover::before {
  opacity: 1;
  visibility: visible;
}

.msg-stat-divider {
  @apply w-px h-3.5 mx-3;
  @apply bg-gray-300/60 dark:bg-gray-600/60;
}

@media (max-width: 640px) {
  .msg-footer-bar {
    @apply opacity-100 flex-wrap;
  }

  .msg-action-btn { @apply w-8 h-8; }
  .msg-stats-capsule { @apply mt-1; }
}
</style>

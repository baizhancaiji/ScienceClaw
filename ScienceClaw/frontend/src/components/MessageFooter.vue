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
        @click="emit('convertToPdf')"
        title="转成PDF"
      >
        <PdfIcon :size="16" />
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
  ThumbsDownIcon,
  ThumbsUpIcon,
  WrenchIcon,
} from 'lucide-vue-next';
import PdfIcon from './icons/PdfIcon.vue';
import type { StatisticsData } from '../types/event';

type FeedbackType = 'like' | 'dislike';

const props = defineProps<{
  feedback: FeedbackType | null;
  isCopied: boolean;
  roundFileCount: number;
  statistics?: StatisticsData;
}>();

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

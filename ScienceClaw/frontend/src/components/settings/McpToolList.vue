<template>
  <div class="rounded-xl border border-gray-100 bg-white shadow-sm dark:border-gray-700/50 dark:bg-gray-800/50">
    <div class="flex items-center justify-between gap-3 border-b border-gray-100 px-4 py-3 dark:border-gray-700/50">
      <div>
        <h4 class="text-sm font-semibold text-gray-800 dark:text-gray-100">Tool Preview</h4>
        <p class="text-xs text-gray-500 dark:text-gray-400">{{ tools.length }} cached tools</p>
      </div>
      <button
        type="button"
        class="inline-flex h-8 items-center gap-1.5 rounded-lg border border-gray-200 px-3 text-xs font-semibold text-gray-600 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
        :disabled="disabled || refreshing"
        @click="$emit('refresh')"
      >
        <RefreshCw class="size-3.5" :class="{ 'animate-spin': refreshing }" />
        Refresh
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-8">
      <Loader2 class="size-6 animate-spin text-gray-300" />
    </div>
    <div v-else-if="tools.length === 0" class="flex flex-col items-center justify-center py-8 text-center">
      <Wrench class="mb-2 size-6 text-gray-300 dark:text-gray-500" />
      <p class="text-sm font-semibold text-gray-400 dark:text-gray-500">No tools cached</p>
    </div>
    <div v-else class="max-h-72 overflow-y-auto">
      <div
        v-for="tool in tools"
        :key="tool.id"
        class="grid grid-cols-[1fr_auto] gap-3 border-b border-gray-100 p-4 last:border-b-0 dark:border-gray-700/50"
      >
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <span class="truncate text-sm font-semibold text-gray-800 dark:text-gray-100">{{ tool.display_name }}</span>
            <span
              v-if="tool.removed"
              class="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-600 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-400"
            >
              removed
            </span>
          </div>
          <p class="mt-1 truncate font-mono text-[11px] text-gray-500 dark:text-gray-400">{{ tool.canonical_name }}</p>
          <p v-if="tool.description" class="mt-2 line-clamp-2 text-xs text-gray-500 dark:text-gray-400">{{ tool.description }}</p>
          <div class="mt-2 flex flex-wrap gap-2 text-[11px] text-gray-400 dark:text-gray-500">
            <span>{{ schemaFieldCount(tool) }} schema fields</span>
            <span v-if="tool.last_seen_at">seen {{ formatTime(tool.last_seen_at) }}</span>
          </div>
        </div>

        <button
          type="button"
          class="inline-flex size-8 items-center justify-center rounded-lg border transition-colors disabled:cursor-not-allowed disabled:opacity-50"
          :class="tool.enabled ? 'border-emerald-200 bg-emerald-50 text-emerald-600 hover:bg-emerald-100 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-400' : 'border-gray-200 bg-white text-gray-400 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-500'"
          :title="tool.enabled ? 'Disable tool' : 'Enable tool'"
          :disabled="disabled || togglingToolId === tool.id || tool.removed"
          @click="$emit('toggle', tool)"
        >
          <Loader2 v-if="togglingToolId === tool.id" class="size-4 animate-spin" />
          <Power v-else class="size-4" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Loader2, Power, RefreshCw, Wrench } from 'lucide-vue-next';
import type { MCPTool } from '@/api/mcp';

defineProps<{
  tools: MCPTool[];
  loading: boolean;
  refreshing: boolean;
  disabled: boolean;
  togglingToolId: string | null;
}>();

defineEmits<{
  refresh: [];
  toggle: [tool: MCPTool];
}>();

const schemaFieldCount = (tool: MCPTool): number => {
  const properties = (tool.input_schema_raw as { properties?: unknown }).properties;
  if (!properties || typeof properties !== 'object') {
    return 0;
  }
  return Object.keys(properties).length;
};

const formatTime = (timestamp: number): string => {
  return new Date(timestamp * 1000).toLocaleString();
};
</script>

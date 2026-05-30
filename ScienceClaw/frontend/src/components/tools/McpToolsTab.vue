<template>
  <div class="flex-1 overflow-y-auto bg-[#f8f9fb] p-5 dark:bg-[#111]">
    <div v-if="loading" class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 max-w-[1800px] mx-auto">
      <div
        v-for="i in 8"
        :key="i"
        class="rounded-xl border border-gray-100 bg-white p-4 dark:border-gray-800 dark:bg-[#1e1e1e]"
      >
        <div class="mb-3 flex items-start gap-3">
          <div class="size-10 animate-pulse rounded-xl bg-gray-200 dark:bg-gray-700"></div>
          <div class="flex-1 space-y-2">
            <div class="h-4 w-2/3 animate-pulse rounded bg-gray-200 dark:bg-gray-700"></div>
            <div class="h-3 w-1/2 animate-pulse rounded bg-gray-100 dark:bg-gray-800"></div>
          </div>
        </div>
        <div class="space-y-2">
          <div class="h-3 animate-pulse rounded bg-gray-100 dark:bg-gray-800"></div>
          <div class="h-3 w-5/6 animate-pulse rounded bg-gray-100 dark:bg-gray-800"></div>
        </div>
      </div>
    </div>

    <div v-else-if="errorMessage" class="flex h-full flex-col items-center justify-center gap-3 text-center text-[var(--text-tertiary)]">
      <div class="flex size-16 items-center justify-center rounded-2xl bg-red-50 dark:bg-red-950/20">
        <AlertCircle :size="28" class="text-red-400 dark:text-red-500" />
      </div>
      <div>
        <p class="text-sm font-semibold text-[var(--text-secondary)]">Failed to load MCP tools</p>
        <p class="mt-1 max-w-md text-xs opacity-70">{{ errorMessage }}</p>
      </div>
      <button
        type="button"
        class="rounded-lg border border-gray-200 bg-white px-4 py-2 text-xs font-semibold text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:bg-[#1e1e1e] dark:text-gray-300 dark:hover:bg-gray-800"
        @click="loadTools"
      >
        Retry
      </button>
    </div>

    <div v-else-if="filteredTools.length === 0" class="flex h-full flex-col items-center justify-center gap-3 text-center text-[var(--text-tertiary)]">
      <div class="flex size-16 items-center justify-center rounded-2xl bg-gray-100 dark:bg-gray-800">
        <Search v-if="searchQuery" :size="28" class="text-gray-300 dark:text-gray-600" />
        <PlugZap v-else :size="28" class="text-gray-300 dark:text-gray-600" />
      </div>
      <div>
        <p class="text-sm font-semibold text-[var(--text-secondary)]">
          {{ searchQuery ? `No MCP tools match "${searchQuery}"` : 'No enabled MCP tools' }}
        </p>
        <p v-if="!searchQuery" class="mt-1 text-xs opacity-60">Enable tools from an MCP server to browse them here</p>
      </div>
    </div>

    <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 max-w-[1800px] mx-auto">
      <article
        v-for="(tool, idx) in filteredTools"
        :key="tool.id"
        class="tool-card group relative overflow-hidden rounded-xl border border-gray-100 bg-white dark:border-gray-800 dark:bg-[#1e1e1e]"
        :style="{ '--delay': `${Math.min(idx, 20) * 30}ms` }"
      >
        <div class="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100">
          <div class="absolute -inset-px rounded-xl bg-gradient-to-r from-sky-400/20 via-emerald-400/20 to-lime-400/20"></div>
        </div>

        <div class="relative p-4">
          <div class="mb-2.5 flex items-start gap-3">
            <div
              class="flex size-10 flex-shrink-0 items-center justify-center rounded-xl text-sm font-bold text-white shadow-lg transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3"
              :style="{ background: getToolGradient(tool.canonical_name || tool.display_name) }"
            >
              {{ tool.display_name.charAt(0).toUpperCase() }}
            </div>
            <div class="min-w-0 flex-1">
              <h3 class="truncate text-sm font-semibold text-[var(--text-primary)] transition-all duration-300 group-hover:bg-gradient-to-r group-hover:from-sky-600 group-hover:to-emerald-600 group-hover:bg-clip-text group-hover:text-transparent">
                {{ tool.display_name }}
              </h3>
              <span class="mt-0.5 inline-block rounded-full bg-gray-100 px-2 py-0.5 font-mono text-[10px] text-[var(--text-tertiary)] dark:bg-gray-800">
                {{ tool.tool_slug || tool.original_name }}
              </span>
            </div>
          </div>

          <p class="line-clamp-2 min-h-[2.5rem] text-xs leading-relaxed text-[var(--text-secondary)]">
            {{ tool.description || 'No description available' }}
          </p>

          <div class="mt-3 flex items-center justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate font-mono text-[10px] text-[var(--text-tertiary)]">{{ tool.canonical_name }}</p>
              <p class="mt-1 text-[10px] text-[var(--text-tertiary)]">{{ schemaFieldCount(tool) }} schema fields</p>
            </div>
            <span
              class="flex-shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold"
              :class="tool.enabled ? 'border-emerald-200 bg-emerald-50 text-emerald-600 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-400' : 'border-gray-200 bg-gray-50 text-gray-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400'"
            >
              {{ tool.enabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { AlertCircle, PlugZap, Search } from 'lucide-vue-next';
import { listMCPTools, type MCPTool } from '@/api/mcp';

const props = defineProps<{
  searchQuery: string;
}>();

const emit = defineEmits<{
  countChange: [count: number];
}>();

const tools = ref<MCPTool[]>([]);
const loading = ref(false);
const errorMessage = ref('');

const gradientPalette = [
  'linear-gradient(135deg, #0ea5e9, #10b981)',
  'linear-gradient(135deg, #22c55e, #84cc16)',
  'linear-gradient(135deg, #14b8a6, #06b6d4)',
  'linear-gradient(135deg, #3b82f6, #0ea5e9)',
  'linear-gradient(135deg, #6366f1, #14b8a6)',
  'linear-gradient(135deg, #f59e0b, #22c55e)',
];

const filteredTools = computed(() => {
  const q = props.searchQuery.trim().toLowerCase();
  if (!q) {
    return tools.value;
  }
  return tools.value.filter((tool) => {
    return [
      tool.display_name,
      tool.canonical_name,
      tool.original_name,
      tool.tool_slug,
      tool.description,
      tool.server_id,
    ].some((value) => value.toLowerCase().includes(q));
  });
});

const loadTools = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    tools.value = await listMCPTools();
  } catch (error) {
    const maybeError = error as { message?: string };
    errorMessage.value = maybeError.message || 'Unknown MCP tools error';
    tools.value = [];
  } finally {
    loading.value = false;
    emit('countChange', tools.value.length);
  }
};

const schemaFieldCount = (tool: MCPTool): number => {
  const properties = (tool.input_schema_raw as { properties?: unknown }).properties;
  if (!properties || typeof properties !== 'object') {
    return 0;
  }
  return Object.keys(properties).length;
};

const getToolGradient = (name: string) => {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return gradientPalette[Math.abs(hash) % gradientPalette.length];
};

onMounted(loadTools);
watch(tools, (value) => emit('countChange', value.length));
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tool-card {
  animation: cardFadeIn 0.4s ease-out both;
  animation-delay: var(--delay, 0ms);
}

@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.tool-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px -8px rgba(0, 0, 0, 0.08), 0 4px 12px -4px rgba(0, 0, 0, 0.04);
}
</style>

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
        <p class="text-sm font-semibold text-[var(--text-secondary)]">{{ t('Failed to load MCP tools') }}</p>
        <p class="mt-1 max-w-md text-xs opacity-70">{{ errorMessage }}</p>
      </div>
      <button
        type="button"
        class="rounded-lg border border-gray-200 bg-white px-4 py-2 text-xs font-semibold text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:bg-[#1e1e1e] dark:text-gray-300 dark:hover:bg-gray-800"
        @click="loadTools"
      >
        {{ t('Retry') }}
      </button>
    </div>

    <div v-else-if="filteredTools.length === 0" class="flex h-full flex-col items-center justify-center gap-3 text-center text-[var(--text-tertiary)]">
      <div class="flex size-16 items-center justify-center rounded-2xl bg-gray-100 dark:bg-gray-800">
        <Search v-if="searchQuery" :size="28" class="text-gray-300 dark:text-gray-600" />
        <PlugZap v-else :size="28" class="text-gray-300 dark:text-gray-600" />
      </div>
      <div>
        <p class="text-sm font-semibold text-[var(--text-secondary)]">
          {{ searchQuery ? t('No MCP tools match "{query}"', { query: searchQuery }) : t('No enabled MCP tools') }}
        </p>
        <p v-if="!searchQuery" class="mt-1 text-xs opacity-60">{{ t('Enable tools from an MCP server to browse them here') }}</p>
      </div>
    </div>

    <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 max-w-[1800px] mx-auto">
      <McpToolCard
        v-for="(tool, idx) in filteredTools"
        :key="tool.id"
        :tool="tool"
        :index="idx"
        @open="selectedTool = $event"
      />
    </div>

    <McpToolSchemaDrawer :tool="selectedTool" @close="selectedTool = null" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { AlertCircle, PlugZap, Search } from 'lucide-vue-next';
import { listMCPTools, type MCPTool } from '@/api/mcp';
import McpToolSchemaDrawer from '@/components/settings/McpToolSchemaDrawer.vue';
import McpToolCard from '@/components/tools/McpToolCard.vue';

const { t } = useI18n();

const props = defineProps<{
  searchQuery: string;
}>();

const emit = defineEmits<{
  countChange: [count: number];
}>();

const tools = ref<MCPTool[]>([]);
const loading = ref(false);
const errorMessage = ref('');
const selectedTool = ref<MCPTool | null>(null);

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
    errorMessage.value = maybeError.message || t('Unknown MCP tools error');
    tools.value = [];
  } finally {
    loading.value = false;
    emit('countChange', tools.value.length);
  }
};

onMounted(loadTools);
watch(tools, (value) => emit('countChange', value.length));
</script>

<style scoped>
</style>

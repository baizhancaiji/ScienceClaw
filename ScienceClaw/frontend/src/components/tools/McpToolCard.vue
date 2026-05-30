<template>
  <article
    class="tool-card group relative overflow-hidden rounded-xl border border-gray-100 bg-white text-left transition-transform dark:border-gray-800 dark:bg-[#1e1e1e]"
    :style="{ '--delay': `${Math.min(index, 20) * 30}ms` }"
  >
    <div class="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100">
      <div class="absolute -inset-px rounded-xl bg-gradient-to-r from-sky-400/20 via-emerald-400/20 to-lime-400/20"></div>
    </div>

    <button type="button" class="relative block h-full w-full p-4 text-left" @click="$emit('open', tool)">
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
          <div class="mt-1 flex flex-wrap items-center gap-1.5 text-[10px] text-[var(--text-tertiary)]">
            <span>{{ schemaSummary.fieldCount }} schema fields</span>
            <span v-if="schemaSummary.payloadMode" class="rounded-full bg-amber-50 px-1.5 py-0.5 font-semibold text-amber-600 dark:bg-amber-950/30 dark:text-amber-400">
              payload mode
            </span>
          </div>
        </div>
        <span
          class="flex-shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold"
          :class="tool.enabled ? 'border-emerald-200 bg-emerald-50 text-emerald-600 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-400' : 'border-gray-200 bg-gray-50 text-gray-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400'"
        >
          {{ tool.enabled ? 'Enabled' : 'Disabled' }}
        </span>
      </div>
    </button>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { MCPTool } from '@/api/mcp';

const props = defineProps<{
  tool: MCPTool;
  index: number;
}>();

defineEmits<{
  open: [tool: MCPTool];
}>();

const complexSchemaKeys = ['oneOf', 'anyOf', 'allOf', 'not', '$ref', 'patternProperties'];
const gradientPalette = [
  'linear-gradient(135deg, #0ea5e9, #10b981)',
  'linear-gradient(135deg, #22c55e, #84cc16)',
  'linear-gradient(135deg, #14b8a6, #06b6d4)',
  'linear-gradient(135deg, #3b82f6, #0ea5e9)',
  'linear-gradient(135deg, #6366f1, #14b8a6)',
  'linear-gradient(135deg, #f59e0b, #22c55e)',
];

const schemaSummary = computed(() => {
  const schema = props.tool.input_schema_raw;
  const properties = (schema as { properties?: unknown }).properties;
  return {
    fieldCount: properties && typeof properties === 'object' ? Object.keys(properties).length : 0,
    payloadMode: isPayloadModeSchema(schema),
  };
});

const isPayloadModeSchema = (schema: unknown): boolean => {
  if (!schema || typeof schema !== 'object') {
    return false;
  }
  const record = schema as Record<string, unknown>;
  if (complexSchemaKeys.some((key) => key in record)) {
    return true;
  }
  if (record.type === 'array') {
    return isPayloadModeSchema(record.items);
  }
  if (record.type !== 'object') {
    return true;
  }
  if (!record.properties || typeof record.properties !== 'object' || Array.isArray(record.properties)) {
    return false;
  }
  return Object.values(record.properties).some((value) => {
    return isPayloadModeSchema(value);
  });
};

const getToolGradient = (name: string) => {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return gradientPalette[Math.abs(hash) % gradientPalette.length];
};
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

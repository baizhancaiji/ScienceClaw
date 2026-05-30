<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="tool" class="fixed inset-0 z-[9999] flex justify-end">
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="$emit('close')"></div>
        <aside class="relative flex h-full w-full max-w-xl flex-col bg-white shadow-2xl dark:bg-[#1e1e1e]">
          <header class="border-b border-gray-100 px-5 py-4 dark:border-gray-800">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="text-[11px] font-semibold uppercase tracking-wide text-emerald-500">MCP tool schema</p>
                <h3 class="mt-1 truncate text-base font-semibold text-[var(--text-primary)]">{{ tool.display_name }}</h3>
                <p class="mt-1 truncate font-mono text-[11px] text-[var(--text-tertiary)]">{{ tool.canonical_name }}</p>
              </div>
              <button
                type="button"
                class="inline-flex size-8 items-center justify-center rounded-lg text-[var(--text-tertiary)] transition-colors hover:bg-gray-100 hover:text-[var(--text-primary)] dark:hover:bg-gray-800"
                title="Close"
                @click="$emit('close')"
              >
                <X class="size-4" />
              </button>
            </div>
          </header>

          <div class="flex-1 overflow-y-auto px-5 py-4">
            <section v-if="payloadMode" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-900 dark:bg-amber-950/25">
              <div class="flex items-start gap-2">
                <AlertTriangle class="mt-0.5 size-4 flex-shrink-0 text-amber-600 dark:text-amber-400" />
                <div>
                  <p class="text-xs font-semibold text-amber-700 dark:text-amber-300">Payload mode</p>
                  <p class="mt-1 text-xs leading-relaxed text-amber-700/80 dark:text-amber-200/80">
                    This schema uses complex JSON Schema features. Pass arguments as a JSON object in <span class="font-mono">payload</span>.
                  </p>
                </div>
              </div>
            </section>

            <section class="mb-4 grid grid-cols-2 gap-3">
              <div class="rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-gray-800 dark:bg-[#151515]">
                <p class="text-[10px] font-semibold uppercase text-[var(--text-tertiary)]">Fields</p>
                <p class="mt-1 text-lg font-semibold text-[var(--text-primary)]">{{ fields.length }}</p>
              </div>
              <div class="rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-gray-800 dark:bg-[#151515]">
                <p class="text-[10px] font-semibold uppercase text-[var(--text-tertiary)]">Required</p>
                <p class="mt-1 text-lg font-semibold text-[var(--text-primary)]">{{ requiredFields.size }}</p>
              </div>
            </section>

            <section v-if="fields.length" class="space-y-3">
              <div
                v-for="field in fields"
                :key="field.name"
                class="rounded-lg border border-gray-100 bg-white p-3 dark:border-gray-800 dark:bg-[#181818]"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <span class="font-mono text-sm font-semibold text-[var(--text-primary)]">{{ field.name }}</span>
                  <span class="rounded-full bg-sky-50 px-2 py-0.5 font-mono text-[10px] font-semibold text-sky-600 dark:bg-sky-950/30 dark:text-sky-400">
                    {{ field.type }}
                  </span>
                  <span
                    v-if="field.required"
                    class="rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-semibold text-red-600 dark:bg-red-950/30 dark:text-red-400"
                  >
                    required
                  </span>
                  <span
                    v-if="field.enumValues.length"
                    class="rounded-full bg-purple-50 px-2 py-0.5 text-[10px] font-semibold text-purple-600 dark:bg-purple-950/30 dark:text-purple-400"
                  >
                    enum
                  </span>
                </div>
                <p v-if="field.description" class="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">{{ field.description }}</p>
                <div v-if="field.enumValues.length" class="mt-2 flex flex-wrap gap-1.5">
                  <span
                    v-for="value in field.enumValues"
                    :key="value"
                    class="rounded-md bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] text-[var(--text-secondary)] dark:bg-gray-800"
                  >
                    {{ value }}
                  </span>
                </div>
                <p v-if="field.defaultValue !== undefined" class="mt-2 text-[11px] text-[var(--text-tertiary)]">
                  default: <span class="font-mono">{{ formatDefault(field.defaultValue) }}</span>
                </p>
              </div>
            </section>

            <section v-else class="rounded-lg border border-gray-100 bg-gray-50 p-4 text-center dark:border-gray-800 dark:bg-[#151515]">
              <p class="text-sm font-semibold text-[var(--text-secondary)]">No named schema fields</p>
              <p class="mt-1 text-xs text-[var(--text-tertiary)]">
                {{ payloadMode ? 'Use payload mode for this tool.' : 'This tool does not declare input properties.' }}
              </p>
            </section>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { AlertTriangle, X } from 'lucide-vue-next';
import type { MCPTool } from '@/api/mcp';

const props = defineProps<{
  tool: MCPTool | null;
}>();

defineEmits<{
  close: [];
}>();

type SchemaRecord = Record<string, unknown>;

interface SchemaField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  enumValues: string[];
  defaultValue: unknown;
}

const complexSchemaKeys = ['oneOf', 'anyOf', 'allOf', 'not', '$ref', 'patternProperties'];

const schema = computed<SchemaRecord>(() => {
  return (props.tool?.input_schema_raw || {}) as SchemaRecord;
});

const requiredFields = computed(() => {
  const required = schema.value.required;
  return new Set(Array.isArray(required) ? required.filter((item): item is string => typeof item === 'string') : []);
});

const fields = computed<SchemaField[]>(() => {
  const properties = schema.value.properties;
  if (!properties || typeof properties !== 'object' || Array.isArray(properties)) {
    return [];
  }
  return Object.entries(properties as Record<string, unknown>).map(([name, value]) => {
    const fieldSchema = value && typeof value === 'object' && !Array.isArray(value) ? (value as SchemaRecord) : {};
    const enumValues = Array.isArray(fieldSchema.enum) ? fieldSchema.enum.map((item) => String(item)) : [];
    return {
      name,
      type: schemaTypeLabel(fieldSchema),
      required: requiredFields.value.has(name),
      description: typeof fieldSchema.description === 'string' ? fieldSchema.description : '',
      enumValues,
      defaultValue: fieldSchema.default,
    };
  });
});

const payloadMode = computed(() => isPayloadModeSchema(schema.value));

const isPayloadModeSchema = (value: unknown): boolean => {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const record = value as SchemaRecord;
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
  return Object.values(record.properties).some((entry) => {
    return isPayloadModeSchema(entry);
  });
};

const schemaTypeLabel = (fieldSchema: SchemaRecord): string => {
  if (Array.isArray(fieldSchema.type)) {
    return fieldSchema.type.map((item) => String(item)).join(' | ');
  }
  if (fieldSchema.type === 'array') {
    const items = fieldSchema.items;
    if (items && typeof items === 'object' && !Array.isArray(items)) {
      return `array<${schemaTypeLabel(items as SchemaRecord)}>`;
    }
    return 'array';
  }
  if (typeof fieldSchema.type === 'string') {
    return fieldSchema.type;
  }
  if (fieldSchema.enum) {
    return 'enum';
  }
  return 'any';
};

const formatDefault = (value: unknown): string => {
  if (typeof value === 'string') {
    return value;
  }
  return JSON.stringify(value);
};
</script>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s ease;
}

.drawer-enter-active aside,
.drawer-leave-active aside {
  transition: transform 0.22s ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from aside,
.drawer-leave-to aside {
  transform: translateX(24px);
}
</style>

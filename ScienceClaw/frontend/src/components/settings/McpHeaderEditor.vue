<template>
  <div class="grid gap-3">
    <div class="flex items-center justify-between">
      <label class="text-sm font-medium text-gray-700 dark:text-gray-200">{{ t('Headers') }} <span class="text-red-500">*</span></label>
      <button
        type="button"
        class="inline-flex h-8 items-center gap-1.5 rounded-lg border border-gray-200 px-3 text-xs font-medium text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
        @click="$emit('add')"
      >
        <Plus class="size-3.5" />
        {{ t('Header') }}
      </button>
    </div>

    <div
      v-for="(header, index) in headers"
      :key="index"
      class="grid grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)_auto] gap-2"
    >
      <input
        :value="header.name"
        class="h-10 min-w-0 rounded-lg border border-gray-200 bg-white px-3 font-mono text-sm text-gray-800 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
        placeholder="X-API-Key"
        @input="updateHeader(index, 'name', $event)"
      />
      <input
        :value="header.value"
        type="password"
        class="h-10 min-w-0 rounded-lg border border-gray-200 bg-white px-3 font-mono text-sm text-gray-800 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
        :placeholder="header.existing ? t('Leave all existing values empty to keep them') : t('Value')"
        @input="updateHeader(index, 'value', $event)"
      />
      <button
        type="button"
        class="inline-flex size-10 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
        :title="t('Remove')"
        @click="$emit('remove', index)"
      >
        <X class="size-4" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Plus, X } from 'lucide-vue-next';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

export type MCPHeaderForm = {
  name: string;
  value: string;
  existing: boolean;
};

defineProps<{
  headers: MCPHeaderForm[];
}>();

const emit = defineEmits<{
  add: [];
  remove: [index: number];
  update: [index: number, field: 'name' | 'value', value: string];
}>();

const updateHeader = (index: number, field: 'name' | 'value', event: Event) => {
  const target = event.target as HTMLInputElement;
  emit('update', index, field, target.value);
};
</script>

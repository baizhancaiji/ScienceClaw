<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="fixed inset-0 z-[9999] flex justify-end">
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="$emit('close')"></div>
        <aside class="relative flex h-full w-full max-w-2xl flex-col bg-white shadow-2xl dark:bg-gray-900">
          <header class="border-b border-gray-100 bg-gray-50/70 px-6 py-4 dark:border-gray-800 dark:bg-gray-800/30">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-[11px] font-semibold uppercase tracking-wide text-blue-500">HTTPS MCP server</p>
                <h3 class="mt-1 flex items-center gap-2 text-lg font-bold text-gray-800 dark:text-gray-100">
                  <Server class="size-5 text-blue-500" />
                  {{ editing ? 'Edit MCP Server' : 'Add MCP Server' }}
                </h3>
              </div>
              <button
                type="button"
                class="inline-flex size-8 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-100"
                title="Close"
                @click="$emit('close')"
              >
                <X class="size-4" />
              </button>
            </div>
          </header>

          <div class="flex-1 overflow-y-auto px-6 py-5">
            <div class="flex flex-col gap-4">
              <div class="grid gap-2">
                <label class="text-sm font-medium text-gray-700 dark:text-gray-200">Name <span class="text-red-500">*</span></label>
                <input
                  :value="form.name"
                  class="h-10 rounded-lg border border-gray-200 bg-white px-3 text-sm text-gray-800 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                  placeholder="GitHub MCP"
                  @input="updateField('name', $event)"
                />
              </div>

              <div class="grid gap-2">
                <label class="text-sm font-medium text-gray-700 dark:text-gray-200">Endpoint URL <span class="text-red-500">*</span></label>
                <input
                  :value="form.endpoint_url"
                  class="h-10 rounded-lg border border-gray-200 bg-white px-3 font-mono text-sm text-gray-800 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                  placeholder="https://example.com/mcp"
                  @input="updateField('endpoint_url', $event)"
                />
              </div>

              <div class="grid gap-2">
                <label class="text-sm font-medium text-gray-700 dark:text-gray-200">Auth Mode</label>
                <div class="grid grid-cols-3 gap-2">
                  <button
                    v-for="mode in authModes"
                    :key="mode"
                    type="button"
                    class="h-9 rounded-lg border text-xs font-semibold transition-colors"
                    :class="form.auth_mode === mode ? 'border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300' : 'border-gray-200 bg-white text-gray-500 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800'"
                    @click="$emit('select-auth-mode', mode)"
                  >
                    {{ authModeTitle(mode) }}
                  </button>
                </div>
              </div>

              <div v-if="form.auth_mode === 'bearer'" class="grid gap-2">
                <label class="text-sm font-medium text-gray-700 dark:text-gray-200">
                  Bearer Token <span v-if="bearerRequired" class="text-red-500">*</span>
                </label>
                <input
                  :value="form.bearer_token"
                  type="password"
                  class="h-10 rounded-lg border border-gray-200 bg-white px-3 font-mono text-sm text-gray-800 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                  :placeholder="hasBearerToken ? 'Leave empty to keep existing token' : 'Token'"
                  @input="updateField('bearer_token', $event)"
                />
              </div>

              <McpHeaderEditor
                v-if="form.auth_mode === 'headers'"
                :headers="form.headers"
                @add="$emit('add-header')"
                @remove="$emit('remove-header', $event)"
                @update="forwardHeaderUpdate"
              />

              <label class="flex items-center gap-3 text-sm font-medium text-gray-700 dark:text-gray-200">
                <input
                  :checked="form.enabled"
                  type="checkbox"
                  class="size-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  @change="updateCheckedField('enabled', $event)"
                />
                Enabled
              </label>

              <div class="grid gap-2 rounded-xl border border-gray-100 bg-gray-50/70 p-3 dark:border-gray-800 dark:bg-gray-800/40">
                <label class="flex items-center gap-3 text-sm font-medium text-gray-700 dark:text-gray-200">
                  <input
                    :checked="form.verify_now"
                    type="checkbox"
                    class="size-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    @change="updateCheckedField('verify_now', $event)"
                  />
                  Verify after save
                </label>
                <label class="flex items-center gap-3 text-sm font-medium text-gray-700 dark:text-gray-200">
                  <input
                    :checked="form.refresh_after_save"
                    type="checkbox"
                    class="size-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    @change="updateCheckedField('refresh_after_save', $event)"
                  />
                  Refresh tools after save
                </label>
              </div>
            </div>
          </div>

          <footer class="border-t border-gray-100 bg-gray-50/70 px-6 py-4 dark:border-gray-800 dark:bg-gray-800/30">
            <div class="flex justify-end gap-3">
              <button
                type="button"
                class="h-10 rounded-xl border border-gray-200 bg-white px-4 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                @click="$emit('close')"
              >
                Cancel
              </button>
              <button
                type="button"
                class="inline-flex h-10 items-center gap-2 rounded-xl bg-blue-600 px-5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="saving"
                @click="$emit('save')"
              >
                <Loader2 v-if="saving" class="size-4 animate-spin" />
                <span>{{ editing ? 'Save' : 'Create' }}</span>
              </button>
            </div>
          </footer>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Loader2, Server, X } from 'lucide-vue-next';
import type { MCPAuthMode } from '@/api/mcp';
import McpHeaderEditor, { type MCPHeaderForm } from './McpHeaderEditor.vue';

export type MCPServerForm = {
  name: string;
  endpoint_url: string;
  auth_mode: MCPAuthMode;
  bearer_token: string;
  headers: MCPHeaderForm[];
  enabled: boolean;
  verify_now: boolean;
  refresh_after_save: boolean;
};

const props = defineProps<{
  open: boolean;
  editing: boolean;
  saving: boolean;
  hasBearerToken: boolean;
  form: MCPServerForm;
}>();

const emit = defineEmits<{
  close: [];
  save: [];
  'add-header': [];
  'remove-header': [index: number];
  'update-header': [index: number, field: 'name' | 'value', value: string];
  'select-auth-mode': [mode: MCPAuthMode];
  'update-field': [field: keyof MCPServerForm, value: string | boolean];
}>();

const authModes: MCPAuthMode[] = ['none', 'bearer', 'headers'];

const bearerRequired = computed(() => {
  return props.form.auth_mode === 'bearer' && (!props.editing || !props.hasBearerToken);
});

const authModeTitle = (mode: MCPAuthMode): string => {
  if (mode === 'bearer') return 'Bearer';
  if (mode === 'headers') return 'Headers';
  return 'None';
};

const updateField = (field: keyof MCPServerForm, event: Event) => {
  const target = event.target as HTMLInputElement;
  emitUpdate(field, target.value);
};

const updateCheckedField = (field: keyof MCPServerForm, event: Event) => {
  const target = event.target as HTMLInputElement;
  emitUpdate(field, target.checked);
};

const forwardHeaderUpdate = (index: number, field: 'name' | 'value', value: string) => {
  emit('update-header', index, field, value);
};

const emitUpdate = (field: keyof MCPServerForm, value: string | boolean) => {
  emit('update-field', field, value);
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

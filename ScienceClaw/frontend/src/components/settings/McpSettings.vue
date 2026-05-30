<template>
  <div class="flex flex-col gap-5 py-2 px-1 w-full">
    <div class="flex items-center justify-between gap-3 px-1">
      <h3 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider flex items-center gap-2 flex-1">
        MCP Servers
        <span class="h-px flex-1 bg-gradient-to-r from-gray-200 dark:from-gray-700 to-transparent"></span>
      </h3>
      <button
        type="button"
        class="inline-flex h-9 items-center gap-2 rounded-xl bg-blue-600 px-4 text-xs font-semibold text-white shadow-sm shadow-blue-500/20 transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="loading || saving"
        @click="openEditor(null)"
      >
        <Plus class="size-3.5" />
        Add Server
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <Loader2 class="size-8 animate-spin text-gray-300" />
    </div>

    <div v-else class="flex flex-col gap-4">
      <div
        v-if="servers.length === 0"
        class="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-200 bg-gray-50/80 py-12 dark:border-gray-700 dark:bg-gray-800/30"
      >
        <Server class="mb-3 size-8 text-gray-300 dark:text-gray-500" />
        <p class="text-sm font-semibold text-gray-400 dark:text-gray-500">No MCP servers configured</p>
      </div>

      <div v-else class="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm dark:border-gray-700/50 dark:bg-gray-800/50">
        <div
          v-for="server in servers"
          :key="server.id"
          class="grid grid-cols-[1fr_auto] gap-3 border-b border-gray-100 p-4 last:border-b-0 dark:border-gray-700/50"
        >
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <span class="truncate text-sm font-semibold text-gray-800 dark:text-gray-100">{{ server.name }}</span>
              <span class="rounded-md bg-gray-100 px-2 py-0.5 font-mono text-[10px] text-gray-500 dark:bg-gray-700 dark:text-gray-300">
                {{ server.slug }}
              </span>
              <span class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase" :class="statusClass(server.verify_status)">
                <Circle class="size-2 fill-current" />
                {{ server.verify_status }}
              </span>
            </div>
            <div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
              <span class="max-w-full truncate font-mono">{{ server.endpoint_url }}</span>
              <span>{{ authModeLabel(server) }}</span>
              <span>{{ server.tool_count }} tools</span>
            </div>
            <p v-if="server.verify_error" class="mt-2 text-xs text-red-500">{{ server.verify_error }}</p>
          </div>

          <div class="flex items-center gap-1 self-start">
            <button
              type="button"
              class="inline-flex size-8 items-center justify-center rounded-lg border transition-colors"
              :class="server.enabled ? 'border-emerald-200 bg-emerald-50 text-emerald-600 hover:bg-emerald-100 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-400' : 'border-gray-200 bg-white text-gray-400 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-500'"
              :title="server.enabled ? 'Disable' : 'Enable'"
              :disabled="saving"
              @click="toggleServer(server)"
            >
              <Power class="size-4" />
            </button>
            <button
              type="button"
              class="inline-flex size-8 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-800 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-100"
              title="Edit"
              :disabled="saving"
              @click="openEditor(server)"
            >
              <Pencil class="size-4" />
            </button>
            <button
              type="button"
              class="inline-flex size-8 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-red-50 hover:text-red-600 dark:text-gray-400 dark:hover:bg-red-950/30 dark:hover:text-red-400"
              title="Delete"
              :disabled="saving"
              @click="confirmDelete(server)"
            >
              <Trash2 class="size-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <Dialog v-model:open="editorOpen">
      <DialogContent class="sm:max-w-[680px] p-0 overflow-hidden rounded-2xl border border-gray-200/60 bg-white shadow-2xl dark:border-gray-700/40 dark:bg-gray-900">
        <DialogHeader class="border-b border-gray-100 bg-gray-50/70 px-6 py-4 dark:border-gray-800 dark:bg-gray-800/30">
          <DialogTitle class="flex items-center gap-2 text-lg font-bold text-gray-800 dark:text-gray-100">
            <Server class="size-5 text-blue-500" />
            {{ editingServer ? 'Edit MCP Server' : 'Add MCP Server' }}
          </DialogTitle>
        </DialogHeader>

        <div class="flex max-h-[65vh] flex-col gap-4 overflow-y-auto px-6 py-5">
          <div class="grid gap-2">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-200">Name <span class="text-red-500">*</span></label>
            <input
              v-model.trim="form.name"
              class="h-10 rounded-lg border border-gray-200 bg-white px-3 text-sm text-gray-800 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
              placeholder="GitHub MCP"
            />
          </div>

          <div class="grid gap-2">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-200">Endpoint URL <span class="text-red-500">*</span></label>
            <input
              v-model.trim="form.endpoint_url"
              class="h-10 rounded-lg border border-gray-200 bg-white px-3 font-mono text-sm text-gray-800 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
              placeholder="https://example.com/mcp"
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
                @click="selectAuthMode(mode)"
              >
                {{ authModeTitle(mode) }}
              </button>
            </div>
          </div>

          <div v-if="form.auth_mode === 'bearer'" class="grid gap-2">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-200">
              Bearer Token <span v-if="!editingServer || !editingServer.has_bearer_token" class="text-red-500">*</span>
            </label>
            <input
              v-model="form.bearer_token"
              type="password"
              class="h-10 rounded-lg border border-gray-200 bg-white px-3 font-mono text-sm text-gray-800 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
              :placeholder="editingServer?.has_bearer_token ? 'Leave empty to keep existing token' : 'Token'"
            />
          </div>

          <div v-if="form.auth_mode === 'headers'" class="grid gap-3">
            <div class="flex items-center justify-between">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-200">Headers <span class="text-red-500">*</span></label>
              <button
                type="button"
                class="inline-flex h-8 items-center gap-1.5 rounded-lg border border-gray-200 px-3 text-xs font-medium text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                @click="addHeader"
              >
                <Plus class="size-3.5" />
                Header
              </button>
            </div>
            <div
              v-for="(header, index) in form.headers"
              :key="index"
              class="grid grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)_auto] gap-2"
            >
              <input
                v-model.trim="header.name"
                class="h-10 min-w-0 rounded-lg border border-gray-200 bg-white px-3 font-mono text-sm text-gray-800 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                placeholder="X-API-Key"
              />
              <input
                v-model="header.value"
                type="password"
                class="h-10 min-w-0 rounded-lg border border-gray-200 bg-white px-3 font-mono text-sm text-gray-800 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                :placeholder="header.existing ? 'Leave all existing values empty to keep them' : 'Value'"
              />
              <button
                type="button"
                class="inline-flex size-10 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
                title="Remove"
                @click="removeHeader(index)"
              >
                <X class="size-4" />
              </button>
            </div>
          </div>

          <label class="flex items-center gap-3 text-sm font-medium text-gray-700 dark:text-gray-200">
            <input
              v-model="form.enabled"
              type="checkbox"
              class="size-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Enabled
          </label>
        </div>

        <DialogFooter class="border-t border-gray-100 bg-gray-50/70 px-6 py-4 dark:border-gray-800 dark:bg-gray-800/30">
          <div class="flex w-full justify-end gap-3">
            <button
              type="button"
              class="h-10 rounded-xl border border-gray-200 bg-white px-4 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              @click="editorOpen = false"
            >
              Cancel
            </button>
            <button
              type="button"
              class="inline-flex h-10 items-center gap-2 rounded-xl bg-blue-600 px-5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="saving"
              @click="saveServer"
            >
              <Loader2 v-if="saving" class="size-4 animate-spin" />
              <span>{{ editingServer ? 'Save' : 'Create' }}</span>
            </button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { Circle, Loader2, Pencil, Plus, Power, Server, Trash2, X } from 'lucide-vue-next';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  createMCPServer,
  deleteMCPServer,
  listMCPServers,
  setMCPServerEnabled,
  updateMCPServer,
  type CreateMCPServerRequest,
  type MCPAuthMode,
  type MCPServer,
  type UpdateMCPServerRequest,
} from '@/api/mcp';
import { showErrorToast, showSuccessToast } from '@/utils/toast';

type HeaderForm = {
  name: string;
  value: string;
  existing: boolean;
};

const authModes: MCPAuthMode[] = ['none', 'bearer', 'headers'];

const servers = ref<MCPServer[]>([]);
const loading = ref(false);
const saving = ref(false);
const editorOpen = ref(false);
const editingServer = ref<MCPServer | null>(null);

const form = reactive({
  name: '',
  endpoint_url: '',
  auth_mode: 'none' as MCPAuthMode,
  bearer_token: '',
  headers: [] as HeaderForm[],
  enabled: true,
});

const isEditing = computed(() => Boolean(editingServer.value));

const loadServers = async () => {
  loading.value = true;
  try {
    servers.value = await listMCPServers();
  } catch (error: any) {
    showErrorToast(error?.message || 'Failed to load MCP servers');
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  form.name = '';
  form.endpoint_url = '';
  form.auth_mode = 'none';
  form.bearer_token = '';
  form.headers = [];
  form.enabled = true;
};

const openEditor = (server: MCPServer | null) => {
  editingServer.value = server;
  resetForm();
  if (server) {
    form.name = server.name;
    form.endpoint_url = server.endpoint_url;
    form.auth_mode = server.auth_mode;
    form.enabled = server.enabled;
    form.headers = server.masked_headers.map((header) => ({
      name: header.name,
      value: '',
      existing: true,
    }));
    if (form.auth_mode === 'headers' && form.headers.length === 0) {
      addHeader();
    }
  }
  editorOpen.value = true;
};

const selectAuthMode = (mode: MCPAuthMode) => {
  form.auth_mode = mode;
  if (mode === 'headers' && form.headers.length === 0) {
    addHeader();
  }
};

const addHeader = () => {
  form.headers.push({ name: '', value: '', existing: false });
};

const removeHeader = (index: number) => {
  form.headers.splice(index, 1);
};

const authModeTitle = (mode: MCPAuthMode): string => {
  if (mode === 'bearer') return 'Bearer';
  if (mode === 'headers') return 'Headers';
  return 'None';
};

const authModeLabel = (server: MCPServer): string => {
  if (server.auth_mode === 'bearer') {
    return server.has_bearer_token ? 'Bearer token' : 'Bearer';
  }
  if (server.auth_mode === 'headers') {
    return `${server.masked_headers.length} headers`;
  }
  return 'No auth';
};

const statusClass = (status: MCPServer['verify_status']): string => {
  if (status === 'healthy') {
    return 'border-emerald-200 bg-emerald-50 text-emerald-600 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-400';
  }
  if (status === 'error') {
    return 'border-red-200 bg-red-50 text-red-600 dark:border-red-900 dark:bg-red-950/30 dark:text-red-400';
  }
  return 'border-amber-200 bg-amber-50 text-amber-600 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-400';
};

const buildCreatePayload = (): CreateMCPServerRequest => ({
  name: form.name,
  endpoint_url: form.endpoint_url,
  auth_mode: form.auth_mode,
  enabled: form.enabled,
  ...authPayload(),
});

const buildUpdatePayload = (): UpdateMCPServerRequest => ({
  name: form.name,
  endpoint_url: form.endpoint_url,
  auth_mode: form.auth_mode,
  enabled: form.enabled,
  ...authPayload(),
});

const authPayload = () => {
  if (form.auth_mode === 'bearer') {
    const token = form.bearer_token.trim();
    return token ? { bearer_token: token } : {};
  }
  if (form.auth_mode === 'headers') {
    if (keepsExistingHeaders()) {
      return {};
    }
    const headers = form.headers
      .filter((header) => header.name.trim() && header.value.trim())
      .map((header) => ({
        name: header.name.trim(),
        value: header.value.trim(),
      }));
    return headers.length > 0 ? { headers } : {};
  }
  return {};
};

const validateForm = (): boolean => {
  if (form.name.trim().length < 2 || !form.endpoint_url.trim()) {
    showErrorToast('Name and endpoint URL are required');
    return false;
  }
  if (!form.endpoint_url.trim().startsWith('https://')) {
    showErrorToast('Endpoint URL must start with https://');
    return false;
  }
  if (form.auth_mode === 'bearer' && !form.bearer_token.trim() && (!isEditing.value || !editingServer.value?.has_bearer_token)) {
    showErrorToast('Bearer token is required');
    return false;
  }
  if (form.auth_mode === 'headers') {
    if (keepsExistingHeaders()) {
      return true;
    }
    if (isEditing.value && editingServer.value?.auth_mode === 'headers') {
      const hasBlankExisting = form.headers.some((header) => header.existing && !header.value.trim());
      if (hasBlankExisting) {
        showErrorToast('Re-enter all header values when changing headers');
        return false;
      }
    }
    const validHeaders = form.headers.filter((header) => header.name.trim() && header.value.trim());
    if (validHeaders.length === 0) {
      showErrorToast('At least one header is required');
      return false;
    }
  }
  return true;
};

const keepsExistingHeaders = (): boolean => {
  return (
    isEditing.value
    && editingServer.value?.auth_mode === 'headers'
    && form.auth_mode === 'headers'
    && form.headers.length > 0
    && form.headers.every((header) => header.existing && !header.value.trim())
  );
};

const saveServer = async () => {
  if (!validateForm()) {
    return;
  }
  saving.value = true;
  try {
    if (editingServer.value) {
      await updateMCPServer(editingServer.value.id, buildUpdatePayload());
      showSuccessToast('MCP server updated');
    } else {
      await createMCPServer(buildCreatePayload());
      showSuccessToast('MCP server created');
    }
    editorOpen.value = false;
    await loadServers();
  } catch (error: any) {
    showErrorToast(error?.message || 'Failed to save MCP server');
  } finally {
    saving.value = false;
  }
};

const toggleServer = async (server: MCPServer) => {
  saving.value = true;
  try {
    const updated = await setMCPServerEnabled(server.id, !server.enabled);
    const index = servers.value.findIndex((item) => item.id === server.id);
    if (index >= 0) {
      servers.value[index] = updated;
    }
  } catch (error: any) {
    showErrorToast(error?.message || 'Failed to update MCP server');
  } finally {
    saving.value = false;
  }
};

const confirmDelete = async (server: MCPServer) => {
  if (!window.confirm(`Delete MCP server "${server.name}"?`)) {
    return;
  }
  saving.value = true;
  try {
    await deleteMCPServer(server.id);
    showSuccessToast('MCP server deleted');
    await loadServers();
  } catch (error: any) {
    showErrorToast(error?.message || 'Failed to delete MCP server');
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  loadServers();
});
</script>

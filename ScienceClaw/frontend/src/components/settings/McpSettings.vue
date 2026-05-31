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
      <div class="grid grid-cols-2 gap-2 md:grid-cols-5">
        <div
          v-for="metric in summaryMetrics"
          :key="metric.label"
          class="rounded-xl border border-gray-100 bg-white px-3 py-2 shadow-sm dark:border-gray-700/50 dark:bg-gray-800/50"
        >
          <p class="text-[10px] font-semibold uppercase text-gray-400 dark:text-gray-500">{{ metric.label }}</p>
          <p class="mt-1 text-lg font-bold text-gray-800 dark:text-gray-100">{{ metric.value }}</p>
        </div>
      </div>

      <div
        v-if="enabledToolCount > 50"
        class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs font-medium text-amber-700 dark:border-amber-900/70 dark:bg-amber-950/30 dark:text-amber-300"
      >
        {{ enabledToolCount }} enabled MCP tools may make tool selection less reliable. Keep only the tools you need enabled.
      </div>

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
          class="grid cursor-pointer grid-cols-[1fr_auto] gap-3 border-b border-gray-100 p-4 transition-colors last:border-b-0 dark:border-gray-700/50"
          :class="selectedServerId === server.id ? 'bg-blue-50/60 dark:bg-blue-950/20' : 'hover:bg-gray-50/70 dark:hover:bg-gray-800/70'"
          @click="selectServer(server)"
        >
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <span class="truncate text-sm font-semibold text-gray-800 dark:text-gray-100">{{ server.name }}</span>
              <span class="rounded-md bg-gray-100 px-2 py-0.5 font-mono text-[10px] text-gray-500 dark:bg-gray-700 dark:text-gray-300">
                {{ server.slug }}
              </span>
              <span class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase" :class="statusClass(server.verify_status)">
                <Circle class="size-2 fill-current" />
                {{ statusLabel(server.verify_status) }}
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
              class="inline-flex size-8 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-800 disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-100"
              title="Verify"
              :disabled="saving || verifyingServerId === server.id"
              @click.stop="verifyServer(server)"
            >
              <Loader2 v-if="verifyingServerId === server.id" class="size-4 animate-spin" />
              <ShieldCheck v-else class="size-4" />
            </button>
            <button
              type="button"
              class="inline-flex size-8 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-800 disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-100"
              title="Refresh tools"
              :disabled="saving || refreshingServerId === server.id"
              @click.stop="refreshTools(server)"
            >
              <Loader2 v-if="refreshingServerId === server.id" class="size-4 animate-spin" />
              <RefreshCw v-else class="size-4" />
            </button>
            <button
              type="button"
              class="inline-flex size-8 items-center justify-center rounded-lg border transition-colors"
              :class="server.enabled ? 'border-emerald-200 bg-emerald-50 text-emerald-600 hover:bg-emerald-100 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-400' : 'border-gray-200 bg-white text-gray-400 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-500'"
              :title="server.enabled ? 'Disable' : 'Enable'"
              :disabled="saving"
              @click.stop="toggleServer(server)"
            >
              <Power class="size-4" />
            </button>
            <button
              type="button"
              class="inline-flex size-8 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-800 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-100"
              title="Edit"
              :disabled="saving"
              @click.stop="openEditor(server)"
            >
              <Pencil class="size-4" />
            </button>
            <button
              type="button"
              class="inline-flex size-8 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-red-50 hover:text-red-600 dark:text-gray-400 dark:hover:bg-red-950/30 dark:hover:text-red-400"
              title="Delete"
              :disabled="saving"
              @click.stop="confirmDelete(server)"
            >
              <Trash2 class="size-4" />
            </button>
          </div>
        </div>
      </div>

      <McpToolList
        v-if="selectedServer"
        :tools="tools"
        :loading="toolsLoading"
        :refreshing="refreshingServerId === selectedServer.id"
        :disabled="saving"
        :toggling-tool-id="togglingToolId"
        @refresh="refreshTools(selectedServer)"
        @toggle="toggleTool"
      />
    </div>

    <McpServerDrawer
      :open="editorOpen"
      :editing="isEditing"
      :saving="saving"
      :has-bearer-token="Boolean(editingServer?.has_bearer_token)"
      :form="form"
      @close="editorOpen = false"
      @save="saveServer"
      @select-auth-mode="selectAuthMode"
      @add-header="addHeader"
      @remove-header="removeHeader"
      @update-header="updateHeader"
      @update-field="updateFormField"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { Circle, Loader2, Pencil, Plus, Power, RefreshCw, Server, ShieldCheck, Trash2 } from 'lucide-vue-next';
import {
  createMCPServer,
  deleteMCPServer,
  listMCPTools,
  listMCPServerTools,
  listMCPServers,
  refreshMCPServerTools,
  setMCPServerEnabled,
  setMCPToolEnabled,
  updateMCPServer,
  verifyMCPServer,
  type CreateMCPServerRequest,
  type MCPAuthMode,
  type MCPServer,
  type MCPTool,
  type UpdateMCPServerRequest,
} from '@/api/mcp';
import { showErrorToast, showSuccessToast } from '@/utils/toast';
import McpServerDrawer, { type MCPServerForm } from './McpServerDrawer.vue';
import McpToolList from './McpToolList.vue';

const servers = ref<MCPServer[]>([]);
const tools = ref<MCPTool[]>([]);
const enabledToolCount = ref(0);
const loading = ref(false);
const toolsLoading = ref(false);
const saving = ref(false);
const verifyingServerId = ref<string | null>(null);
const refreshingServerId = ref<string | null>(null);
const togglingToolId = ref<string | null>(null);
const editorOpen = ref(false);
const editingServer = ref<MCPServer | null>(null);
const selectedServerId = ref<string | null>(null);

const form = reactive<MCPServerForm>({
  name: '',
  endpoint_url: '',
  auth_mode: 'none' as MCPAuthMode,
  bearer_token: '',
  headers: [],
  enabled: true,
  verify_now: false,
  refresh_after_save: false,
});

const isEditing = computed(() => Boolean(editingServer.value));

const selectedServer = computed(() => {
  return servers.value.find((server) => server.id === selectedServerId.value) ?? null;
});

const summaryMetrics = computed(() => {
  return [
    { label: 'Servers', value: servers.value.length },
    { label: 'Enabled', value: servers.value.filter((server) => server.enabled).length },
    { label: 'Healthy', value: servers.value.filter((server) => server.verify_status === 'healthy').length },
    { label: 'Tools', value: enabledToolCount.value },
    { label: 'Errors', value: servers.value.filter((server) => server.verify_status === 'error').length },
  ];
});

const errorMessage = (error: unknown, fallback: string): string => {
  const maybeError = error as {
    message?: string;
    response?: { data?: { detail?: unknown } };
  };
  const detail = maybeError?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      if (item && typeof item === 'object' && 'msg' in item) {
        return String(item.msg);
      }
      return String(item);
    }).join('; ');
  }
  if (typeof detail === 'string') {
    return detail;
  }
  return maybeError?.message || fallback;
};

const loadServers = async () => {
  loading.value = true;
  try {
    servers.value = await listMCPServers();
    enabledToolCount.value = (await listMCPTools()).length;
    if (!selectedServerId.value && servers.value.length > 0) {
      selectedServerId.value = servers.value[0].id;
    }
    if (selectedServerId.value && !servers.value.some((server) => server.id === selectedServerId.value)) {
      selectedServerId.value = servers.value[0]?.id ?? null;
    }
    if (selectedServerId.value) {
      await loadTools(selectedServerId.value);
    } else {
      tools.value = [];
    }
  } catch (error: unknown) {
    showErrorToast(errorMessage(error, 'Failed to load MCP servers'));
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
  form.verify_now = false;
  form.refresh_after_save = false;
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

const updateHeader = (index: number, field: 'name' | 'value', value: string) => {
  const header = form.headers[index];
  if (!header) {
    return;
  }
  header[field] = value;
};

const updateFormField = (field: keyof MCPServerForm, value: string | boolean) => {
  if (field === 'headers') {
    return;
  }
  if (typeof form[field] === 'boolean') {
    (form[field] as boolean) = Boolean(value);
    return;
  }
  (form[field] as string | MCPAuthMode) = String(value) as MCPAuthMode;
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

const statusLabel = (status: MCPServer['verify_status']): string => {
  if (status === 'healthy') return 'Healthy';
  if (status === 'error') return 'Error';
  return 'Unknown';
};

const selectServer = async (server: MCPServer) => {
  if (selectedServerId.value === server.id) {
    return;
  }
  selectedServerId.value = server.id;
  await loadTools(server.id);
};

const replaceServer = (updated: MCPServer) => {
  const index = servers.value.findIndex((item) => item.id === updated.id);
  if (index >= 0) {
    servers.value[index] = updated;
  }
};

const loadTools = async (serverId: string) => {
  toolsLoading.value = true;
  try {
    tools.value = await listMCPServerTools(serverId);
  } catch (error: unknown) {
    tools.value = [];
    showErrorToast(errorMessage(error, 'Failed to load MCP tools'));
  } finally {
    toolsLoading.value = false;
  }
};

const buildCreatePayload = (): CreateMCPServerRequest => ({
  name: form.name.trim(),
  endpoint_url: form.endpoint_url.trim(),
  auth_mode: form.auth_mode,
  enabled: form.enabled,
  verify_now: form.verify_now,
  ...authPayload(),
});

const buildUpdatePayload = (): UpdateMCPServerRequest => ({
  name: form.name.trim(),
  endpoint_url: form.endpoint_url.trim(),
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
    let saved: MCPServer;
    if (editingServer.value) {
      saved = await updateMCPServer(editingServer.value.id, buildUpdatePayload());
      showSuccessToast('MCP server updated');
    } else {
      saved = await createMCPServer(buildCreatePayload());
      showSuccessToast('MCP server created');
    }
    editorOpen.value = false;
    selectedServerId.value = saved.id;
    if (form.verify_now && editingServer.value) {
      await verifyServer(saved, false);
    }
    if (form.refresh_after_save) {
      await refreshTools(saved, false);
    }
    await loadServers();
  } catch (error: unknown) {
    showErrorToast(errorMessage(error, 'Failed to save MCP server'));
  } finally {
    saving.value = false;
  }
};

const toggleServer = async (server: MCPServer) => {
  saving.value = true;
  try {
    const updated = await setMCPServerEnabled(server.id, !server.enabled);
    replaceServer(updated);
  } catch (error: unknown) {
    showErrorToast(errorMessage(error, 'Failed to update MCP server'));
  } finally {
    saving.value = false;
  }
};

const verifyServer = async (server: MCPServer, toast = true) => {
  verifyingServerId.value = server.id;
  try {
    const result = await verifyMCPServer(server.id);
    replaceServer(result);
    if (toast) {
      showSuccessToast(result.verify_status === 'healthy' ? 'MCP server verified' : 'MCP verification finished');
    }
  } catch (error: unknown) {
    showErrorToast(errorMessage(error, 'Failed to verify MCP server'));
  } finally {
    verifyingServerId.value = null;
  }
};

const refreshTools = async (server: MCPServer, toast = true) => {
  refreshingServerId.value = server.id;
  try {
    const result = await refreshMCPServerTools(server.id);
    replaceServer(result);
    selectedServerId.value = server.id;
    await loadTools(server.id);
    if (toast) {
      showSuccessToast(`MCP tools refreshed: ${result.inserted} added, ${result.updated} updated, ${result.removed} removed`);
    }
  } catch (error: unknown) {
    showErrorToast(errorMessage(error, 'Failed to refresh MCP tools'));
  } finally {
    refreshingServerId.value = null;
  }
};

const toggleTool = async (tool: MCPTool) => {
  const previous = tool.enabled;
  togglingToolId.value = tool.id;
  tool.enabled = !tool.enabled;
  try {
    const updated = await setMCPToolEnabled(tool.id, tool.enabled);
    const index = tools.value.findIndex((item) => item.id === tool.id);
    if (index >= 0) {
      tools.value[index] = updated;
    }
  } catch (error: unknown) {
    tool.enabled = previous;
    showErrorToast(errorMessage(error, 'Failed to update MCP tool'));
  } finally {
    togglingToolId.value = null;
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
  } catch (error: unknown) {
    showErrorToast(errorMessage(error, 'Failed to delete MCP server'));
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  loadServers();
});
</script>

<template>
  <div class="flex flex-col sandbox-preview"
    :style="expanded ? { flex: '1.5 1 0%', minHeight: '120px' } : { flex: '0 0 auto' }">

    <!-- Header (unified with ActivityPanel section headers) -->
    <div
      @click="expanded = !expanded"
      class="flex-shrink-0 flex items-center gap-2 cursor-pointer select-none group/sec px-4 py-2.5 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors"
    >
      <ChevronRightIcon :size="12"
        class="text-gray-400 dark:text-gray-500 transition-transform duration-150 flex-shrink-0"
        :class="{ 'rotate-90': expanded }" />
      <MonitorIcon :size="13" class="text-teal-400 flex-shrink-0" />
      <span class="text-[12px] font-semibold transition-colors"
        :class="expanded ? 'text-gray-600 dark:text-gray-300' : 'text-gray-400 dark:text-gray-500 group-hover/sec:text-gray-600 dark:group-hover/sec:text-gray-300'">
        {{ t('Sandbox') }}
      </span>

      <!-- Inline tab pills -->
      <div class="flex items-center gap-0.5 ml-1" @click.stop>
        <button
          v-for="tab in availableTabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="px-1.5 py-0.5 text-[10px] font-medium rounded transition-colors"
          :class="activeTab === tab.id
            ? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'
            : 'text-gray-400 dark:text-gray-500 hover:text-gray-500 dark:hover:text-gray-400'"
        >
          {{ tab.label }}
        </button>
      </div>

      <button
        v-if="sessionId"
        type="button"
        @click.stop="takeOver"
        class="ml-2 inline-flex items-center justify-center rounded-md border border-gray-200 bg-white px-2 py-0.5 text-[10px] font-medium text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-200"
      >
        {{ t('Take Over') }}
      </button>

      <div class="flex items-center gap-2 ml-auto">
        <SandboxTakeoverStatusBadge v-if="isTakenOver" />

        <!-- Live indicator -->
        <div v-if="isLive" class="flex items-center gap-1">
          <span class="relative flex h-1.5 w-1.5">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
          </span>
          <span class="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold tabular-nums">LIVE</span>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div v-if="expanded" class="flex-1 min-h-0 overflow-hidden bg-[#1e1e1e] section-content-enter">
      <!-- Terminal view -->
      <SandboxTerminal
        v-if="activeTab === 'terminal'"
        ref="terminalRef"
        :active="expanded && activeTab === 'terminal'"
        :history="props.history"
      />

      <!-- Browser VNC view -->
      <iframe
        v-else-if="activeTab === 'browser'"
        :src="vncUrl"
        class="w-full h-full border-0"
        sandbox="allow-same-origin allow-scripts allow-popups"
        referrerpolicy="no-referrer"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { ChevronRight as ChevronRightIcon, Monitor as MonitorIcon } from 'lucide-vue-next';
import { useI18n } from 'vue-i18n';
import SandboxTerminal from './SandboxTerminal.vue';
import SandboxTakeoverStatusBadge from './SandboxTakeoverStatusBadge.vue';
import { getSandboxVncUrl, type SandboxPreviewMode } from '@/utils/sandbox';
import {
  SANDBOX_TAKEOVER_EVENT,
  readSandboxTakeoverState,
  writeSandboxTakeoverState,
  getActiveTakeoverSession,
  setActiveTakeoverSession,
  type SandboxTakeoverState,
} from '@/utils/sandboxTakeoverState';
import { showInfoToast } from '@/utils/toast';

const { t } = useI18n();

export interface SandboxExecEntry {
  toolName: string;
  command: string;
  output?: string;
  status: string;
}

const props = defineProps<{
  mode: SandboxPreviewMode;
  isLive: boolean;
  sessionId?: string;
  history?: SandboxExecEntry[];
}>();

const expanded = ref(true);
const activeTab = ref<'terminal' | 'browser'>('browser');
const terminalRef = ref<InstanceType<typeof SandboxTerminal> | null>(null);
const isTakenOver = ref(false);

const vncUrl = computed(() => getSandboxVncUrl());

const availableTabs = computed(() => {
  const tabs: { id: 'terminal' | 'browser'; label: string }[] = [];
  tabs.push({ id: 'terminal', label: t('Terminal') });
  tabs.push({ id: 'browser', label: t('Browser') });
  return tabs;
});

// Auto-switch tab based on the incoming tool mode
watch(() => props.mode, (mode) => {
  if (mode === 'terminal') {
    activeTab.value = 'terminal';
    expanded.value = true;
  } else if (mode === 'browser') {
    activeTab.value = 'browser';
    expanded.value = true;
  }
}, { immediate: true });

const syncTakeoverState = () => {
  isTakenOver.value = props.sessionId ? readSandboxTakeoverState(props.sessionId) : false;
};

const takeOver = () => {
  if (!props.sessionId) {
    return;
  }
  const activeSession = getActiveTakeoverSession();
  if (activeSession && activeSession !== props.sessionId) {
    showInfoToast(t('A sandbox takeover is already active in another session. Please close it first.'));
    return;
  }
  writeSandboxTakeoverState(props.sessionId, true);
  setActiveTakeoverSession(props.sessionId);
  window.open(`/chat/${props.sessionId}?sandbox=1`, '_blank', 'noopener');
};

const handleTakeoverStateEvent = (event: Event) => {
  const customEvent = event as CustomEvent<SandboxTakeoverState>;
  if (!props.sessionId || customEvent.detail?.sessionId !== props.sessionId) {
    return;
  }
  isTakenOver.value = !!customEvent.detail?.active;
};

const handleStorageEvent = (event: StorageEvent) => {
  if (!props.sessionId) {
    return;
  }
  if (event.key && event.key !== `scienceclaw:sandbox-takeover:${props.sessionId}`) {
    return;
  }
  syncTakeoverState();
};

const writeExecution = (toolName: string, command: string, output?: string, status?: string) => {
  terminalRef.value?.writeExecution(toolName, command, output, status);
};

watch(() => props.sessionId, syncTakeoverState, { immediate: true });

onMounted(() => {
  window.addEventListener(SANDBOX_TAKEOVER_EVENT, handleTakeoverStateEvent as EventListener);
  window.addEventListener('storage', handleStorageEvent);
});

onBeforeUnmount(() => {
  window.removeEventListener(SANDBOX_TAKEOVER_EVENT, handleTakeoverStateEvent as EventListener);
  window.removeEventListener('storage', handleStorageEvent);
});

defineExpose({ writeExecution });
</script>

<style scoped>
.sandbox-preview {
  transition: flex 0.2s ease-out;
}

.section-content-enter {
  animation: section-reveal 0.2s ease-out;
}
@keyframes section-reveal {
  from { opacity: 0; transform: translateY(-6px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

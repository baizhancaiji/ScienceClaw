<template>
  <div
    v-if="shouldShow"
    class="fixed inset-0 z-50 flex h-full w-full flex-col bg-[var(--background-gray-main)]"
  >
    <div class="border-b border-[var(--border-main)] bg-[var(--background-white)]/90 px-4 py-3 backdrop-blur">
      <div class="flex flex-wrap items-center gap-3">
        <div class="min-w-0">
          <div class="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--text-tertiary)]">
            {{ t('Sandbox') }}
          </div>
          <div class="truncate text-sm font-medium text-[var(--text-primary)]">
            {{ boundSessionId }}
          </div>
        </div>

        <div class="ml-auto flex items-center gap-2" data-testid="takeover-tabs">
          <button
            v-for="tab in availableTabs"
            :key="tab.id"
            type="button"
            :data-testid="`takeover-tab-${tab.id}`"
            class="inline-flex items-center justify-center rounded-full border px-3 py-1.5 text-sm font-medium transition-colors"
            :class="activeTab === tab.id
              ? 'border-[var(--border-dark)] bg-[var(--Button-primary-black)] text-[var(--text-onblack)]'
              : 'border-[var(--border-main)] bg-[var(--background-white)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>

        <button
          type="button"
          class="inline-flex items-center justify-center whitespace-nowrap rounded-full border-2 border-[var(--border-dark)] bg-[var(--Button-primary-black)] px-3 py-1.5 text-sm font-medium text-[var(--text-onblack)] transition-colors hover:opacity-90 active:opacity-80"
          @click="exitTakeOver"
        >
          {{ t('Exit Takeover') }}
        </button>
      </div>
    </div>

    <div class="flex min-h-0 flex-1 flex-col">
      <div
        v-if="activeTab === 'browser'"
        class="flex items-center justify-between gap-3 border-b border-[var(--border-main)] bg-[var(--background-white)] px-4 py-2"
      >
        <div class="text-sm text-[var(--text-secondary)]">
          {{ t('Browser View Only') }}
        </div>
        <button
          type="button"
          data-testid="takeover-browser-control-toggle"
          class="inline-flex items-center justify-center rounded-full border px-3 py-1.5 text-sm font-medium transition-colors"
          :class="browserViewOnly
            ? 'border-[var(--border-main)] bg-[var(--background-white)] text-[var(--text-secondary)]'
            : 'border-[var(--border-dark)] bg-[var(--Button-primary-black)] text-[var(--text-onblack)]'"
          :aria-pressed="!browserViewOnly"
          @click="browserViewOnly = !browserViewOnly"
        >
          {{ browserViewOnly ? t('Enable Browser Control') : t('Disable Browser Control') }}
        </button>
      </div>

      <div class="min-h-0 flex-1">
        <SandboxTerminal
          v-if="activeTab === 'terminal'"
          :active="shouldShow && activeTab === 'terminal'"
          :history="terminalHistory"
        />

        <VNCViewer
          v-else
          :session-id="boundSessionId"
          :enabled="shouldShow && activeTab === 'browser'"
          :view-only="browserViewOnly"
          @connected="onVNCConnected"
          @disconnected="onVNCDisconnected"
          @credentials-required="onVNCCredentialsRequired"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';

import SandboxTerminal from './SandboxTerminal.vue';
import VNCViewer from './VNCViewer.vue';
import {
  getSandboxHistoryChannelName,
  readSandboxHistory,
  type SandboxExecEntry,
  type SandboxHistoryChannelMessage,
} from '../utils/sandboxHistoryChannel';
import { writeSandboxTakeoverState, clearActiveTakeoverSession, setActiveTakeoverSession } from '../utils/sandboxTakeoverState';

interface TakeOverDetail {
  active?: boolean;
  sessionId?: string;
}

const route = useRoute();
const { t } = useI18n();

const takeOverActive = ref(false);
const boundSessionId = ref('');
const activeTab = ref<'terminal' | 'browser'>('browser');
const browserViewOnly = ref(true);
const terminalHistory = ref<SandboxExecEntry[]>([]);
const routeTakeOverDismissed = ref(false);
let sandboxHistoryChannel: BroadcastChannel | null = null;
let snapshotRetryTimer: ReturnType<typeof setTimeout> | null = null;
let snapshotRequestAttempts = 0;
let hasReceivedSnapshot = false;

const SNAPSHOT_REQUEST_RETRY_MS = 250;
const SNAPSHOT_REQUEST_MAX_ATTEMPTS = 8;

const availableTabs = computed(() => ([
  { id: 'terminal' as const, label: t('Terminal') },
  { id: 'browser' as const, label: t('Browser') },
]));

const isEnabledQueryFlag = (value: unknown): boolean => {
  if (Array.isArray(value)) {
    return value.includes('1');
  }
  return value === '1';
};

const getRouteSessionId = (): string => {
  const sessionParam = route.params.sessionId;
  if (Array.isArray(sessionParam)) {
    return sessionParam[0] ?? '';
  }
  return typeof sessionParam === 'string' ? sessionParam : '';
};

const isRouteTakeOverMode = computed(() => {
  const sessionId = getRouteSessionId();
  if (!sessionId) {
    return false;
  }

  return isEnabledQueryFlag(route.query.sandbox) || isEnabledQueryFlag(route.query.vnc);
});

const bindSession = (sessionId: string) => {
  if (!sessionId) {
    return;
  }

  if (boundSessionId.value && boundSessionId.value !== sessionId) {
    writeSandboxTakeoverState(boundSessionId.value, false);
    clearActiveTakeoverSession(boundSessionId.value);
  }
  boundSessionId.value = sessionId;
  activeTab.value = 'browser';
  browserViewOnly.value = true;
  // Read initial history from localStorage (written by the source tab's ActivityPanel).
  // This is more reliable than BroadcastChannel snapshot requests which depend on
  // the source tab being alive and responsive.
  terminalHistory.value = readSandboxHistory(sessionId);
  routeTakeOverDismissed.value = false;
  writeSandboxTakeoverState(sessionId, true);
  setActiveTakeoverSession(sessionId);
};

const clearSnapshotRetry = () => {
  if (snapshotRetryTimer !== null) {
    clearTimeout(snapshotRetryTimer);
    snapshotRetryTimer = null;
  }
};

const resetSnapshotSyncState = () => {
  clearSnapshotRetry();
  snapshotRequestAttempts = 0;
  hasReceivedSnapshot = false;
};

const clearTakeOverState = () => {
  if (boundSessionId.value) {
    writeSandboxTakeoverState(boundSessionId.value, false);
    clearActiveTakeoverSession(boundSessionId.value);
  }
  takeOverActive.value = false;
  boundSessionId.value = '';
  activeTab.value = 'browser';
  browserViewOnly.value = true;
  terminalHistory.value = [];
  resetSnapshotSyncState();
};

const closeSandboxHistoryChannel = () => {
  clearSnapshotRetry();
  sandboxHistoryChannel?.close();
  sandboxHistoryChannel = null;
};

const requestSandboxHistorySnapshot = (sessionId: string, resetAttempts = false) => {
  if (!sandboxHistoryChannel || !sessionId || hasReceivedSnapshot) {
    return;
  }

  if (resetAttempts) {
    resetSnapshotSyncState();
  }

  sandboxHistoryChannel.postMessage({
    type: 'request-snapshot',
    sessionId,
  } satisfies SandboxHistoryChannelMessage);

  snapshotRequestAttempts += 1;
  if (snapshotRequestAttempts >= SNAPSHOT_REQUEST_MAX_ATTEMPTS) {
    return;
  }

  clearSnapshotRetry();
  snapshotRetryTimer = setTimeout(() => {
    snapshotRetryTimer = null;
    if (
      hasReceivedSnapshot
      || boundSessionId.value !== sessionId
      || !(takeOverActive.value || isRouteTakeOverMode.value)
    ) {
      return;
    }
    requestSandboxHistorySnapshot(sessionId);
  }, SNAPSHOT_REQUEST_RETRY_MS);
};

const rebuildSandboxHistoryChannel = (sessionId: string) => {
  closeSandboxHistoryChannel();

  if (!sessionId) {
    return;
  }

  resetSnapshotSyncState();
  sandboxHistoryChannel = new BroadcastChannel(getSandboxHistoryChannelName(sessionId));
  sandboxHistoryChannel.addEventListener('message', (event: MessageEvent<SandboxHistoryChannelMessage>) => {
    const message = event.data;
    if (!message || message.sessionId !== sessionId) {
      return;
    }

    if (message.type === 'snapshot') {
      hasReceivedSnapshot = true;
      clearSnapshotRetry();
      // Only overwrite if the BroadcastChannel snapshot has more entries than
      // what we already loaded from localStorage (e.g. real-time updates arrived
      // after the localStorage snapshot was written).
      if (message.entries.length > terminalHistory.value.length) {
        terminalHistory.value = [...message.entries];
      }
      return;
    }

    if (message.type === 'incremental') {
      terminalHistory.value = [...terminalHistory.value, message.entry];
    }
  });

  requestSandboxHistorySnapshot(sessionId, true);
};

const handleTakeOverEvent = (event: Event) => {
  const customEvent = event as CustomEvent<TakeOverDetail>;
  const detail = customEvent.detail ?? {};

  if (detail.active && detail.sessionId) {
    takeOverActive.value = true;
    bindSession(detail.sessionId);
    return;
  }

  clearTakeOverState();
};

const onVNCConnected = () => {
  console.log('TakeOver VNC connection successful');
};

const onVNCDisconnected = (reason?: unknown) => {
  console.log('TakeOver VNC connection disconnected', reason);
};

const onVNCCredentialsRequired = () => {
  console.log('TakeOver VNC credentials required');
};

watch(
  () => [route.params.sessionId, route.query.sandbox, route.query.vnc],
  () => {
    if (takeOverActive.value) {
      return;
    }

    if (!isRouteTakeOverMode.value) {
      routeTakeOverDismissed.value = false;
      if (boundSessionId.value) {
        clearTakeOverState();
        closeSandboxHistoryChannel();
      }
      return;
    }

    const routeSessionId = getRouteSessionId();
    if (!routeSessionId) {
      return;
    }

    if (boundSessionId.value !== routeSessionId || routeTakeOverDismissed.value) {
      bindSession(routeSessionId);
    }
  },
  { immediate: true },
);

watch(activeTab, (tab) => {
  if (
    tab === 'terminal'
    && boundSessionId.value
    && sandboxHistoryChannel
    && !hasReceivedSnapshot
  ) {
    requestSandboxHistorySnapshot(boundSessionId.value, true);
  }
});

watch(boundSessionId, (sessionId) => {
  if (!(takeOverActive.value || isRouteTakeOverMode.value)) {
    closeSandboxHistoryChannel();
    return;
  }

  rebuildSandboxHistoryChannel(sessionId);
}, { immediate: true });

const shouldShow = computed(() => {
  if (takeOverActive.value && boundSessionId.value) {
    return true;
  }

  if (routeTakeOverDismissed.value) {
    return false;
  }

  return isRouteTakeOverMode.value && !!boundSessionId.value;
});

const exitTakeOver = () => {
  routeTakeOverDismissed.value = true;
  clearTakeOverState();
};

onMounted(() => {
  window.addEventListener('takeover', handleTakeOverEvent as EventListener);
});

onBeforeUnmount(() => {
  if (boundSessionId.value) {
    writeSandboxTakeoverState(boundSessionId.value, false);
    clearActiveTakeoverSession(boundSessionId.value);
  }
  window.removeEventListener('takeover', handleTakeOverEvent as EventListener);
  closeSandboxHistoryChannel();
});

defineExpose({
  sessionId: computed(() => boundSessionId.value),
});
</script>

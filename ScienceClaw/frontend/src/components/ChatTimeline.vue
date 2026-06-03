<template>
  <div
    class="chat-timeline"
    :class="{ 'chat-timeline--visible': entries.length > 1 }"
    @mouseleave="hoveredEntry = null"
  >
    <div class="chat-timeline__inner">
      <!-- Vertical line -->
      <div class="chat-timeline__line"></div>

      <!-- Anchors -->
      <button
        v-for="(entry, i) in entries"
        :key="entry.messageKey"
        class="chat-timeline__anchor"
        :class="{ 'chat-timeline__anchor--active': activeIndex === i }"
        @click="$emit('navigate', entry.messageKey)"
        @mouseenter="onAnchorHover(entry, $event)"
      >
        <div class="chat-timeline__dot"></div>
      </button>
    </div>

    <!-- Floating tooltip (teleported to body to escape overflow clipping) -->
    <Teleport to="body">
      <div
        v-if="hoveredEntry && tooltipStyle"
        class="chat-timeline__tooltip"
        :style="tooltipStyle"
      >
        <span class="chat-timeline__tooltip-time">{{ hoveredEntry.time }}</span>
        <span class="chat-timeline__tooltip-preview">{{ hoveredEntry.preview }}</span>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { GroupedMessage } from '../composables/useMessageGrouper';

export interface TimelineEntry {
  messageKey: string;
  time: string;
  preview: string;
  title: string;
}

const props = defineProps<{
  groups: GroupedMessage[];
  /** Index of which user message is currently visually active/nearest */
  activeIndex: number;
  /** Function to get message key from a group */
  getMessageKey: (group: GroupedMessage) => string;
}>();

defineEmits<{
  navigate: [messageKey: string];
}>();

const entries = computed<TimelineEntry[]>(() => {
  const result: TimelineEntry[] = [];
  for (const group of props.groups) {
    if (group.type === 'single' && group.message?.type === 'user') {
      const msg = group.message;
      const content = (msg.content as any)?.content || '';
      const ts = (msg.content as any)?.timestamp;
      const preview = content.slice(0, 50).replace(/\n/g, ' ').trim();
      const time = ts ? formatTime(ts) : '';
      result.push({
        messageKey: props.getMessageKey(group),
        time,
        preview: preview || '(empty)',
        title: `${time}\n${content.slice(0, 200)}`,
      });
    }
  }
  return result;
});

function formatTime(ts: number): string {
  const d = new Date(ts * 1000);
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ── Tooltip state ──
const hoveredEntry = ref<TimelineEntry | null>(null);
const tooltipStyle = ref<Record<string, string> | null>(null);

const onAnchorHover = (entry: TimelineEntry, event: MouseEvent) => {
  hoveredEntry.value = entry;
  tooltipStyle.value = {
    position: 'fixed',
    left: `${event.clientX - 12}px`,
    top: `${event.clientY - 8}px`,
    transform: 'translate(-100%, -50%)',
  };
};
</script>

<style scoped>
.chat-timeline {
  position: sticky;
  top: 0;
  right: 0;
  z-index: 15;
  flex-shrink: 0;
  width: 28px;
  margin-right: 4px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.25s ease;
  align-self: stretch;
  display: flex;
  flex-direction: column;
}

.chat-timeline--visible {
  pointer-events: auto;
  opacity: 1;
}

.chat-timeline__inner {
  position: sticky;
  top: 0;
  height: 100vh;
  max-height: 100vh;
  overflow-y: auto;
  scrollbar-width: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 0;
}
.chat-timeline__inner::-webkit-scrollbar {
  display: none;
}

/* Vertical line */
.chat-timeline__line {
  position: absolute;
  top: 20px;
  bottom: 20px;
  left: 13px;
  width: 2px;
  background: var(--border-main, #e5e7eb);
  border-radius: 1px;
}

/* Anchor buttons */
.chat-timeline__anchor {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 12px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
}

/* Dot */
.chat-timeline__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--text-disable, #d1d5db);
  transition: background 0.2s, transform 0.2s, box-shadow 0.2s;
  z-index: 1;
}
.chat-timeline__anchor:hover .chat-timeline__dot {
  background: var(--text-tertiary, #9ca3af);
  transform: scale(1.3);
}
.chat-timeline__anchor--active .chat-timeline__dot {
  background: var(--accent-blue, #3b82f6);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent-blue, #3b82f6) 20%, transparent);
  transform: scale(1.2);
}

/* Floating tooltip (teleported to body, preserves component scope) */
.chat-timeline__tooltip {
  position: fixed;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 5px 10px;
  border-radius: 6px;
  background: var(--background-white-main, #fff);
  border: 1px solid var(--border-main, #e5e7eb);
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  pointer-events: none;
  line-height: 1.3;
  white-space: nowrap;
}
.chat-timeline__tooltip-time {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-tertiary, #9ca3af);
  letter-spacing: 0.02em;
}
.chat-timeline__tooltip-preview {
  font-size: 11px;
  color: var(--text-tertiary, #9ca3af);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>

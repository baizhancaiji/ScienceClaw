import { ref } from 'vue'
import type { ListSessionItem } from '../types/response'

const onSessionTitleUpdate = ref<((sessionId: string, title: string) => void) | null>(null)
const onSessionPatch = ref<((sessionId: string, patch: Partial<ListSessionItem>) => void) | null>(null)

/**
 * Shared composable for updating session title in the left-panel session list
 * when the backend sends a title event (e.g. after first user message).
 */
export function useSessionListUpdate() {
  return {
    setOnSessionTitleUpdate: (fn: ((sessionId: string, title: string) => void) | null) => {
      onSessionTitleUpdate.value = fn
    },
    setOnSessionPatch: (fn: ((sessionId: string, patch: Partial<ListSessionItem>) => void) | null) => {
      onSessionPatch.value = fn
    },
    updateSessionTitle: (sessionId: string, title: string) => {
      onSessionTitleUpdate.value?.(sessionId, title)
    },
    patchSessionItem: (sessionId: string, patch: Partial<ListSessionItem>) => {
      onSessionPatch.value?.(sessionId, patch)
    },
  }
}

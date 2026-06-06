<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 dark:bg-black/50" @click.self="handleCancel">
      <div class="w-[420px] max-w-[92vw] rounded-xl border border-gray-100 bg-white p-5 shadow-xl dark:border-gray-700 dark:bg-gray-800">
        <div class="mb-4 flex items-start justify-between gap-4">
          <div>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ t('Verify session password') }}</h3>
            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ t('Session password required') }}</p>
          </div>
          <button class="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700" @click="handleCancel">
            <X :size="16" />
          </button>
        </div>

        <div class="space-y-3">
          <div v-if="hint" class="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-900/20 dark:text-amber-300">
            <span class="font-medium">{{ t('Password hint') }}:</span> {{ hint }}
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ t('Session password') }}</label>
            <input
              v-model="password"
              type="password"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              :placeholder="t('Enter session password')"
              @keyup.enter="handleVerify"
            />
          </div>

          <button class="text-xs text-blue-500 hover:text-blue-600" @click="showReset = true">
            {{ t('Forgot session password?') }}
          </button>

          <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
        </div>

        <div class="mt-5 flex justify-end gap-2">
          <button class="rounded-lg px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700" @click="handleCancel">
            {{ t('Cancel') }}
          </button>
          <button
            class="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!password || loading"
            @click="handleVerify"
          >
            {{ loading ? t('Verifying...') : t('Confirm') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <ResetSessionPasswordDialog
    :open="showReset"
    :session-id="sessionId"
    @update:open="showReset = $event"
    @success="handleResetSuccess"
  />
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { X } from 'lucide-vue-next';
import { getSessionPasswordHint, verifySessionPassword } from '../../api/agent';
import ResetSessionPasswordDialog from './ResetSessionPasswordDialog.vue';

const props = defineProps<{
  open: boolean;
  sessionId: string;
}>();

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void;
  (e: 'success', hasPassword?: boolean): void;
  (e: 'cancel'): void;
}>();

const { t } = useI18n();
const password = ref('');
const hint = ref('');
const error = ref('');
const loading = ref(false);
const showReset = ref(false);

watch(() => props.open, async (open) => {
  if (!open) return;
  password.value = '';
  error.value = '';
  loading.value = false;
  try {
    const result = await getSessionPasswordHint(props.sessionId);
    hint.value = result.hint || '';
  } catch {
    hint.value = '';
  }
});

const handleCancel = () => {
  if (loading.value) return;
  emit('update:open', false);
  emit('cancel');
};

const handleVerify = async () => {
  if (!password.value || loading.value) return;
  loading.value = true;
  error.value = '';
  try {
    const result = await verifySessionPassword(props.sessionId, { password: password.value });
    if (!result.valid) {
      error.value = t('Incorrect session password');
      return;
    }
    emit('update:open', false);
    emit('success', true);
  } catch (err: any) {
    error.value = err?.message || t('Failed to verify session password');
  } finally {
    loading.value = false;
  }
};

const handleResetSuccess = (hasPassword: boolean) => {
  showReset.value = false;
  emit('update:open', false);
  emit('success', hasPassword);
};
</script>

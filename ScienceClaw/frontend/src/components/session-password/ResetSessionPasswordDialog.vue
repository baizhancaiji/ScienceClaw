<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/30 dark:bg-black/50" @click.self="handleCancel">
      <div class="w-[420px] max-w-[92vw] rounded-xl border border-gray-100 bg-white p-5 shadow-xl dark:border-gray-700 dark:bg-gray-800">
        <div class="mb-4 flex items-start justify-between gap-4">
          <div>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ t('Reset session password') }}</h3>
            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ t('Use account password to reset session password.') }}</p>
          </div>
          <button class="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700" @click="handleCancel">
            <X :size="16" />
          </button>
        </div>

        <div class="space-y-3">
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ t('Account password') }}</label>
            <input
              v-model="accountPassword"
              type="password"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              :placeholder="t('Enter account password')"
            />
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ t('New session password') }}</label>
            <input
              v-model="newPassword"
              type="password"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              :placeholder="t('Leave empty to remove protection')"
            />
            <p v-if="newPassword" class="text-[11px] text-gray-400">{{ t('Session password rule') }}</p>
          </div>

          <div v-if="newPassword" class="space-y-1.5">
            <label class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ t('Confirm session password') }}</label>
            <input
              v-model="confirmPassword"
              type="password"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              :placeholder="t('Enter session password again')"
            />
            <p v-if="confirmPassword && newPassword !== confirmPassword" class="text-[11px] text-red-500">
              {{ t('Session passwords do not match') }}
            </p>
          </div>

          <div v-if="newPassword" class="space-y-1.5">
            <label class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ t('Password hint') }}</label>
            <input
              v-model="hint"
              type="text"
              maxlength="100"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              :placeholder="t('Optional password hint')"
            />
            <p class="text-[11px] text-gray-400">{{ t('Do not include the password itself') }}</p>
          </div>

          <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
        </div>

        <div class="mt-5 flex justify-end gap-2">
          <button class="rounded-lg px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700" @click="handleCancel">
            {{ t('Cancel') }}
          </button>
          <button
            class="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!canSubmit || loading"
            @click="handleReset"
          >
            {{ loading ? t('Saving...') : t('Reset session password') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { X } from 'lucide-vue-next';
import { resetSessionPassword } from '../../api/agent';

const props = defineProps<{
  open: boolean;
  sessionId: string;
}>();

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void;
  (e: 'success', hasPassword: boolean): void;
}>();

const { t } = useI18n();
const accountPassword = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const hint = ref('');
const error = ref('');
const loading = ref(false);

const newPasswordMeetsRule = computed(() => {
  const categories = [
    /[a-z]/.test(newPassword.value),
    /[A-Z]/.test(newPassword.value),
    /\d/.test(newPassword.value),
  ].filter(Boolean).length;
  return newPassword.value.length >= 4 && categories >= 2;
});

const canSubmit = computed(() => {
  if (!accountPassword.value) return false;
  if (!newPassword.value) return true;
  return newPasswordMeetsRule.value && newPassword.value === confirmPassword.value;
});

watch(() => props.open, (open) => {
  if (open) {
    accountPassword.value = '';
    newPassword.value = '';
    confirmPassword.value = '';
    hint.value = '';
    error.value = '';
    loading.value = false;
  }
});

const handleCancel = () => {
  if (!loading.value) emit('update:open', false);
};

const handleReset = async () => {
  if (!canSubmit.value || loading.value) return;
  loading.value = true;
  error.value = '';
  try {
    const result = await resetSessionPassword(props.sessionId, {
      account_password: accountPassword.value,
      new_password: newPassword.value || undefined,
      hint: newPassword.value ? hint.value || undefined : undefined,
    });
    emit('success', result.has_password);
    emit('update:open', false);
  } catch (err: any) {
    error.value = err?.message || t('Failed to update session password');
  } finally {
    loading.value = false;
  }
};
</script>

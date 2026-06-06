<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 dark:bg-black/50" @click.self="handleCancel">
      <div class="w-[420px] max-w-[92vw] rounded-xl border border-gray-100 bg-white p-5 shadow-xl dark:border-gray-700 dark:bg-gray-800">
        <div class="mb-4 flex items-start justify-between gap-4">
          <div>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ dialogTitle }}</h3>
            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ dialogDescription }}</p>
          </div>
          <button class="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700" @click="handleCancel">
            <X :size="16" />
          </button>
        </div>

        <div class="space-y-3">
          <div v-if="mode === 'update'" class="space-y-1.5">
            <label class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ t('Current session password') }}</label>
            <input
              v-model="oldPassword"
              type="password"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              :placeholder="t('Enter current session password')"
            />
          </div>

          <div v-if="mode === 'remove'" class="space-y-1.5">
            <label class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ t('Session password') }}</label>
            <input
              v-model="password"
              type="password"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              :placeholder="t('Enter session password')"
              @keyup.enter="handleSubmit"
            />
          </div>

          <template v-else>
            <div class="space-y-1.5">
              <label class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ mode === 'update' ? t('New session password') : t('Session password') }}</label>
              <input
                v-model="password"
                type="password"
                class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                :placeholder="t('At least 4 characters')"
              />
              <p class="text-[11px] text-gray-400">{{ t('Session password rule') }}</p>
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ t('Confirm session password') }}</label>
              <input
                v-model="confirmPassword"
                type="password"
                class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                :placeholder="t('Enter session password again')"
                @keyup.enter="handleSubmit"
              />
              <p v-if="confirmPassword && password !== confirmPassword" class="text-[11px] text-red-500">
                {{ t('Session passwords do not match') }}
              </p>
            </div>

            <div class="space-y-1.5">
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
          </template>

          <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
        </div>

        <div class="mt-5 flex justify-end gap-2">
          <button
            v-if="mode === 'update'"
            class="rounded-lg px-3 py-1.5 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
            :disabled="loading"
            @click="$emit('switch-mode', 'remove')"
          >
            {{ t('Remove session password') }}
          </button>
          <button class="rounded-lg px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700" @click="handleCancel">
            {{ t('Cancel') }}
          </button>
          <button
            class="rounded-lg px-3 py-1.5 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
            :class="mode === 'remove' ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'"
            :disabled="!canSubmit || loading"
            @click="handleSubmit"
          >
            {{ loading ? t('Saving...') : submitLabel }}
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
import { removeSessionPassword, setSessionPassword, updateSessionPassword } from '../../api/agent';

type Mode = 'set' | 'update' | 'remove';

const props = defineProps<{
  open: boolean;
  sessionId: string;
  mode: Mode;
}>();

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void;
  (e: 'success', hasPassword: boolean): void;
  (e: 'switch-mode', mode: Mode): void;
}>();

const { t } = useI18n();
const oldPassword = ref('');
const password = ref('');
const confirmPassword = ref('');
const hint = ref('');
const error = ref('');
const loading = ref(false);

const dialogTitle = computed(() => {
  if (props.mode === 'update') return t('Change session password');
  if (props.mode === 'remove') return t('Remove session password');
  return t('Set session password');
});

const dialogDescription = computed(() => {
  if (props.mode === 'remove') return t('Enter the current session password to remove protection.');
  return t('Protect this session with a password.');
});

const submitLabel = computed(() => {
  if (props.mode === 'remove') return t('Remove session password');
  if (props.mode === 'update') return t('Change session password');
  return t('Set session password');
});

const passwordMeetsRule = computed(() => {
  const categories = [
    /[a-z]/.test(password.value),
    /[A-Z]/.test(password.value),
    /\d/.test(password.value),
  ].filter(Boolean).length;
  return password.value.length >= 4 && categories >= 2;
});

const canSubmit = computed(() => {
  if (props.mode === 'remove') return password.value.length > 0;
  if (props.mode === 'update' && !oldPassword.value) return false;
  return passwordMeetsRule.value && password.value === confirmPassword.value;
});

watch(() => props.open, (open) => {
  if (open) {
    oldPassword.value = '';
    password.value = '';
    confirmPassword.value = '';
    hint.value = '';
    error.value = '';
    loading.value = false;
  }
});

const close = () => {
  emit('update:open', false);
};

const handleCancel = () => {
  if (!loading.value) close();
};

const handleSubmit = async () => {
  if (!canSubmit.value || loading.value) return;
  if (props.mode !== 'remove' && password.value !== confirmPassword.value) {
    error.value = t('Session passwords do not match');
    return;
  }

  loading.value = true;
  error.value = '';
  try {
    if (props.mode === 'set') {
      await setSessionPassword(props.sessionId, { password: password.value, hint: hint.value || undefined });
      emit('success', true);
    } else if (props.mode === 'update') {
      await updateSessionPassword(props.sessionId, {
        old_password: oldPassword.value,
        new_password: password.value,
        hint: hint.value || undefined,
      });
      emit('success', true);
    } else {
      await removeSessionPassword(props.sessionId, { password: password.value });
      emit('success', false);
    }
    close();
  } catch (err: any) {
    error.value = err?.message || t('Failed to update session password');
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <span
    class="inline-flex items-center rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700 dark:border-amber-800/60 dark:bg-amber-900/20 dark:text-amber-300"
  >
    {{ t('Sandbox Taken Over') }}
  </span>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
</script>

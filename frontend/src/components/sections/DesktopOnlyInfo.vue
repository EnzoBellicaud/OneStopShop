<!-- THIS APPEARS WHEN YOUR SCREEN IS SMALLER THAN DESKTOP SCREEN -->

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<template>
  <div class="desktop-only-overlay">
    <div class="desktop-only-message">
      <h2>{{ t('desktop.title') }}</h2>
      <p>{{ t('desktop.sub') }}</p>
    </div>
  </div>
</template>

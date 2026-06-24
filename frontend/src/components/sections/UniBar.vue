<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<template>
    <div class="uni-bar">
        <div class="uni-bar-inner">
            <span class="uni-bar-label">{{ t('uniBar.label') }}</span>
            <div class="uni-logos">
            <span class="uni-badge">University of Stockholm</span>
            <span class="uni-badge">KTH Royal Institute</span>
            <span class="uni-badge">Uppsala University</span>
            <span class="uni-badge">Lund University</span>
            <span class="uni-badge">Chalmers</span>
            <span class="uni-badge">Linköping University</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<template>
    <div class="stats">
        <div class="stat-card">
            <div class="stat-num">9<span>+</span></div>
            <div class="stat-label">{{ t('stats.partners') }}</div>
        </div>
        <div class="stat-card">
            <div class="stat-num">340<span>+</span></div>
            <div class="stat-label">{{ t('stats.opportunities') }}</div>
        </div>
        <div class="stat-card">
            <div class="stat-num">120<span>+</span></div>
            <div class="stat-label">{{ t('stats.thesis') }}</div>
        </div>
        <div class="stat-card">
            <div class="stat-num">80<span>+</span></div>
            <div class="stat-label">{{ t('stats.internships') }}</div>
        </div>
    </div>
</template>

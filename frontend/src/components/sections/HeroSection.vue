<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<template>
    <section class="hero">
        <div>
            <div class="hero-eyebrow">{{ t('hero.eyebrow') }}</div>
            <h1>{{ t('hero.title') }} <em>{{ t('hero.titleEm') }}</em></h1>
            <p class="hero-sub">{{ t('hero.sub') }}</p>
            <div class="hero-actions">
            <a class="btn-ghost" href="#about">{{ t('hero.learnMore') }}</a>
        </div>
    </div>
    <div class="hero-img">
            <div class="img-icon">
                <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
            </div>
            <span class="img-placeholder-label">{{ t('hero.imageLabel') }}</span>
    </div>
    </section>
</template>

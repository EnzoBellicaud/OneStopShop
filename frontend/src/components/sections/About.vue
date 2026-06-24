
<script setup>
    import { computed } from 'vue';
    import { useRoute } from 'vue-router'
    import { useI18n } from 'vue-i18n'

    const route = useRoute()
    const { t } = useI18n()

    const isLanding = computed(() => route.name === 'landing')
</script>

<template>
    <section :class="['about', { 'about-landing': isLanding }]" id="about">
        <div class="about-inner">
            <div :class="['about-img', { 'about-img-landing': isLanding }]">
              <img src="/about-map.jpg" alt="Map of partner countries" class="about-map-img" />
            </div>
            <div>
            <p class="about-eyebrow">{{ t('about.eyebrow') }}</p>
            <h2>{{ t('about.titlePre') }} <em>{{ t('about.titleEm') }}</em> {{ t('about.titlePost') }}</h2>
            <p>{{ t('about.p1') }}</p>
            <p>{{ t('about.p2') }}</p>
            <div class="about-features">
                <div class="feat">
                <div class="feat-icon">
                    <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                </div>
                <div class="feat-text">
                    <strong>{{ t('about.f1Title') }}</strong>
                    <span>{{ t('about.f1Desc') }}</span>
                </div>
                </div>
                <div class="feat">
                <div class="feat-icon">
                    <svg viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                </div>
                <div class="feat-text">
                    <strong>{{ t('about.f2Title') }}</strong>
                    <span>{{ t('about.f2Desc') }}</span>
                </div>
                </div>
                <div class="feat">
                <div class="feat-icon">
                    <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
                </div>
                <div class="feat-text">
                    <strong>{{ t('about.f3Title') }}</strong>
                    <span>{{ t('about.f3Desc') }}</span>
                </div>
                </div>
                <div class="feat">
                <div class="feat-icon">
                    <svg viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                </div>
                <div class="feat-text">
                    <strong>{{ t('about.f4Title') }}</strong>
                    <span>{{ t('about.f4Desc') }}</span>
                </div>
                </div>
            </div>
            </div>
        </div>
    </section>
</template>
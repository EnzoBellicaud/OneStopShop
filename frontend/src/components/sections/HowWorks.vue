<script setup>
    import { computed } from 'vue';
    import { useRoute } from 'vue-router'
    import { useI18n } from 'vue-i18n'

    const route = useRoute()
    const { t } = useI18n()

    const isLanding = computed(() => route.name === 'landing')
</script>

<template>
    <section class="how" id="how">
        <div class="section-header" style="padding:0; margin-bottom:0;">
            <div>
            <p class="section-eyebrow">{{ t('how.eyebrow') }}</p>
            <h2 class="section-title">{{ t('how.title') }}</h2>
            </div>
        </div>
        <div class="how-steps">
            <div :class="['step', { 'step-landing': isLanding}]">
            <div :class="['step-num', { 'step-num-landing': isLanding}]">01</div>
            <h3>{{ t('how.step1Title') }}</h3>
            <p>{{ t('how.step1Desc') }}</p>
            </div>
            <div :class="['step', { 'step-landing': isLanding}]">
            <div :class="['step-num', { 'step-num-landing': isLanding}]">02</div>
            <h3>{{ t('how.step2Title') }}</h3>
            <p>{{ t('how.step2Desc') }}</p>
            </div>
            <div :class="['step', { 'step-landing': isLanding}]">
            <div :class="['step-num', { 'step-num-landing': isLanding}]">03</div>
            <h3>{{ t('how.step3Title') }}</h3>
            <p>{{ t('how.step3Desc') }}</p>
            </div>
        </div>
    </section>
</template>

<script setup>
    import { computed } from 'vue';
    import { useRoute } from 'vue-router'

    const route = useRoute()

    const isLanding = computed(() => route.name === 'landing')
</script>

<template>
    <section class="how" id="how">
        <div class="section-header" style="padding:0; margin-bottom:0;">
            <div>
            <p class="section-eyebrow">The process</p>
            <h2 class="section-title">How it works</h2>
            </div>
        </div>
        <div class="how-steps">
            <div :class="['step', { 'step-landing': isLanding}]">
            <div :class="['step-num', { 'step-num-landing': isLanding}]">01</div>
            <h3>Browse & filter</h3>
            <p>Search across all six universities using filters for opportunity type, field of study, duration, and location.</p>
            </div>
            <div :class="['step', { 'step-landing': isLanding}]">
            <div :class="['step-num', { 'step-num-landing': isLanding}]">02</div>
            <h3>Find your match</h3>
            <p>Read the full listing details — supervisor info, requirements, and deadlines — all presented in a consistent format.</p>
            </div>
            <div :class="['step', { 'step-landing': isLanding}]">
            <div :class="['step-num', { 'step-num-landing': isLanding}]">03</div>
            <h3>Apply at the source</h3>
            <p>Click "View at [university]" and you'll be redirected to the official university page to submit your application directly.</p>
            </div>
        </div>
    </section>
</template>
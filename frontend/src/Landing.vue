<script setup>
    import Header from './components/layout/AppHeader.vue';
    import Footer from './components/layout/AppFooter.vue';
    import About from './components/sections/About.vue';
    import HowWorks from './components/sections/HowWorks.vue';
    import ProfileSelection from './components/sections/ProfileSelection.vue';
    import Desktop from './components/sections/DesktopOnlyInfo.vue'
    import { ref, onMounted } from 'vue'
    import { useI18n } from 'vue-i18n'

    const { t } = useI18n()
    const show = ref(false)

    onMounted(() => {
        show.value = true
    })
</script>

<template>
    <div>
        <Header />

        <!-- Hero -->
        <section class="page-hero landing-hero">
            <div class="page-hero-inner">
                <p class="section-eyebrow">{{ t('landing.eyebrow') }}</p>
                <h1 class="page-title">{{ t('landing.title') }}</h1>
                <p class="page-sub">
                    {{ t('landing.subtitle') }}
                </p>
                <div class="hero-actions">
                    <router-link to="/student" class="btn-primary" :data-hover="t('landing.getStarted')">{{ t('landing.getStarted') }}</router-link>
                    <router-link to="/forum" class="btn-ghost">{{ t('landing.forum') }} →</router-link>
                </div>
            </div>
        </section>

        <transition name="slide">
            <ProfileSelection v-if="show" />
        </transition>
        <transition name="slide">
            <HowWorks v-if="show" />
        </transition>
        <transition name="slide">
            <About v-if="show" />
        </transition>

        <Footer />
        <Desktop />
    </div>
</template>

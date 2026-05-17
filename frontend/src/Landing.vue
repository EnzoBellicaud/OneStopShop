<script setup>
    import Header from './components/layout/AppHeader.vue';
    import Footer from './components/layout/AppFooter.vue';
    import About from './components/sections/About.vue';
    import HowWorks from './components/sections/HowWorks.vue';
    import ProfileSelection from './components/sections/ProfileSelection.vue';
    import Desktop from './components/sections/DesktopOnlyInfo.vue'
    import { ref, onMounted } from 'vue'

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
                <p class="section-eyebrow">One Stop Shop</p>
                <h1 class="page-title">Your gateway to <em>university opportunities</em></h1>
                <p class="page-sub">
                    Find internships, research groups, trainings, and more across our partner universities — all in one place.
                </p>
                <div class="hero-actions">
                    <router-link to="/student" class="btn-primary" data-hover="Get started">Get started</router-link>
                    <router-link to="/forum" class="btn-ghost">Visit Forum →</router-link>
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

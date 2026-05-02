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
    <div class="sharedbg">
        <Header />
        <transition name="slide">
            <ProfileSelection v-if="show" />
        </transition>
        <transition name="slide">
            <HowWorks v-if="show" />
        </transition>
        <transition name="slide">
            <About v-if="show" />
        </transition>
    </div>
        <Footer />
        <Desktop />
</template>

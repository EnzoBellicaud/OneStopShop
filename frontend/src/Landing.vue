<script setup>
    import Header from './components/layout/AppHeader.vue';
    import Footer from './components/layout/AppFooter.vue';
    import About from './components/sections/About.vue';
    import HowWorks from './components/sections/HowWorks.vue';
    import ProfileSelection from './components/sections/ProfileSelection.vue';
</script>

<template>
    <div class="sharedbg">
        <Header />
        <ProfileSelection />
        <HowWorks />
        <About />
    </div>
    <Footer />
</template>
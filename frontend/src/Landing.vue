<script setup>
    import Header from './components/layout/AppHeader.vue';
    import Footer from './components/layout/AppFooter.vue';
    import Selection from './components/sections/SelectCards.vue';
    import Hero from './components/sections/HeroSection.vue'
    import HeroV2 from './components/sections/HeroSectionV2.vue';
    import About from './components/sections/About.vue';
    import HowWorks from './components/sections/HowWorks.vue';
    import Contact from './components/sections/Contact.vue';
</script>

<template>
    <!-- <Hero /> -->
    <div class="sharedbg">
        <Header />
        <HeroV2 />
        <Selection />
        <About />
        <HowWorks />
        <Contact />
    </div>
    <Footer />
</template>
<script setup>
import { RouterLink } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
</script>

<template>
  <AppHeader />
  <main class="not-found-wrap">
    <p class="not-found-num">404</p>
    <h1 class="not-found-title">Page not found</h1>
    <p class="not-found-sub">
      The page you're looking for doesn't exist or has been moved.
    </p>
    <div class="not-found-actions">
      <RouterLink to="/" class="btn-primary">Go home</RouterLink>
      <RouterLink to="/offers" class="btn-ghost">Browse opportunities</RouterLink>
    </div>
  </main>
  <AppFooter />
</template>

<style scoped>
.not-found-wrap {
  max-width: 1200px;
  margin: 0 auto;
  padding: 8rem 3rem;
  text-align: center;
}
.not-found-num {
  font-family: 'DM Serif Display', serif;
  font-size: 96px;
  color: var(--border);
  line-height: 1;
  margin-bottom: 1rem;
}
.not-found-title {
  font-family: 'DM Serif Display', serif;
  font-size: 36px;
  color: var(--ink);
  letter-spacing: -0.5px;
  margin-bottom: 1rem;
}
.not-found-sub {
  font-size: 15px;
  color: var(--ink-soft);
  max-width: 380px;
  margin: 0 auto 2.5rem;
}
.not-found-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  align-items: center;
}
</style>

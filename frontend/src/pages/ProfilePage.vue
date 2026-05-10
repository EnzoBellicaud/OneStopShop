<script setup>
import { RouterLink } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import { useAuth } from '../composables/useAuth'

const { user } = useAuth()
</script>

<template>
  <AppHeader />
  <main>
    <div class="profile-wrap">
      <section class="profile-header">
        <div class="avatar">{{ user?.username?.[0]?.toUpperCase() ?? '?' }}</div>
        <div>
          <h1 class="profile-name">{{ user?.username ?? 'My Profile' }}</h1>
          <p class="profile-email">{{ user?.email ?? '' }}</p>
          <span class="type-tag tag-thesis" style="margin-top: 8px; display: inline-block;">
            {{ user?.profile ?? 'Student' }}
          </span>
        </div>
      </section>

      <section class="profile-section">
        <p class="section-eyebrow">Saved</p>
        <h2 class="section-title" style="margin-bottom: 1.5rem;">My Opportunities</h2>
        <div class="empty-state">
          <p>No saved opportunities yet.</p>
          <RouterLink to="/offers" class="btn-primary" style="display: inline-block; margin-top: 1rem;">
            Browse opportunities
          </RouterLink>
        </div>
      </section>

      <section class="profile-section">
        <p class="section-eyebrow">Settings</p>
        <h2 class="section-title" style="margin-bottom: 1.5rem;">Account Settings</h2>
        <div class="settings-card">
          <div class="settings-row">
            <span class="settings-label">Username</span>
            <span class="settings-value">{{ user?.username ?? '—' }}</span>
          </div>
          <div class="settings-row">
            <span class="settings-label">Email</span>
            <span class="settings-value">{{ user?.email ?? '—' }}</span>
          </div>
          <div class="settings-row">
            <span class="settings-label">Profile type</span>
            <span class="settings-value">{{ user?.profile ?? '—' }}</span>
          </div>
        </div>
      </section>
    </div>
  </main>
  <AppFooter />
</template>

<style scoped>
.profile-wrap {
  max-width: 800px;
  margin: 0 auto;
  padding: 3rem;
  display: flex;
  flex-direction: column;
  gap: 3rem;
}
.profile-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border);
}
.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--ink);
  color: var(--white);
  font-family: 'DM Serif Display', serif;
  font-size: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.profile-name {
  font-family: 'DM Serif Display', serif;
  font-size: 26px;
  letter-spacing: -0.3px;
  color: var(--ink);
  margin-bottom: 4px;
}
.profile-email {
  font-size: 13px;
  color: var(--ink-soft);
}
.profile-section {
  display: flex;
  flex-direction: column;
}
.empty-state {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 2.5rem;
  text-align: center;
  color: var(--ink-soft);
  font-size: 14px;
}
.settings-card {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  overflow: hidden;
}
.settings-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}
.settings-row:last-child {
  border-bottom: none;
}
.settings-label {
  color: var(--ink-soft);
}
.settings-value {
  font-weight: 500;
  color: var(--ink);
}
</style>

<template>
  <section class="profile-selector" id="profiles">
    <div class="section-header">
      <div>
        <p class="section-eyebrow">{{ t('profiles.eyebrow') }}</p>
        <h2 class="section-title">{{ t('profiles.titlePre') }} <em>{{ t('profiles.titleEm') }}</em></h2>
      </div>
    </div>

    <div class="profile-grid">
      <router-link
        v-for="profile in profiles"
        :key="profile.key"
        :to="profile.route"
        class="profile-card"
        @click="saveProfile(profile)"
      >
        <div class="profile-card-icon">{{ profile.icon }}</div>
        <h3>{{ t(profile.titleKey) }}</h3>
        <p>{{ t(profile.descKey) }}</p>
        <span class="profile-card-cta">{{ t('profiles.cta') }}</span>
      </router-link>
    </div>
  </section>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const profiles = [
  {
    key: 'student',
    titleKey: 'profiles.studentTitle',
    icon: '🎓',
    descKey: 'profiles.studentDesc',
    route: '/student',
  },
  {
    key: 'academic_staff',
    titleKey: 'profiles.staffTitle',
    icon: '🔬',
    descKey: 'profiles.staffDesc',
    route: '/staff',
  },
  {
    key: 'external_user',
    titleKey: 'profiles.externalTitle',
    icon: '🌐',
    descKey: 'profiles.externalDesc',
    route: '/external_user',
  },
]

function saveProfile(profile) {
  // Persist a stable, locale-independent label for the selected profile.
  localStorage.setItem('selected_profile', JSON.stringify({ key: profile.key, route: profile.route }))
}
</script>

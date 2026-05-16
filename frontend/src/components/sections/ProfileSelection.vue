<template>
  <section class="profile-selector" id="profiles">
    <div class="section-header">
      <div>
        <p class="section-eyebrow">Choose your role</p>
        <h2 class="section-title">How would you like to <em>explore?</em></h2>
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
        <h3>{{ profile.title }}</h3>
        <p>{{ profile.description }}</p>
        <span class="profile-card-cta">View tailored content →</span>
      </router-link>
    </div>
  </section>
</template>

<script setup>
const profiles = [
  {
    key: 'student',
    title: 'Student',
    icon: '🎓',
    description: 'Find internships, thesis projects, challenges, hackathons, and student opportunities.',
    route: '/student',
  },
  {
    key: 'academic_staff',
    title: 'Academic Staff',
    icon: '🔬',
    description: 'Discover research groups, infrastructure, expert services, and project opportunities.',
    route: '/staff',
  },
  {
    key: 'external_user',
    title: 'External User',
    icon: '🌐',
    description: 'Explore lifelong learning, expert services, trainings, testbeds, and labs.',
    route: '/external_user',
  },
]

function saveProfile(profile) {
  localStorage.setItem('selected_profile', JSON.stringify(profile))
}
</script>

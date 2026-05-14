<template>
  <section class="dashboard-page">
    <div class="dashboard-header">
      <div>
        <p class="section-eyebrow">Profile Center</p>
        <h1>My Dashboard</h1>
        <p class="dashboard-subtitle">
          Manage your needs, offers, saved favorites, and matching hits.
        </p>
      </div>
      <button class="btn-primary">+ Add Need / Offer</button>
    </div>

    <div class="dashboard-stats">
      <div><strong>{{ needs.length }}</strong><span>Needs</span></div>
      <div><strong>{{ offers.length }}</strong><span>Offers</span></div>
      <div><strong>{{ favorites.length }}</strong><span>Favorites</span></div>
      <div><strong>{{ matches.length }}</strong><span>Matches</span></div>
    </div>

    <div class="dashboard-tabs">
      <button @click="tab = 'matches'" :class="{ active: tab === 'matches' }">Matching Hits</button>
      <button @click="tab = 'needs'" :class="{ active: tab === 'needs' }">My Needs</button>
      <button @click="tab = 'offers'" :class="{ active: tab === 'offers' }">My Offers</button>
      <button @click="tab = 'favorites'" :class="{ active: tab === 'favorites' }">Favorites</button>
    </div>

    <div class="dashboard-grid">
      <article
        v-for="item in currentItems"
        :key="item.id"
        class="dashboard-card"
      >
        <span class="dashboard-tag">{{ item.type }}</span>
        <h3>{{ item.title }}</h3>
        <p>{{ item.description }}</p>

        <div class="dashboard-footer">
          <span>{{ item.meta }}</span>
          <a :href="`mailto:${item.email}?subject=Interest in ${item.title}`">
            Reach out
          </a>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'

const tab = ref('matches')

const needs = ref([
  {
    id: 1,
    type: 'Need',
    title: 'Looking for thesis collaboration',
    description: 'I am searching for a thesis project in AI, software engineering, or data systems.',
    meta: 'Open',
    email: 'contact@example.com'
  }
])

const offers = ref([
  {
    id: 2,
    type: 'Offer',
    title: 'Frontend prototype support',
    description: 'I can help build Vue/Figma prototypes for student or academic projects.',
    meta: 'Available',
    email: 'contact@example.com'
  }
])

const favorites = ref([
  {
    id: 3,
    type: 'Favorite',
    title: 'AI-driven energy optimisation thesis',
    description: 'Saved opportunity from KTH related to smart grid optimisation.',
    meta: 'KTH',
    email: 'contact@example.com'
  }
])

const matches = ref([
  {
    id: 4,
    type: '92% Match',
    title: 'Research Assistant — Computational Biology',
    description: 'Matched based on your interests in software, data, and research.',
    meta: 'Uppsala University',
    email: 'contact@example.com'
  },
  {
    id: 5,
    type: '86% Match',
    title: 'Advanced Machine Learning Course',
    description: 'Recommended because your profile includes AI and software engineering.',
    meta: 'Chalmers',
    email: 'contact@example.com'
  }
])

const currentItems = computed(() => {
  if (tab.value === 'needs') return needs.value
  if (tab.value === 'offers') return offers.value
  if (tab.value === 'favorites') return favorites.value
  return matches.value
})
</script>
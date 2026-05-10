<script setup>
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'

const activeFilter = ref('All')
const filters = ['All', 'Thesis', 'Internship', 'Job', 'Course']

const allCards = [
  { id: 1, type: 'Thesis', tagClass: 'tag-thesis', uni: 'UNIBZ',
    title: 'Machine Learning for Climate Data Analysis', location: 'Bolzano, Italy', deadline: 'Jun 2025' },
  { id: 2, type: 'Internship', tagClass: 'tag-intern', uni: 'LiU',
    title: 'Software Engineering Internship — Data Platforms', location: 'Linköping, Sweden', deadline: 'Jul 2025' },
  { id: 3, type: 'Job', tagClass: 'tag-job', uni: 'TU/e',
    title: 'Junior Backend Developer — Research Institute', location: 'Eindhoven, Netherlands', deadline: 'May 2025' },
  { id: 4, type: 'Course', tagClass: 'tag-course', uni: 'UNIBZ',
    title: 'Advanced Algorithms — Spring Semester', location: 'Bolzano, Italy', deadline: 'Sep 2025' },
  { id: 5, type: 'Thesis', tagClass: 'tag-thesis', uni: 'LiU',
    title: 'Human-Computer Interaction in Hybrid Workplaces', location: 'Linköping, Sweden', deadline: 'Aug 2025' },
  { id: 6, type: 'Internship', tagClass: 'tag-intern', uni: 'TU/e',
    title: 'UX Research Internship — EdTech Startup', location: 'Eindhoven, Netherlands', deadline: 'Jun 2025' },
]

const filteredCards = computed(() =>
  activeFilter.value === 'All'
    ? allCards
    : allCards.filter(c => c.type === activeFilter.value)
)
</script>

<template>
  <AppHeader />
  <main>
    <section class="page-hero">
      <div class="page-hero-inner">
        <p class="section-eyebrow">Discover</p>
        <h1 class="page-title">Browse Opportunities</h1>
        <p class="page-sub">
          Thesis topics, internships, jobs and courses from our partner universities.
        </p>
      </div>
    </section>

    <div class="filter-bar">
      <input class="search-input" type="text" placeholder="Search opportunities..." />
      <select class="filter-select">
        <option>All countries</option>
        <option>Italy</option>
        <option>Sweden</option>
        <option>Netherlands</option>
      </select>
      <button
        v-for="f in filters"
        :key="f"
        class="filter-chip"
        :class="{ active: activeFilter === f }"
        @click="activeFilter = f"
      >{{ f }}</button>
    </div>

    <div class="cards-grid">
      <div v-for="card in filteredCards" :key="card.id" class="opp-card">
        <div class="card-top">
          <span class="type-tag" :class="card.tagClass">{{ card.type }}</span>
          <div class="uni-logo-sm">{{ card.uni }}</div>
        </div>
        <p class="card-title">{{ card.title }}</p>
        <div class="card-meta">
          <div class="card-meta-row">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="13" height="13">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>
            {{ card.location }}
          </div>
        </div>
        <div class="card-footer">
          <span class="deadline">Deadline: {{ card.deadline }}</span>
          <RouterLink :to="`/offers/${card.id}`" class="btn-view">View</RouterLink>
        </div>
      </div>
    </div>
  </main>
  <AppFooter />
</template>

<style scoped>
.page-hero {
  border-bottom: 1px solid var(--border);
  padding: 4rem 3rem 3rem;
  background: var(--white);
}
.page-hero-inner {
  max-width: 1200px;
  margin: 0 auto;
}
.page-title {
  font-family: 'DM Serif Display', serif;
  font-size: 40px;
  letter-spacing: -0.5px;
  color: var(--ink);
  margin: 0.5rem 0 1rem;
}
.page-sub {
  font-size: 15px;
  color: var(--ink-soft);
  max-width: 480px;
}
</style>

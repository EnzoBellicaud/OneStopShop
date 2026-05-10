<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'

const route = useRoute()
const router = useRouter()

const tagMap = {
  1: {
    type: 'Thesis', tagClass: 'tag-thesis', uni: 'UNIBZ',
    title: 'Machine Learning for Climate Data Analysis',
    location: 'Bolzano, Italy', deadline: 'Jun 2025',
    description: 'Conduct research on applying ML models to climate sensor data from the Alps region. Co-supervised with the Faculty of Computer Science.',
  },
  2: {
    type: 'Internship', tagClass: 'tag-intern', uni: 'LiU',
    title: 'Software Engineering Internship — Data Platforms',
    location: 'Linköping, Sweden', deadline: 'Jul 2025',
    description: 'Join the data engineering team at Linköping University for a 6-month internship building data pipelines and analytics tooling.',
  },
  3: {
    type: 'Job', tagClass: 'tag-job', uni: 'TU/e',
    title: 'Junior Backend Developer — Research Institute',
    location: 'Eindhoven, Netherlands', deadline: 'May 2025',
    description: 'Work as a junior backend developer at TU/e\'s interdisciplinary research institute, contributing to open-source academic tooling.',
  },
  4: {
    type: 'Course', tagClass: 'tag-course', uni: 'UNIBZ',
    title: 'Advanced Algorithms — Spring Semester',
    location: 'Bolzano, Italy', deadline: 'Sep 2025',
    description: 'Enroll in the Advanced Algorithms graduate course. Covers complexity theory, graph algorithms, and approximation methods.',
  },
  5: {
    type: 'Thesis', tagClass: 'tag-thesis', uni: 'LiU',
    title: 'Human-Computer Interaction in Hybrid Workplaces',
    location: 'Linköping, Sweden', deadline: 'Aug 2025',
    description: 'Investigate HCI patterns and user needs in distributed, hybrid work settings. Fieldwork + prototype evaluation required.',
  },
  6: {
    type: 'Internship', tagClass: 'tag-intern', uni: 'TU/e',
    title: 'UX Research Internship — EdTech Startup',
    location: 'Eindhoven, Netherlands', deadline: 'Jun 2025',
    description: 'Join a fast-growing EdTech startup incubated at TU/e. Conduct user research, run usability studies, and inform product direction.',
  },
}

const offer = computed(() =>
  tagMap[Number(route.params.id)] ?? {
    type: 'Opportunity', tagClass: 'tag-thesis', uni: '—',
    title: `Opportunity #${route.params.id}`,
    location: '—', deadline: '—',
    description: 'Full details will be loaded from the API.',
  }
)
</script>

<template>
  <AppHeader />
  <main>
    <div class="detail-wrap">
      <button class="back-btn" @click="router.back()">← Back to offers</button>

      <div class="detail-card">
        <div class="card-top">
          <span class="type-tag" :class="offer.tagClass">{{ offer.type }}</span>
          <div class="uni-logo-sm">{{ offer.uni }}</div>
        </div>
        <h1 class="detail-title">{{ offer.title }}</h1>
        <div class="card-meta" style="margin-bottom: 1.5rem;">
          <div class="card-meta-row">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="13" height="13">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>
            {{ offer.location }}
          </div>
          <div class="card-meta-row">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="13" height="13">
              <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            Deadline: {{ offer.deadline }}
          </div>
        </div>
        <p class="detail-desc">{{ offer.description }}</p>
        <div class="detail-actions">
          <button class="btn-primary" disabled>Apply now</button>
          <button class="btn-ghost" @click="router.back()">Back to list</button>
        </div>
      </div>
    </div>
  </main>
  <AppFooter />
</template>

<style scoped>
.detail-wrap {
  max-width: 780px;
  margin: 0 auto;
  padding: 3rem;
}
.back-btn {
  background: none;
  border: none;
  font-size: 13px;
  color: var(--ink-soft);
  cursor: pointer;
  padding: 0;
  margin-bottom: 1.5rem;
  display: block;
  font-family: 'DM Sans', sans-serif;
}
.back-btn:hover { color: var(--ink); }
.detail-card {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 2.5rem;
}
.detail-title {
  font-family: 'DM Serif Display', serif;
  font-size: 28px;
  letter-spacing: -0.4px;
  color: var(--ink);
  margin: 1rem 0 0.75rem;
}
.detail-desc {
  font-size: 15px;
  color: var(--ink-soft);
  line-height: 1.75;
  margin-bottom: 2rem;
}
.detail-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>

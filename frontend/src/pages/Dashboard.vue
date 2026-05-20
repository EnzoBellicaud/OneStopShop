<template>
  <section class="dashboard-page">
    <div class="dashboard-header">
      <div>
        <p class="section-eyebrow">Profile Center</p>
        <h1>My Dashboard</h1>
        <p class="dashboard-subtitle">Manage your needs, saved favorites, and matching hits.</p>
      </div>
    </div>

    <div v-if="loadingStats" class="dashboard-loading">Loading…</div>

    <template v-else>
      <div class="dashboard-stats">
        <div><strong>{{ stats.active_needs_count ?? 0 }}</strong><span>Needs</span></div>
        <div><strong>{{ stats.total_favorites ?? 0 }}</strong><span>Favorites</span></div>
        <div><strong>{{ stats.new_matches_count ?? 0 }}</strong><span>New Matches</span></div>
      </div>

      <div class="dashboard-tabs">
        <button @click="tab = 'matches'" :class="{ active: tab === 'matches' }">Matching Hits</button>
        <button @click="tab = 'needs'" :class="{ active: tab === 'needs' }">My Needs</button>
        <button @click="tab = 'favorites'" :class="{ active: tab === 'favorites' }">Favorites</button>
      </div>

      <div v-if="tabLoading" class="dashboard-loading">Loading…</div>
      <div v-else-if="tabError" class="dashboard-error">{{ tabError }}</div>

      <!-- Matching Hits -->
      <div v-else-if="tab === 'matches'" class="dashboard-grid">
        <div v-if="matches.length === 0" class="empty-state">No matching hits yet.</div>
        <article v-for="hit in matches" :key="hit.id" class="dashboard-card">
          <span class="dashboard-tag">{{ (hit.match_score * 100).toFixed(0) }}% Match</span>
          <h3>{{ hit.offer.title }}</h3>
          <p class="card-org">{{ hit.offer.organization }}</p>
          <p class="card-reason">{{ hit.match_reason }}</p>
          <div class="dashboard-footer">
            <span class="hit-status" :class="`status-${hit.status}`">{{ hit.status }}</span>
            <a :href="hit.offer.link" target="_blank" rel="noopener noreferrer">Open ↗</a>
          </div>
        </article>
      </div>

      <!-- Needs -->
      <div v-else-if="tab === 'needs'" class="dashboard-grid">
        <div v-if="needs.length === 0" class="empty-state">No active needs. Create one to start matching.</div>
        <article v-for="need in needs" :key="need.id" class="dashboard-card">
          <span class="dashboard-tag">{{ need.status }}</span>
          <h3>{{ need.title }}</h3>
          <p>{{ need.description }}</p>
          <div class="dashboard-footer">
            <span>{{ need.matching_hits_count }} match{{ need.matching_hits_count !== 1 ? 'es' : '' }}</span>
          </div>
        </article>
      </div>

      <!-- Favorites -->
      <div v-else-if="tab === 'favorites'" class="dashboard-grid">
        <div v-if="favorites.length === 0" class="empty-state">No saved favorites yet.</div>
        <article v-for="fav in favorites" :key="fav.id" class="dashboard-card">
          <span class="dashboard-tag">Favorite</span>
          <h3>{{ fav.offer.title }}</h3>
          <p class="card-org">{{ fav.offer.organization }}</p>
          <p v-if="fav.note" class="card-note">{{ fav.note }}</p>
          <div class="dashboard-footer">
            <a :href="fav.offer.link" target="_blank" rel="noopener noreferrer">Open ↗</a>
          </div>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { api } from '../services/api.js'
import { useAuth } from '../composables/useAuth.js'

const { user } = useAuth()
const tab = ref('matches')

const stats = ref({})
const loadingStats = ref(false)

const matches = ref([])
const needs = ref([])
const favorites = ref([])
const tabLoading = ref(false)
const tabError = ref(null)

async function loadDashboard() {
  if (!user.value) return
  loadingStats.value = true
  try {
    const res = await api.get(`/api/users/${user.value.id}/dashboard`)
    if (res.ok) {
      const data = await res.json()
      stats.value = data.stats
    }
  } finally {
    loadingStats.value = false
  }
  loadTab(tab.value)
}

async function loadTab(name) {
  if (!user.value) return
  tabLoading.value = true
  tabError.value = null
  try {
    if (name === 'matches') {
      const res = await api.get(`/api/users/${user.value.id}/matching-hits?sort=-match_score&page_size=25`)
      if (!res.ok) throw new Error('Failed to load matching hits')
      const data = await res.json()
      matches.value = data.results
    } else if (name === 'needs') {
      const res = await api.get(`/api/users/${user.value.id}/needs?status=active&page_size=25`)
      if (!res.ok) throw new Error('Failed to load needs')
      const data = await res.json()
      needs.value = data.results
    } else if (name === 'favorites') {
      const res = await api.get(`/api/users/${user.value.id}/favorites?page_size=25`)
      if (!res.ok) throw new Error('Failed to load favorites')
      const data = await res.json()
      favorites.value = data.results
    }
  } catch (e) {
    tabError.value = e.message
  } finally {
    tabLoading.value = false
  }
}

watch(tab, loadTab)
onMounted(loadDashboard)
</script>

<style scoped>
.dashboard-loading {
  padding: 3rem;
  text-align: center;
  color: var(--ink-soft);
  font-size: 14px;
}
.dashboard-error {
  padding: 1rem 2rem;
  color: var(--accent-mid);
  font-size: 14px;
}
.empty-state {
  padding: 2rem;
  color: var(--ink-soft);
  font-size: 14px;
  grid-column: 1 / -1;
}
.card-org {
  font-size: 12px;
  color: var(--ink-soft);
  margin: 0.25rem 0;
}
.card-reason {
  font-size: 13px;
  color: var(--ink-soft);
  margin: 0.5rem 0;
  line-height: 1.5;
}
.card-note {
  font-size: 13px;
  color: var(--ink-soft);
  font-style: italic;
  margin: 0.5rem 0;
}
.hit-status {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 2px 8px;
  border-radius: 20px;
  background: var(--border);
  color: var(--ink-soft);
}
.status-new { background: #e8f5e9; color: #2e7d32; }
.status-interested { background: #e3f2fd; color: #1565c0; }
.status-declined { background: #fce4ec; color: #c62828; }
</style>

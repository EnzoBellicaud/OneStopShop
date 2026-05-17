<template>
  <div>
    <AppHeader />

    <section class="page-hero db-page-hero">
      <div class="page-hero-inner">
        <p class="section-eyebrow">My Dashboard</p>
        <h1 class="page-title">Needs · Favorites · Matches</h1>
      </div>
    </section>

    <main class="db-wrap">
      <div v-if="!user" class="db-empty">
        Please <router-link to="/login">log in</router-link> to view your dashboard.
      </div>

      <template v-else>
        <div class="db-stats">
          <div class="db-stat">
            <strong>{{ stats.active_needs_count }}</strong>
            <span>Active needs</span>
          </div>
          <div class="db-stat">
            <strong>{{ stats.total_favorites }}</strong>
            <span>Favorites</span>
          </div>
          <div class="db-stat">
            <strong>{{ stats.new_matches_count }}</strong>
            <span>New matches</span>
          </div>
        </div>

        <div class="db-panels">

          <!-- NEEDS -->
          <section class="db-panel">
            <div class="panel-head">
              <h2>My Needs</h2>
              <div class="filter-chips">
                <button
                  v-for="s in ['active','fulfilled','archived']" :key="s"
                  :class="['chip', { active: needFilter === s }]"
                  @click="setNeedFilter(s)"
                >{{ s }}</button>
                <button :class="['chip', { active: needFilter === '' }]" @click="setNeedFilter('')">all</button>
              </div>
            </div>

            <form class="need-form" @submit.prevent="submitNeed">
              <input
                v-model="needDraft.title"
                class="db-input"
                placeholder="Need title"
                required
                maxlength="255"
              />
              <textarea
                v-model="needDraft.description"
                class="db-input"
                placeholder="Description (optional)"
                rows="2"
              ></textarea>
              <label v-if="editingNeedId" class="db-label">
                Status
                <select v-model="needDraft.status" class="db-input">
                  <option value="active">active</option>
                  <option value="fulfilled">fulfilled</option>
                  <option value="archived">archived</option>
                </select>
              </label>
              <div class="form-row">
                <button type="submit" class="btn-primary">
                  {{ editingNeedId ? 'Update need' : 'Add need' }}
                </button>
                <button v-if="editingNeedId" type="button" class="btn-ghost" @click="cancelNeedEdit">
                  Cancel
                </button>
              </div>
            </form>

            <div v-if="needsLoading" class="db-loading">Loading…</div>
            <ul v-else class="item-list">
              <li v-for="need in needs" :key="need.id" class="item-card">
                <div class="item-top">
                  <strong>{{ need.title }}</strong>
                  <span class="pill">{{ need.status }}</span>
                </div>
                <p v-if="need.description" class="item-desc">{{ need.description }}</p>
                <p class="item-meta">{{ need.matching_hits_count }} match{{ need.matching_hits_count !== 1 ? 'es' : '' }}</p>
                <div class="item-actions">
                  <button class="btn-ghost" @click="startEditNeed(need)">Edit</button>
                  <button class="btn-danger" @click="deleteNeed(need.id)">Delete</button>
                </div>
              </li>
              <li v-if="needs.length === 0" class="db-empty-state">No needs yet. Add one above.</li>
            </ul>
          </section>

          <!-- FAVORITES -->
          <section class="db-panel">
            <div class="panel-head">
              <h2>Saved Favorites</h2>
            </div>
            <div v-if="favsLoading" class="db-loading">Loading…</div>
            <ul v-else class="item-list">
              <li v-for="fav in favorites" :key="fav.id" class="item-card">
                <div class="item-top">
                  <strong>{{ fav.offer.title }}</strong>
                  <button class="btn-danger" @click="removeFavorite(fav.offer.id)">Remove</button>
                </div>
                <p class="item-meta">{{ fav.offer.organization }}</p>
                <p v-if="fav.note" class="item-desc">{{ fav.note }}</p>
                <a :href="fav.offer.link" target="_blank" rel="noopener noreferrer" class="ext-link">
                  Open offer ↗
                </a>
              </li>
              <li v-if="favorites.length === 0" class="db-empty-state">
                No favorites yet. Save offers while browsing.
              </li>
            </ul>
          </section>

          <!-- MATCHING HITS -->
          <section class="db-panel matches-panel">
            <div class="panel-head">
              <h2>Matches</h2>
              <div class="filter-chips">
                <select v-model="matchFilter" class="db-select" @change="loadMatches">
                  <option value="">All statuses</option>
                  <option v-for="s in ['new','viewed','interested','declined']" :key="s" :value="s">{{ s }}</option>
                </select>
                <select v-model="matchSort" class="db-select" @change="loadMatches">
                  <option value="-match_score">Best score first</option>
                  <option value="created_at">Newest first</option>
                </select>
              </div>
            </div>

            <div v-if="hitsLoading" class="db-loading">Loading…</div>
            <ul v-else class="item-list">
              <li v-for="hit in matchingHits" :key="hit.id" class="item-card match-card">
                <div class="item-top">
                  <strong>{{ hit.offer.title }}</strong>
                  <span class="score-badge">{{ Math.round(hit.match_score * 100) }}%</span>
                </div>
                <p class="item-meta">
                  {{ hit.need.title }} ·
                  <span :class="'status-tag status-' + hit.status">{{ hit.status }}</span>
                </p>
                <p class="item-desc">{{ hit.match_reason }}</p>
                <a :href="hit.offer.link" target="_blank" rel="noopener noreferrer" class="ext-link">
                  Open offer ↗
                </a>
                <div class="item-actions">
                  <button
                    v-for="s in ['viewed','interested','declined']" :key="s"
                    :class="['btn-ghost', { active: hit.status === s }]"
                    :disabled="updatingHit === hit.id"
                    @click="updateHitStatus(hit.id, s)"
                  >{{ s }}</button>
                </div>
              </li>
              <li v-if="matchingHits.length === 0" class="db-empty-state">
                No matches for the current filter.
              </li>
            </ul>
          </section>

        </div>
      </template>
    </main>

    <AppFooter />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuth } from './composables/useAuth.js'
import { api } from './services/api.js'
import AppHeader from './components/layout/AppHeader.vue'
import AppFooter from './components/layout/AppFooter.vue'

const { user } = useAuth()

const stats = ref({ active_needs_count: 0, total_favorites: 0, new_matches_count: 0 })

const needs = ref([])
const needsLoading = ref(false)
const needFilter = ref('')
const editingNeedId = ref(null)
const needDraft = ref({ title: '', description: '', status: 'active' })

const favorites = ref([])
const favsLoading = ref(false)

const matchingHits = ref([])
const hitsLoading = ref(false)
const matchFilter = ref('')
const matchSort = ref('-match_score')
const updatingHit = ref(null)

async function loadStats() {
  const res = await api.get(`/api/users/${user.value.id}/dashboard`)
  if (res.ok) {
    const data = await res.json()
    stats.value = data.stats
  }
}

async function loadNeeds() {
  needsLoading.value = true
  try {
    const params = new URLSearchParams({ page_size: 50 })
    if (needFilter.value) params.set('status', needFilter.value)
    const res = await api.get(`/api/users/${user.value.id}/needs?${params}`)
    if (res.ok) needs.value = (await res.json()).results
  } finally {
    needsLoading.value = false
  }
}

async function loadFavorites() {
  favsLoading.value = true
  try {
    const res = await api.get(`/api/users/${user.value.id}/favorites?page_size=50`)
    if (res.ok) favorites.value = (await res.json()).results
  } finally {
    favsLoading.value = false
  }
}

async function loadMatches() {
  hitsLoading.value = true
  try {
    const params = new URLSearchParams({ page_size: 50, sort: matchSort.value })
    if (matchFilter.value) params.set('status', matchFilter.value)
    const res = await api.get(`/api/users/${user.value.id}/matching-hits?${params}`)
    if (res.ok) matchingHits.value = (await res.json()).results
  } finally {
    hitsLoading.value = false
  }
}

function setNeedFilter(s) {
  needFilter.value = s
  loadNeeds()
}

async function submitNeed() {
  const uid = user.value.id
  if (editingNeedId.value) {
    const body = {
      title: needDraft.value.title,
      description: needDraft.value.description,
      status: needDraft.value.status,
    }
    const res = await api.patch(`/api/users/${uid}/needs/${editingNeedId.value}`, body)
    if (res.ok) {
      const updated = await res.json()
      const idx = needs.value.findIndex(n => n.id === editingNeedId.value)
      if (idx !== -1) needs.value[idx] = updated
      cancelNeedEdit()
      loadStats()
    }
  } else {
    const body = { title: needDraft.value.title, description: needDraft.value.description }
    const res = await api.post(`/api/users/${uid}/needs`, body)
    if (res.ok) {
      needs.value.unshift(await res.json())
      needDraft.value = { title: '', description: '', status: 'active' }
      loadStats()
    }
  }
}

function startEditNeed(need) {
  editingNeedId.value = need.id
  needDraft.value = { title: need.title, description: need.description, status: need.status }
}

function cancelNeedEdit() {
  editingNeedId.value = null
  needDraft.value = { title: '', description: '', status: 'active' }
}

async function deleteNeed(needId) {
  const res = await api.delete(`/api/users/${user.value.id}/needs/${needId}`)
  if (res.ok) {
    needs.value = needs.value.filter(n => n.id !== needId)
    loadStats()
  }
}

async function removeFavorite(offerId) {
  const res = await api.delete(`/api/users/${user.value.id}/favorites/${offerId}`)
  if (res.ok) {
    favorites.value = favorites.value.filter(f => f.offer.id !== offerId)
    loadStats()
  }
}

async function updateHitStatus(hitId, status) {
  updatingHit.value = hitId
  try {
    const res = await api.patch(`/api/users/${user.value.id}/matching-hits/${hitId}`, { status })
    if (res.ok) {
      const updated = await res.json()
      const idx = matchingHits.value.findIndex(h => h.id === hitId)
      if (idx !== -1) matchingHits.value[idx] = updated
      loadStats()
    }
  } finally {
    updatingHit.value = null
  }
}

onMounted(() => {
  if (!user.value) return
  loadStats()
  loadNeeds()
  loadFavorites()
  loadMatches()
})
</script>

<style scoped>
.db-page-hero {
  padding-bottom: 0;
  border-bottom: 1px solid var(--border);
}

.db-wrap {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem 4rem;
}

.db-empty {
  text-align: center;
  padding: 4rem;
  color: var(--ink-soft);
}
.db-empty a { color: var(--ink); font-weight: 500; }

.db-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.db-stat {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 120px;
}
.db-stat strong { font-size: 1.8rem; color: var(--ink); }
.db-stat span { font-size: 0.8rem; color: var(--ink-soft); text-transform: uppercase; letter-spacing: 0.05em; }

.db-panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}
.matches-panel { grid-column: 1 / -1; }

.db-panel {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.panel-head h2 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--ink);
}

.filter-chips { display: flex; gap: 0.4rem; flex-wrap: wrap; align-items: center; }
.chip {
  padding: 0.2rem 0.7rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 0.78rem;
  cursor: pointer;
  color: var(--ink-soft);
  transition: all 0.15s;
}
.chip.active, .chip:hover {
  background: var(--ink);
  color: var(--white);
  border-color: var(--ink);
}

.db-select {
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 0.3rem 0.6rem;
  font-size: 0.82rem;
  background: var(--surface);
  color: var(--ink);
}

.need-form {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}
.db-input {
  width: 100%;
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--r);
  font-size: 0.9rem;
  background: var(--surface);
  color: var(--ink);
  font-family: inherit;
  resize: vertical;
}
.db-input:focus { outline: none; border-color: var(--ink); }
.db-label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.85rem; color: var(--ink-soft); }

.form-row { display: flex; gap: 0.5rem; }

.item-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 420px;
  overflow-y: auto;
}
.matches-panel .item-list { max-height: 500px; }

.item-card {
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 0.9rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.item-top strong { color: var(--ink); font-size: 0.95rem; }
.item-desc { font-size: 0.85rem; color: var(--ink-soft); }
.item-meta { font-size: 0.78rem; color: var(--ink-faint); }
.item-actions { display: flex; gap: 0.4rem; margin-top: 0.25rem; flex-wrap: wrap; }

.pill {
  font-size: 0.72rem;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--ink-soft);
  white-space: nowrap;
}

.score-badge {
  font-size: 0.78rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  background: #e8f5e9;
  color: #1a6b3c;
}

.status-tag { font-size: 0.78rem; font-weight: 500; }
.status-new    { color: var(--ink-soft); }
.status-interested { color: #1a6b3c; }
.status-viewed { color: #5b2da8; }
.status-declined { color: var(--ink-faint); }

.ext-link { font-size: 0.82rem; color: var(--ink-soft); text-decoration: none; }
.ext-link:hover { color: var(--ink); text-decoration: underline; }

.btn-primary {
  padding: 0.5rem 1.1rem;
  background: var(--ink);
  color: var(--white);
  border: none;
  border-radius: var(--r);
  font-size: 0.88rem;
  cursor: pointer;
  font-family: inherit;
  transition: opacity 0.15s;
}
.btn-primary:hover { opacity: 0.85; }

.btn-ghost {
  padding: 0.35rem 0.75rem;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--r);
  font-size: 0.82rem;
  cursor: pointer;
  color: var(--ink-soft);
  font-family: inherit;
  transition: all 0.15s;
}
.btn-ghost:hover, .btn-ghost.active {
  background: var(--ink);
  color: var(--white);
  border-color: var(--ink);
}
.btn-ghost:disabled { opacity: 0.45; cursor: not-allowed; }

.btn-danger {
  padding: 0.35rem 0.75rem;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--r);
  font-size: 0.82rem;
  cursor: pointer;
  color: var(--ink-faint);
  font-family: inherit;
  transition: all 0.15s;
}
.btn-danger:hover { background: #fef2f2; border-color: #fca5a5; color: #b91c1c; }

.db-loading { color: var(--ink-faint); font-size: 0.88rem; }
.db-empty-state { color: var(--ink-faint); font-size: 0.88rem; text-align: center; padding: 1rem 0; }
</style>

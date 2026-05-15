<template>
  <section class="selection-screen" :class="{ 'compact-mode': isSearching }">
    <div class="container">
      <div v-if="!isSearching" class="text-center">
        <h1 class="title">What are you <span>looking for?</span></h1>
        <p class="subtitle">Search opportunities or use quick filters below</p>
      </div>

      <div class="search-wrapper">
        <input
          type="text"
          class="search-input"
          :placeholder="searchPlaceholder || 'Search opportunities...'"
          v-model="searchTerm"
          @focus="isSearching = true"
          @input="onSearchInput"
        />
      </div>

      <div v-if="!isSearching" class="grid-profiles">
        <div
          v-for="item in shortcuts"
          :key="item"
          class="shortcut-card"
          @click="applyShortcut(item)"
        >
          <span class="item-name">{{ item }}</span>
          <button class="select-btn">Explore</button>
        </div>
      </div>

      <div v-else class="results-layout">
        <aside class="side-filters">
          <h3>Filters</h3>
          <div class="filter-group">
            <h4>Offer Type</h4>
            <label v-for="cat in shortcuts" :key="cat" class="checkbox-item">
              <input
                type="checkbox"
                :checked="activeFilter === cat"
                @change="toggleFilter(cat)"
              />
              {{ cat }}
            </label>
          </div>
          <button class="reset-btn" @click="resetSearch">Reset All</button>
        </aside>

        <main class="results-grid">
          <div class="results-header">
            <template v-if="loading">Loading…</template>
            <template v-else-if="fetchError">{{ fetchError }}</template>
            <template v-else>{{ total }} result{{ total !== 1 ? 's' : '' }} found</template>
          </div>

          <div v-if="loading" class="cards-container">
            <div v-for="n in 3" :key="n" class="opportunity-card skeleton"></div>
          </div>

          <div v-else-if="!loading && offers.length === 0" class="empty-state">
            No opportunities found. Try a different search.
          </div>

          <div v-else class="cards-container">
            <div
              v-for="offer in offers"
              :key="offer.id"
              class="opportunity-card"
            >
              <div class="card-top-row">
                <span class="card-tag">{{ offer.offer_type }}</span>
                <span class="card-country">{{ offer.country }}</span>
                <button
                  v-if="user"
                  :class="['fav-btn', { saved: favIds.has(offer.id) }]"
                  :title="favIds.has(offer.id) ? 'Remove from favorites' : 'Save to favorites'"
                  :disabled="togglingFav === offer.id"
                  @click.stop="toggleFavorite(offer)"
                >{{ favIds.has(offer.id) ? '★' : '☆' }}</button>
              </div>
              <a :href="offer.link" target="_blank" rel="noopener noreferrer" class="card-link-area">
                <h3 class="card-title">{{ offer.title }}</h3>
                <p class="card-summary">{{ offer.summary }}</p>
              </a>
              <div class="card-footer-row">
                <span class="card-org">{{ offer.organization.name }}</span>
                <span class="card-link-hint">Open ↗</span>
              </div>
            </div>
          </div>

          <div v-if="totalPages > 1" class="pagination">
            <button @click="prevPage" :disabled="page <= 1" class="page-btn">←</button>
            <span class="page-info">{{ page }} / {{ totalPages }}</span>
            <button @click="nextPage" :disabled="page >= totalPages" class="page-btn">→</button>
          </div>
        </main>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
import { api } from '../../services/api.js'
import { useAuth } from '../../composables/useAuth.js'

const props = defineProps({
  shortcuts: Array,
  searchPlaceholder: String,
  targetProfile: String,
})

const { user } = useAuth()
const favIds = ref(new Set())
const togglingFav = ref(null)

async function loadFavIds() {
  if (!user.value) return
  const res = await api.get(`/api/users/${user.value.id}/favorites?page_size=200`)
  if (res.ok) {
    const data = await res.json()
    favIds.value = new Set(data.results.map(f => f.offer.id))
  }
}

async function toggleFavorite(offer) {
  if (!user.value || togglingFav.value) return
  togglingFav.value = offer.id
  try {
    if (favIds.value.has(offer.id)) {
      const res = await api.delete(`/api/users/${user.value.id}/favorites/${offer.id}`)
      if (res.ok) {
        const next = new Set(favIds.value)
        next.delete(offer.id)
        favIds.value = next
      }
    } else {
      const res = await api.post(`/api/users/${user.value.id}/favorites`, { offer_id: offer.id })
      if (res.ok) {
        const next = new Set(favIds.value)
        next.add(offer.id)
        favIds.value = next
      }
    }
  } finally {
    togglingFav.value = null
  }
}

const isSearching = ref(false)
const searchTerm = ref('')
const activeFilter = ref('')

const offers = ref([])
const total = ref(0)
const totalPages = ref(0)
const page = ref(1)
const loading = ref(false)
const fetchError = ref(null)

let debounceTimer = null

function onSearchInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    fetchOffers()
  }, 400)
}

function applyShortcut(item) {
  isSearching.value = true
  searchTerm.value = ''
  activeFilter.value = item
  page.value = 1
  fetchOffers()
}

function toggleFilter(cat) {
  activeFilter.value = activeFilter.value === cat ? '' : cat
  page.value = 1
  fetchOffers()
}

function resetSearch() {
  isSearching.value = false
  searchTerm.value = ''
  activeFilter.value = ''
  page.value = 1
  offers.value = []
}

function prevPage() {
  if (page.value > 1) { page.value--; fetchOffers() }
}

function nextPage() {
  if (page.value < totalPages.value) { page.value++; fetchOffers() }
}

async function fetchOffers() {
  loading.value = true
  fetchError.value = null
  try {
    const params = new URLSearchParams({ page: page.value, page_size: 9, status: 'published' })
    if (searchTerm.value.trim()) params.set('q', searchTerm.value.trim())
    if (activeFilter.value) {
      params.set('offer_type', activeFilter.value)
    } else if (props.targetProfile) {
      params.set('target_profile', props.targetProfile)
    }

    const res = await api.get(`/api/offers?${params}`)
    if (!res.ok) throw new Error('Failed to load offers')
    const data = await res.json()
    offers.value = data.results
    total.value = data.count
    totalPages.value = data.total_pages
  } catch (e) {
    fetchError.value = e.message
  } finally {
    loading.value = false
  }
}

watch(isSearching, (val) => {
  if (val) {
    if (offers.value.length === 0) fetchOffers()
    loadFavIds()
  }
})
</script>

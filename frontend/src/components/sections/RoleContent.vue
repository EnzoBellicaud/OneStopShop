<template>
  <div class="selection-screen">
    <!-- Hero -->
    <section class="page-hero">
      <div class="page-hero-inner">
        <p class="section-eyebrow">Opportunities</p>
        <h1 class="page-title">{{ title || 'What are you looking for?' }}</h1>
        <p class="page-sub">{{ description || 'Search opportunities or browse by category below.' }}</p>
        <div v-if="isSearching" class="hero-actions">
          <button class="btn-ghost" @click="resetSearch">← Browse categories</button>
        </div>
      </div>
    </section>

    <!-- Filter bar -->
    <div class="filter-bar">
      <input
        type="text"
        class="search-input"
        :placeholder="searchPlaceholder || 'Search opportunities...'"
        v-model="searchTerm"
        @focus="isSearching = true"
        @input="onSearchInput"
      />
    </div>

    <!-- Content -->
    <div class="role-content-wrap">

      <!-- Browse: shortcut cards -->
      <div v-if="!isSearching" class="grid-profiles">
        <div
          v-for="item in shortcuts"
          :key="itemValue(item)"
          class="shortcut-card"
          @click="applyShortcut(item)"
        >
          <span class="item-name">{{ itemLabel(item) }}</span>
          <button class="select-btn">Explore</button>
        </div>
      </div>

      <!-- Search results -->
      <div v-else class="results-layout">
        <aside class="side-filters">
          <h3>Filters</h3>

          <div class="filter-group">
            <h4>Category</h4>
            <label v-for="cat in shortcuts" :key="itemValue(cat)" class="checkbox-item">
              <input
                type="checkbox"
                :checked="activeFilter === itemValue(cat)"
                @change="toggleFilter(cat)"
              />
              {{ itemLabel(cat) }}
            </label>
          </div>

          <div class="filter-group">
            <h4>University</h4>
            <label v-for="uni in UNIVERSITIES" :key="uni.value" class="checkbox-item">
              <input
                type="checkbox"
                :checked="activeUniversity === uni.value"
                @change="toggleUniversity(uni.value)"
              />
              {{ uni.label }}
            </label>
          </div>

          <div class="filter-group">
            <h4>Domain</h4>
            <label v-for="dom in visibleDomains" :key="dom" class="checkbox-item">
              <input
                type="checkbox"
                :checked="activeDomainFilter === dom"
                @change="toggleDomainFilter(dom)"
              />
              {{ dom.replace(/_/g, ' ') }}
            </label>
            <button class="show-more-btn" @click="showAllDomains = !showAllDomains">
              {{ showAllDomains ? 'Show less ↑' : `+${DOMAINS.length - DOMAIN_PREVIEW} more` }}
            </button>
          </div>

          <button class="reset-btn" @click="resetSearch">Reset All</button>
        </aside>

        <main class="results-grid">
          <div class="results-controls">
            <div class="results-header">
              <template v-if="loading">Loading…</template>
              <template v-else-if="fetchError">{{ fetchError }}</template>
              <template v-else>{{ total }} result{{ total !== 1 ? 's' : '' }} found</template>
            </div>
            <div class="sort-bar">
              <span class="sort-label">Sort:</span>
              <button
                v-for="opt in SORT_OPTIONS"
                :key="opt.value"
                :class="['sort-btn', { active: sortBy === opt.value }]"
                @click="setSortBy(opt.value)"
              >{{ opt.label }}</button>
              <button class="sort-order-btn" @click="toggleSortOrder" :title="sortOrder === 'asc' ? 'Switch to descending' : 'Switch to ascending'">
                {{ sortOrder === 'asc' ? '↑ Asc' : '↓ Desc' }}
              </button>
            </div>
          </div>

          <div v-if="loading" class="cards-container">
            <div v-for="n in 3" :key="n" class="opportunity-card skeleton"></div>
          </div>

          <div v-else-if="!loading && offers.length === 0" class="empty-state">
            No opportunities found. Try a different search or reset the filters.
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
              <div v-if="offer.domains && offer.domains.length" class="card-domains">
                <span v-for="domain in offer.domains" :key="domain" class="domain-chip">{{ domain }}</span>
              </div>
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
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '../../services/api.js'
import { useAuth } from '../../composables/useAuth.js'

const props = defineProps({
  shortcuts: Array,
  searchPlaceholder: String,
  targetProfile: String,
  title: String,
  description: String,
})

// ── Auth / Favorites ──────────────────────────────────────────────────────────
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

// ── Static filter data ────────────────────────────────────────────────────────
const UNIVERSITIES = [
  { label: 'EUC',        value: 'EUC' },
  { label: 'UNIBZ',      value: 'UNIBZ' },
  { label: 'IPVC',       value: 'IPVC' },
  { label: 'MDU',        value: 'MDU' },
  { label: 'TU Ilmenau', value: 'TU Ilmenau' },
  { label: 'UITM',       value: 'UITM' },
  { label: 'UNMO',       value: 'UNMO' },
  { label: 'UNIVPM',     value: 'UNIVPM' },
  { label: 'UTC',        value: 'UTC' },
]

const DOMAINS = [
  'AI', 'Co_creation_and_testbeds', 'Cybersecurity', 'Digitalisation',
  'Innovation_and_entrepreneurship', 'Mobility', 'Regional_development',
  'Robotics', 'STEAM_education', 'Social_transformation', 'Sustainability',
  'Technology_transfer',
]

const SORT_OPTIONS = [
  { label: 'Name',  value: 'title' },
  { label: 'Date',  value: 'created_at' },
]

const DOMAIN_PREVIEW = 5

// ── Filter / sort state ───────────────────────────────────────────────────────
const isSearching = ref(false)
const searchTerm = ref('')
const activeFilter = ref('')
const activeFilterType = ref('offer_type')
const activeUniversity = ref('')
const activeDomainFilter = ref('')
const sortBy = ref('title')
const sortOrder = ref('asc')
const showAllDomains = ref(false)

const visibleDomains = computed(() =>
  showAllDomains.value ? DOMAINS : DOMAINS.slice(0, DOMAIN_PREVIEW)
)

// ── Results state ─────────────────────────────────────────────────────────────
const offers = ref([])
const total = ref(0)
const totalPages = ref(0)
const page = ref(1)
const loading = ref(false)
const fetchError = ref(null)

// ── Shortcut helpers ──────────────────────────────────────────────────────────
function itemLabel(item) { return typeof item === 'string' ? item : item.label }
function itemValue(item) { return typeof item === 'string' ? item : item.value }
function itemType(item)  { return typeof item === 'object' && item.type ? item.type : 'offer_type' }

// ── Actions ───────────────────────────────────────────────────────────────────
let debounceTimer = null

function onSearchInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { page.value = 1; fetchOffers() }, 400)
}

function applyShortcut(item) {
  isSearching.value = true
  searchTerm.value = ''
  activeFilter.value = itemValue(item)
  activeFilterType.value = itemType(item)
  page.value = 1
  fetchOffers()
}

function toggleFilter(cat) {
  const val = itemValue(cat)
  if (activeFilter.value === val) {
    activeFilter.value = ''
    activeFilterType.value = 'offer_type'
  } else {
    activeFilter.value = val
    activeFilterType.value = itemType(cat)
  }
  page.value = 1
  fetchOffers()
}

function toggleUniversity(val) {
  activeUniversity.value = activeUniversity.value === val ? '' : val
  page.value = 1
  fetchOffers()
}

function toggleDomainFilter(val) {
  activeDomainFilter.value = activeDomainFilter.value === val ? '' : val
  page.value = 1
  fetchOffers()
}

function setSortBy(val) {
  sortBy.value = val
  page.value = 1
  fetchOffers()
}

function toggleSortOrder() {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  page.value = 1
  fetchOffers()
}

function resetSearch() {
  isSearching.value = false
  searchTerm.value = ''
  activeFilter.value = ''
  activeFilterType.value = 'offer_type'
  activeUniversity.value = ''
  activeDomainFilter.value = ''
  sortBy.value = 'title'
  sortOrder.value = 'asc'
  page.value = 1
  offers.value = []
}

function prevPage() { if (page.value > 1) { page.value--; fetchOffers() } }
function nextPage() { if (page.value < totalPages.value) { page.value++; fetchOffers() } }

// ── Fetch ─────────────────────────────────────────────────────────────────────
async function fetchOffers() {
  loading.value = true
  fetchError.value = null
  try {
    const params = new URLSearchParams({ page: page.value, page_size: 9, status: 'published' })

    if (searchTerm.value.trim()) params.set('q', searchTerm.value.trim())

    if (activeFilter.value && activeFilterType.value === 'offer_type') {
      params.set('offer_type', activeFilter.value)
    } else if (props.targetProfile) {
      params.set('target_profile', props.targetProfile)
    }

    const domainVal = activeDomainFilter.value ||
      (activeFilterType.value === 'domain' ? activeFilter.value : '')
    if (domainVal) params.set('domain', domainVal)

    if (activeUniversity.value) params.set('organization', activeUniversity.value)

    params.set('ordering', `${sortOrder.value === 'desc' ? '-' : ''}${sortBy.value}`)

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

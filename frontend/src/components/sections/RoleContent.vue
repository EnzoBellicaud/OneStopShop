<template>
  <div class="selection-screen">
    <!-- Hero -->
    <section class="page-hero">
      <div class="page-hero-inner">
        <p class="section-eyebrow">{{ t('role.eyebrow') }}</p>
        <h1 class="page-title">{{ title || t('role.defaultTitle') }}</h1>
        <p class="page-sub">{{ description || t('role.defaultDescription') }}</p>
        <div v-if="isSearching" class="hero-actions">
          <button class="btn-ghost" @click="resetSearch">{{ t('role.browseCategories') }}</button>
        </div>
      </div>
    </section>

    <!-- Filter bar -->
    <div class="filter-bar">
      <input
        type="text"
        class="search-input"
        :placeholder="searchPlaceholder || t('role.searchPlaceholder')"
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
          v-for="item in validShortcuts"
          :key="itemValue(item)"
          class="shortcut-card"
          @click="applyShortcut(item)"
        >
          <span class="item-name">{{ itemLabel(item) }}</span>
          <button class="select-btn">{{ t('role.explore') }}</button>
        </div>
      </div>

      <!-- Search results -->
      <div v-else class="results-layout">
        <aside class="side-filters">
          <h3>{{ t('role.filters') }}</h3>

          <div class="filter-group">
            <h4>{{ t('role.category') }}</h4>
            <label v-for="cat in validShortcuts" :key="itemValue(cat)" class="checkbox-item">
              <input
                type="checkbox"
                :checked="activeFilter === itemValue(cat)"
                @change="toggleFilter(cat)"
              />
              {{ itemLabel(cat) }}
            </label>
          </div>

          <div class="filter-group">
            <h4>{{ t('role.university') }}</h4>
            <label v-for="uni in universities" :key="uni.value" class="checkbox-item">
              <input
                type="checkbox"
                :checked="activeUniversity === uni.value"
                @change="toggleUniversity(uni.value)"
              />
              {{ uni.label }}
            </label>
          </div>

          <div class="filter-group">
            <h4>{{ t('role.domain') }}</h4>
            <label v-for="dom in visibleDomains" :key="dom" class="checkbox-item">
              <input
                type="checkbox"
                :checked="activeDomainFilter === dom"
                @change="toggleDomainFilter(dom)"
              />
              {{ dom.replace(/_/g, ' ') }}
            </label>
            <button v-if="validDomains.length > DOMAIN_PREVIEW" class="show-more-btn" @click="showAllDomains = !showAllDomains">
              {{ showAllDomains ? t('role.showLess') : t('role.showMore', { count: validDomains.length - DOMAIN_PREVIEW }) }}
            </button>
          </div>

          <button class="reset-btn" @click="resetSearch">{{ t('role.resetAll') }}</button>
        </aside>

        <main class="results-grid">
          <div class="results-controls">
            <div class="results-header">
              <template v-if="loading">{{ t('role.loading') }}</template>
              <template v-else-if="fetchError">{{ fetchError }}</template>
              <template v-else>{{ total }} {{ t('role.result', total) }}</template>
            </div>
            <div class="sort-bar">
              <span class="sort-label">{{ t('role.sort') }}</span>
              <button
                v-for="opt in SORT_OPTIONS"
                :key="opt.value"
                :class="['sort-btn', { active: sortBy === opt.value }]"
                @click="setSortBy(opt.value)"
              >{{ t(opt.labelKey) }}</button>
              <button class="sort-order-btn" @click="toggleSortOrder" :title="sortOrder === 'asc' ? t('role.switchToDesc') : t('role.switchToAsc')">
                {{ sortOrder === 'asc' ? t('role.asc') : t('role.desc') }}
              </button>
            </div>
          </div>

          <div v-if="loading" class="cards-container">
            <div v-for="n in 3" :key="n" class="opportunity-card skeleton"></div>
          </div>

          <div v-else-if="!loading && offers.length === 0" class="empty-state">
            {{ t('role.empty') }}
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
                  :title="favIds.has(offer.id) ? t('role.removeFav') : t('role.saveFav')"
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
                <span class="card-link-hint">{{ t('role.open') }}</span>
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
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../../services/api.js'
import { useAuth } from '../../composables/useAuth.js'

const { t, locale } = useI18n()

const props = defineProps({
  shortcuts: Array,
  searchPlaceholder: String,
  targetProfile: String,
  title: String,
  description: String,
  skipValidation: { type: Boolean, default: false },
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

// ── Dynamic university list ───────────────────────────────────────────────────
const universities = ref([])

async function loadUniversities() {
  const res = await api.get('/api/lookups/organizations?page_size=50')
  if (res.ok) {
    const data = await res.json()
    universities.value = data.results.map(org => ({ label: org.name, value: org.name }))
  }
}

// ── Valid shortcuts (hide zero-count categories) ──────────────────────────────
const validShortcuts = ref(props.shortcuts ?? [])

async function validateShortcuts() {
  if (props.skipValidation || !props.shortcuts?.length) return
  const checks = props.shortcuts.map(async (item) => {
    const type = itemType(item)
    const val  = itemValue(item)
    const params = new URLSearchParams({ page_size: 1, status: 'published' })
    if (props.targetProfile) params.set('target_profile', props.targetProfile)
    if (type === 'offer_type') params.set('offer_type', val)
    else if (type === 'domain') params.set('domain', val)
    try {
      const res = await api.get(`/api/offers?${params}`)
      if (!res.ok) return { item, count: 0 }
      const data = await res.json()
      return { item, count: data.count }
    } catch {
      return { item, count: 0 }
    }
  })
  const results = await Promise.all(checks)
  validShortcuts.value = results.filter(r => r.count > 0).map(r => r.item)
}

const ALL_DOMAINS = [
  'AI', 'Co_creation_and_testbeds', 'Cybersecurity', 'Digitalisation',
  'Innovation_and_entrepreneurship', 'Mobility', 'Regional_development',
  'Robotics', 'STEAM_education', 'Social_transformation', 'Sustainability',
  'Technology_transfer',
]

const validDomains = ref([])

async function validateDomains() {
  const checks = ALL_DOMAINS.map(async (domain) => {
    const params = new URLSearchParams({ page_size: 1, status: 'published', domain })
    if (props.targetProfile) params.set('target_profile', props.targetProfile)
    try {
      const res = await api.get(`/api/offers?${params}`)
      if (!res.ok) return { domain, count: 0 }
      const data = await res.json()
      return { domain, count: data.count }
    } catch {
      return { domain, count: 0 }
    }
  })
  const results = await Promise.all(checks)
  validDomains.value = results.filter(r => r.count > 0).map(r => r.domain)
}

const SORT_OPTIONS = [
  { labelKey: 'role.sortName', value: 'title' },
  { labelKey: 'role.sortDate', value: 'created_at' },
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
  showAllDomains.value ? validDomains.value : validDomains.value.slice(0, DOMAIN_PREVIEW)
)

// ── Results state ─────────────────────────────────────────────────────────────
const offers = ref([])
const total = ref(0)
const totalPages = ref(0)
const page = ref(1)
const loading = ref(false)
const fetchError = ref(null)

// ── Shortcut helpers ──────────────────────────────────────────────────────────
function itemLabel(item) {
  if (typeof item === 'string') return item
  return item.labelKey ? t(item.labelKey) : item.label
}
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
    params.set('lang', locale.value)

    const res = await api.get(`/api/offers?${params}`)
    if (!res.ok) throw new Error('load-failed')
    const data = await res.json()
    offers.value = data.results
    total.value = data.count
    totalPages.value = data.total_pages
  } catch (e) {
    fetchError.value = t('role.loadError')
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

// Re-fetch so cards reflect the newly selected language's cached translations.
watch(locale, () => {
  if (isSearching.value) fetchOffers()
})

onMounted(() => { loadUniversities(); validateShortcuts(); validateDomains() })
</script>

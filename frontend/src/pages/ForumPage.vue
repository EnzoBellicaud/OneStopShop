<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import { useAuth } from '../composables/useAuth'
import { useForum } from '../composables/useForum'

const router = useRouter()
const { isLoggedIn } = useAuth()
const { fetchQuestions, fetchOfferTypes } = useForum()

const searchQuery = ref('')
const selectedOfferType = ref('')
const onlyMine = ref(false)
const offerTypes = ref([])
const questions = ref([])
const loading = ref(false)
const error = ref('')

const page = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)
const totalPages = ref(0)

let searchDebounce = null

const hasResults = computed(() => questions.value.length > 0)

async function loadOfferTypes() {
  try {
    offerTypes.value = await fetchOfferTypes()
  } catch (err) {
    offerTypes.value = []
  }
}

async function loadQuestions() {
  loading.value = true
  error.value = ''
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (searchQuery.value.trim()) params.q = searchQuery.value.trim()
    if (selectedOfferType.value) params.offer_type = selectedOfferType.value
    if (onlyMine.value && isLoggedIn.value) params.mine = 'true'

    const data = await fetchQuestions(params)
    questions.value = data.results || []
    totalCount.value = data.count || 0
    totalPages.value = data.total_pages || 0
  } catch (err) {
    error.value = err.message || 'Failed to load questions.'
    questions.value = []
  } finally {
    loading.value = false
  }
}

function resetAndLoad() {
  page.value = 1
  loadQuestions()
}

watch(searchQuery, () => {
  if (searchDebounce) clearTimeout(searchDebounce)
  searchDebounce = setTimeout(resetAndLoad, 300)
})

watch(selectedOfferType, resetAndLoad)
watch(onlyMine, resetAndLoad)
watch(page, loadQuestions)

function toggleMine() {
  if (!isLoggedIn.value) {
    router.push({ name: 'Auth', query: { redirect: '/forum' } })
    return
  }
  onlyMine.value = !onlyMine.value
}

function goToNew() {
  if (!isLoggedIn.value) {
    router.push({ name: 'Auth', query: { redirect: '/forum/new' } })
    return
  }
  router.push({ name: 'NewQuestion' })
}

function previewBody(text) {
  if (!text) return ''
  const trimmed = text.trim()
  return trimmed.length > 180 ? `${trimmed.slice(0, 180)}…` : trimmed
}

function formatDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
    })
  } catch {
    return iso
  }
}

function offerTypeClass(name) {
  switch (name) {
    case 'thesis': return 'tag-thesis'
    case 'internship': return 'tag-intern'
    case 'training': return 'tag-course'
    default: return 'tag-job'
  }
}

onMounted(() => {
  loadOfferTypes()
  loadQuestions()
})
</script>

<template>
  <AppHeader />
  <main>
    <section class="page-hero">
      <div class="page-hero-inner">
        <p class="section-eyebrow">Community</p>
        <h1 class="page-title">Forum</h1>
        <p class="page-sub">
          Ask questions, share answers, and learn from the community across our partner universities.
        </p>
        <div class="hero-actions">
          <button class="btn-primary" @click="goToNew">Ask a question</button>
        </div>
      </div>
    </section>

    <div class="filter-bar">
      <input
        v-model="searchQuery"
        class="search-input"
        type="text"
        placeholder="Search questions..."
      />
      <select v-model="selectedOfferType" class="filter-select">
        <option value="">All offer types</option>
        <option v-for="t in offerTypes" :key="t.id" :value="t.name">{{ t.name }}</option>
      </select>
      <button
        class="filter-chip"
        :class="{ active: onlyMine }"
        @click="toggleMine"
      >My questions</button>
    </div>

    <div class="forum-content">
      <p v-if="error" class="error-message">{{ error }}</p>
      <p v-else-if="loading && !hasResults" class="info-message">Loading…</p>
      <p v-else-if="!hasResults" class="info-message">No questions found.</p>

      <div class="question-list">
        <RouterLink
          v-for="q in questions"
          :key="q.id"
          :to="{ name: 'QuestionDetail', params: { id: q.id } }"
          class="question-card"
        >
          <div class="question-card-top">
            <span
              v-if="q.offer_type"
              class="type-tag"
              :class="offerTypeClass(q.offer_type)"
            >{{ q.offer_type }}</span>
            <span class="answer-badge">{{ q.answer_count }} {{ q.answer_count === 1 ? 'answer' : 'answers' }}</span>
          </div>
          <h3 class="question-title">{{ q.title }}</h3>
          <p class="question-body">{{ previewBody(q.body) }}</p>
          <div class="question-meta">
            <span>by {{ q.author.username }}</span>
            <span>•</span>
            <span>{{ formatDate(q.created_at) }}</span>
          </div>
        </RouterLink>
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button
          class="btn-ghost pagination-btn"
          :disabled="page <= 1 || loading"
          @click="page = page - 1"
        >← Prev</button>
        <span class="pagination-info">Page {{ page }} of {{ totalPages }} · {{ totalCount }} total</span>
        <button
          class="btn-ghost pagination-btn"
          :disabled="page >= totalPages || loading"
          @click="page = page + 1"
        >Next →</button>
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
  max-width: 540px;
  margin-bottom: 1.5rem;
}
.hero-actions {
  display: flex;
  gap: 12px;
}
.forum-content {
  max-width: 880px;
  margin: 0 auto;
  padding: 0 3rem 4rem;
}
.error-message {
  background: #fde8e8;
  color: #9a1a1a;
  border-radius: var(--r);
  padding: 10px 14px;
  font-size: 14px;
}
.info-message {
  color: var(--ink-soft);
  font-size: 14px;
  padding: 1rem 0;
}
.question-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.question-card {
  display: block;
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.25rem 1.5rem;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s, transform 0.2s;
}
.question-card:hover {
  border-color: #bbb;
  transform: translateY(-1px);
}
.question-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.answer-badge {
  font-size: 12px;
  color: var(--ink-soft);
  background: var(--surface);
  border-radius: 999px;
  padding: 3px 10px;
}
.question-title {
  font-family: 'DM Serif Display', serif;
  font-size: 20px;
  color: var(--ink);
  margin: 0 0 0.5rem;
}
.question-body {
  font-size: 14px;
  color: var(--ink-soft);
  line-height: 1.55;
  margin: 0 0 0.75rem;
}
.question-meta {
  font-size: 12px;
  color: var(--ink-faint);
  display: flex;
  gap: 6px;
}
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 2rem;
}
.pagination-btn {
  padding: 8px 14px;
  font-size: 13px;
}
.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.pagination-info {
  font-size: 13px;
  color: var(--ink-soft);
}
</style>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import { useAuth } from '../composables/useAuth.js'
import { useForum } from '../composables/useForum.js'

const route = useRoute()
const router = useRouter()
const { user, isLoggedIn } = useAuth()
const {
  fetchQuestion,
  updateQuestion,
  deleteQuestion,
  createAnswer,
  updateAnswer,
  deleteAnswer,
} = useForum()

const question = ref(null)
const answers = ref([])
const loading = ref(true)
const error = ref('')

const editingQuestion = ref(false)
const questionDraft = ref({ title: '', body: '' })
const questionError = ref('')

const answerDraft = ref('')
const answerError = ref('')
const submittingAnswer = ref(false)

const editingAnswerId = ref(null)
const answerEditDraft = ref('')

const currentUserId = computed(() => user.value?.id || null)
const canModifyQuestion = computed(() =>
  question.value && currentUserId.value && question.value.author.id === currentUserId.value
)

function canModifyAnswer(answer) {
  return currentUserId.value && answer.author.id === currentUserId.value
}

function offerTypeClass(name) {
  switch (name) {
    case 'thesis': return 'tag-thesis'
    case 'internship': return 'tag-intern'
    case 'training': return 'tag-course'
    default: return 'tag-job'
  }
}

function formatDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

async function loadQuestion() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchQuestion(route.params.id)
    question.value = data
    answers.value = data.answers || []
  } catch (err) {
    error.value = err.message || 'Failed to load question.'
    question.value = null
    answers.value = []
  } finally {
    loading.value = false
  }
}

function startEditQuestion() {
  if (!question.value) return
  questionDraft.value = { title: question.value.title, body: question.value.body }
  questionError.value = ''
  editingQuestion.value = true
}

function cancelEditQuestion() {
  editingQuestion.value = false
  questionError.value = ''
}

async function saveQuestion() {
  questionError.value = ''
  const title = questionDraft.value.title.trim()
  const body = questionDraft.value.body.trim()
  if (title.length < 5) {
    questionError.value = 'Title must be at least 5 characters.'
    return
  }
  if (body.length < 10) {
    questionError.value = 'Body must be at least 10 characters.'
    return
  }
  try {
    const updated = await updateQuestion(question.value.id, { title, body })
    question.value = { ...question.value, ...updated }
    editingQuestion.value = false
  } catch (err) {
    questionError.value = err.message || 'Failed to update question.'
  }
}

async function removeQuestion() {
  if (!confirm('Delete this question and all of its answers?')) return
  try {
    await deleteQuestion(question.value.id)
    router.push({ name: 'Forum' })
  } catch (err) {
    error.value = err.message || 'Failed to delete question.'
  }
}

async function submitAnswer() {
  answerError.value = ''
  const body = answerDraft.value.trim()
  if (body.length < 10) {
    answerError.value = 'Answer must be at least 10 characters.'
    return
  }
  submittingAnswer.value = true
  try {
    const created = await createAnswer(question.value.id, body)
    answers.value = [...answers.value, created]
    answerDraft.value = ''
    if (question.value) {
      question.value.answer_count = (question.value.answer_count || 0) + 1
    }
  } catch (err) {
    answerError.value = err.message || 'Failed to post answer.'
  } finally {
    submittingAnswer.value = false
  }
}

function startEditAnswer(answer) {
  editingAnswerId.value = answer.id
  answerEditDraft.value = answer.body
}

function cancelEditAnswer() {
  editingAnswerId.value = null
  answerEditDraft.value = ''
}

async function saveAnswer(answer) {
  const body = answerEditDraft.value.trim()
  if (body.length < 10) {
    answerError.value = 'Answer must be at least 10 characters.'
    return
  }
  try {
    const updated = await updateAnswer(answer.id, body)
    answers.value = answers.value.map((a) => (a.id === answer.id ? { ...a, ...updated } : a))
    editingAnswerId.value = null
    answerEditDraft.value = ''
  } catch (err) {
    answerError.value = err.message || 'Failed to update answer.'
  }
}

async function removeAnswer(answer) {
  if (!confirm('Delete this answer?')) return
  try {
    await deleteAnswer(answer.id)
    answers.value = answers.value.filter((a) => a.id !== answer.id)
    if (question.value) {
      question.value.answer_count = Math.max(0, (question.value.answer_count || 1) - 1)
    }
  } catch (err) {
    answerError.value = err.message || 'Failed to delete answer.'
  }
}

watch(() => route.params.id, (id) => {
  if (id) loadQuestion()
})

onMounted(loadQuestion)
</script>

<template>
  <AppHeader />
  <main>
    <div class="detail-wrap">
      <button class="back-btn" @click="router.back()">← Back</button>

      <p v-if="loading" class="forum-info">Loading…</p>
      <p v-else-if="error && !question" class="forum-error">{{ error }}</p>

      <div v-if="question && !loading" class="detail-card">
        <div class="card-top">
          <span
            v-if="question.offer_type"
            class="type-tag"
            :class="offerTypeClass(question.offer_type)"
          >{{ question.offer_type }}</span>
          <span class="answer-badge">{{ question.answer_count }} {{ question.answer_count === 1 ? 'answer' : 'answers' }}</span>
        </div>

        <template v-if="!editingQuestion">
          <h1 class="detail-title">{{ question.title }}</h1>
          <p class="detail-meta">
            asked by <strong>{{ question.author.username }}</strong> · {{ formatDate(question.created_at) }}
          </p>
          <p class="detail-desc">{{ question.body }}</p>
          <div v-if="canModifyQuestion" class="detail-actions">
            <button class="btn-ghost" @click="startEditQuestion">Edit</button>
            <button class="btn-ghost btn-danger" @click="removeQuestion">Delete</button>
          </div>
        </template>

        <template v-else>
          <div class="dform-group">
            <label>Title</label>
            <input v-model="questionDraft.title" type="text" class="dtext-input" />
          </div>
          <div class="dform-group">
            <label>Body</label>
            <textarea v-model="questionDraft.body" rows="6" class="dtext-area"></textarea>
          </div>
          <p v-if="questionError" class="forum-error">{{ questionError }}</p>
          <div class="detail-actions">
            <button class="btn-primary" @click="saveQuestion">Save</button>
            <button class="btn-ghost" @click="cancelEditQuestion">Cancel</button>
          </div>
        </template>
      </div>

      <section v-if="question" class="answers-section">
        <h2 class="answers-title">
          {{ answers.length }} {{ answers.length === 1 ? 'Answer' : 'Answers' }}
        </h2>

        <p v-if="answerError" class="forum-error">{{ answerError }}</p>

        <div class="answer-list">
          <div v-for="answer in answers" :key="answer.id" class="answer-card">
            <template v-if="editingAnswerId !== answer.id">
              <p class="answer-body">{{ answer.body }}</p>
              <div class="answer-footer">
                <span class="answer-meta">
                  {{ answer.author.username }} · {{ formatDate(answer.created_at) }}
                </span>
                <div v-if="canModifyAnswer(answer)" class="answer-actions">
                  <button class="link-btn" @click="startEditAnswer(answer)">Edit</button>
                  <button class="link-btn link-btn-danger" @click="removeAnswer(answer)">Delete</button>
                </div>
              </div>
            </template>
            <template v-else>
              <textarea v-model="answerEditDraft" rows="4" class="dtext-area"></textarea>
              <div class="answer-footer">
                <span></span>
                <div class="answer-actions">
                  <button class="btn-primary btn-sm" @click="saveAnswer(answer)">Save</button>
                  <button class="btn-ghost btn-sm" @click="cancelEditAnswer">Cancel</button>
                </div>
              </div>
            </template>
          </div>
        </div>

        <div class="answer-compose">
          <h3 class="compose-title">Post an answer</h3>
          <template v-if="isLoggedIn">
            <textarea
              v-model="answerDraft"
              rows="4"
              class="dtext-area"
              placeholder="Share your answer..."
            ></textarea>
            <button
              class="btn-primary"
              :disabled="submittingAnswer || answerDraft.trim().length < 10"
              @click="submitAnswer"
            >{{ submittingAnswer ? 'Posting…' : 'Post answer' }}</button>
          </template>
          <p v-else class="forum-info">
            <RouterLink :to="{ name: 'login', query: { redirect: route.fullPath } }">Log in</RouterLink>
            to post an answer.
          </p>
        </div>
      </section>
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
  padding: 2rem;
  margin-bottom: 2rem;
}
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.answer-badge {
  font-size: 12px;
  color: var(--ink-soft);
  background: var(--surface);
  border-radius: 999px;
  padding: 3px 10px;
}
.detail-title {
  font-family: 'DM Serif Display', serif;
  font-size: 26px;
  letter-spacing: -0.4px;
  color: var(--ink);
  margin: 0.75rem 0 0.5rem;
}
.detail-meta {
  font-size: 13px;
  color: var(--ink-faint);
  margin-bottom: 1.25rem;
}
.detail-desc {
  font-size: 15px;
  color: var(--ink);
  line-height: 1.7;
  margin-bottom: 1.5rem;
  white-space: pre-wrap;
}
.detail-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 1rem;
}
.btn-danger { color: #9a1a1a; }
.btn-sm { padding: 6px 12px; font-size: 13px; }

.dform-group { margin-bottom: 1rem; }
.dform-group label {
  display: block;
  font-size: 13px;
  color: var(--ink-soft);
  margin-bottom: 6px;
}
.dtext-input,
.dtext-area {
  width: 100%;
  font-family: inherit;
  font-size: 14px;
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 10px 12px;
  background: var(--white);
  color: var(--ink);
  box-sizing: border-box;
}
.dtext-area { resize: vertical; line-height: 1.5; }

.answers-section {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 2rem;
}
.answers-title {
  font-family: 'DM Serif Display', serif;
  font-size: 22px;
  color: var(--ink);
  margin: 0 0 1rem;
}
.answer-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 2rem;
}
.answer-card {
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 1rem 1.25rem;
}
.answer-body {
  font-size: 14px;
  color: var(--ink);
  line-height: 1.65;
  white-space: pre-wrap;
  margin: 0 0 0.75rem;
}
.answer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.answer-meta { font-size: 12px; color: var(--ink-faint); }
.answer-actions { display: flex; gap: 8px; }
.link-btn {
  background: none;
  border: none;
  color: var(--ink-soft);
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}
.link-btn:hover { color: var(--ink); text-decoration: underline; }
.link-btn-danger { color: #9a1a1a; }

.answer-compose {
  border-top: 1px solid var(--border);
  padding-top: 1.5rem;
}
.compose-title {
  font-family: 'DM Serif Display', serif;
  font-size: 18px;
  color: var(--ink);
  margin: 0 0 0.75rem;
}
.answer-compose .dtext-area { margin-bottom: 0.75rem; }

.forum-error {
  background: #fde8e8;
  color: #9a1a1a;
  border-radius: var(--r);
  padding: 10px 14px;
  font-size: 14px;
  margin-bottom: 1rem;
}
.forum-info {
  color: var(--ink-soft);
  font-size: 14px;
  padding: 0.5rem 0;
}
</style>

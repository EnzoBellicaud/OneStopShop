<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import { useForum } from '../composables/useForum'

const router = useRouter()
const { createQuestion, fetchOfferTypes } = useForum()

const form = ref({
  title: '',
  body: '',
  offer_type_id: '',
})
const offerTypes = ref([])
const formError = ref('')
const submitting = ref(false)

async function loadOfferTypes() {
  try {
    offerTypes.value = await fetchOfferTypes()
  } catch (err) {
    offerTypes.value = []
  }
}

async function handleSubmit() {
  formError.value = ''
  const title = form.value.title.trim()
  const body = form.value.body.trim()

  if (title.length < 5) {
    formError.value = 'Title must be at least 5 characters.'
    return
  }
  if (title.length > 255) {
    formError.value = 'Title must be at most 255 characters.'
    return
  }
  if (body.length < 10) {
    formError.value = 'Body must be at least 10 characters.'
    return
  }

  submitting.value = true
  try {
    const payload = { title, body }
    if (form.value.offer_type_id) payload.offer_type_id = form.value.offer_type_id
    const created = await createQuestion(payload)
    router.push({ name: 'QuestionDetail', params: { id: created.id } })
  } catch (err) {
    formError.value = err.message || 'Failed to create question.'
  } finally {
    submitting.value = false
  }
}

onMounted(loadOfferTypes)
</script>

<template>
  <AppHeader />
  <main>
    <div class="form-wrap">
      <button class="back-btn" @click="router.back()">← Back</button>
      <h1 class="page-title">Ask a question</h1>
      <p class="page-sub">Share what you need help with — the community can answer below.</p>

      <form class="question-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="title">Title</label>
          <input
            id="title"
            v-model="form.title"
            type="text"
            class="text-input"
            placeholder="What is your question?"
            maxlength="255"
            required
          />
        </div>

        <div class="form-group">
          <label for="body">Details</label>
          <textarea
            id="body"
            v-model="form.body"
            rows="8"
            class="text-area"
            placeholder="Provide more context, what you have tried, and what you are looking for..."
            required
          ></textarea>
        </div>

        <div class="form-group">
          <label for="offer_type">Related offer type (optional)</label>
          <select id="offer_type" v-model="form.offer_type_id" class="text-input">
            <option value="">— None —</option>
            <option v-for="t in offerTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
        </div>

        <p v-if="formError" class="error-message">{{ formError }}</p>

        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="submitting">
            {{ submitting ? 'Posting…' : 'Post question' }}
          </button>
          <button type="button" class="btn-ghost" @click="router.back()">Cancel</button>
        </div>
      </form>
    </div>
  </main>
  <AppFooter />
</template>

<style scoped>
.form-wrap {
  max-width: 720px;
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
.page-title {
  font-family: 'DM Serif Display', serif;
  font-size: 32px;
  letter-spacing: -0.4px;
  color: var(--ink);
  margin: 0 0 0.5rem;
}
.page-sub {
  font-size: 14px;
  color: var(--ink-soft);
  margin: 0 0 2rem;
}
.question-form {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 2rem;
}
.form-group {
  margin-bottom: 1.25rem;
}
.form-group label {
  display: block;
  font-size: 13px;
  color: var(--ink-soft);
  margin-bottom: 6px;
}
.text-input,
.text-area {
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
.text-area {
  resize: vertical;
  line-height: 1.5;
}
.form-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 1rem;
}
.error-message {
  background: #fde8e8;
  color: #9a1a1a;
  border-radius: var(--r);
  padding: 10px 14px;
  font-size: 14px;
  margin-bottom: 1rem;
}
</style>

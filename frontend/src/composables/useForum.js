import { apiFetch } from '../api/client'

function buildQuery(params) {
  const usp = new URLSearchParams()
  for (const [key, value] of Object.entries(params || {})) {
    if (value === undefined || value === null || value === '') continue
    usp.append(key, String(value))
  }
  const qs = usp.toString()
  return qs ? `?${qs}` : ''
}

async function parseOrThrow(res, fallback) {
  let data = null
  try {
    if (res.status !== 204) data = await res.json()
  } catch {
    data = null
  }
  if (!res.ok) {
    const message = (data && (data.detail || data.message)) || fallback
    throw new Error(message)
  }
  return data
}

export function useForum() {
  async function fetchQuestions(params = {}) {
    const res = await apiFetch(`/api/forum/questions${buildQuery(params)}`, { method: 'GET' })
    return parseOrThrow(res, 'Failed to load questions')
  }

  async function fetchQuestion(id) {
    const res = await apiFetch(`/api/forum/questions/${id}`, { method: 'GET' })
    return parseOrThrow(res, 'Failed to load question')
  }

  async function createQuestion(payload) {
    const res = await apiFetch('/api/forum/questions', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    return parseOrThrow(res, 'Failed to create question')
  }

  async function updateQuestion(id, payload) {
    const res = await apiFetch(`/api/forum/questions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
    return parseOrThrow(res, 'Failed to update question')
  }

  async function deleteQuestion(id) {
    const res = await apiFetch(`/api/forum/questions/${id}`, { method: 'DELETE' })
    await parseOrThrow(res, 'Failed to delete question')
  }

  async function createAnswer(questionId, body) {
    const res = await apiFetch(`/api/forum/questions/${questionId}/answers`, {
      method: 'POST',
      body: JSON.stringify({ body }),
    })
    return parseOrThrow(res, 'Failed to post answer')
  }

  async function updateAnswer(id, body) {
    const res = await apiFetch(`/api/forum/answers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ body }),
    })
    return parseOrThrow(res, 'Failed to update answer')
  }

  async function deleteAnswer(id) {
    const res = await apiFetch(`/api/forum/answers/${id}`, { method: 'DELETE' })
    await parseOrThrow(res, 'Failed to delete answer')
  }

  async function fetchOfferTypes() {
    const res = await apiFetch('/api/lookups/offer-types', { method: 'GET' })
    const data = await parseOrThrow(res, 'Failed to load offer types')
    return data.results || []
  }

  return {
    fetchQuestions,
    fetchQuestion,
    createQuestion,
    updateQuestion,
    deleteQuestion,
    createAnswer,
    updateAnswer,
    deleteAnswer,
    fetchOfferTypes,
  }
}

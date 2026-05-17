import { api } from '../services/api.js'

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
    const res = await api.get(`/api/forum/questions${buildQuery(params)}`)
    return parseOrThrow(res, 'Failed to load questions')
  }

  async function fetchQuestion(id) {
    const res = await api.get(`/api/forum/questions/${id}`)
    return parseOrThrow(res, 'Failed to load question')
  }

  async function createQuestion(payload) {
    const res = await api.post('/api/forum/questions', payload)
    return parseOrThrow(res, 'Failed to create question')
  }

  async function updateQuestion(id, payload) {
    const res = await api.patch(`/api/forum/questions/${id}`, payload)
    return parseOrThrow(res, 'Failed to update question')
  }

  async function deleteQuestion(id) {
    const res = await api.delete(`/api/forum/questions/${id}`)
    await parseOrThrow(res, 'Failed to delete question')
  }

  async function createAnswer(questionId, body) {
    const res = await api.post(`/api/forum/questions/${questionId}/answers`, { body })
    return parseOrThrow(res, 'Failed to post answer')
  }

  async function updateAnswer(id, body) {
    const res = await api.patch(`/api/forum/answers/${id}`, { body })
    return parseOrThrow(res, 'Failed to update answer')
  }

  async function deleteAnswer(id) {
    const res = await api.delete(`/api/forum/answers/${id}`)
    await parseOrThrow(res, 'Failed to delete answer')
  }

  async function fetchOfferTypes() {
    const res = await api.get('/api/lookups/offer-types')
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

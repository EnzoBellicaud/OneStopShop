import { ref, computed } from 'vue'
import { apiFetch, clearAuth } from '../api/client'
import { useRouter } from 'vue-router'

function safeParseUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    localStorage.removeItem('user')
    return null
  }
}

// Module-level singletons — shared across all useAuth() callers
const user = ref(safeParseUser())
const accessToken = ref(localStorage.getItem('access_token') || null)

export function useAuth() {
  const router = useRouter()
  const isLoggedIn = computed(() => !!accessToken.value)

  function setSession(data) {
    localStorage.setItem('access_token', data.tokens.access_token)
    localStorage.setItem('refresh_token', data.tokens.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    accessToken.value = data.tokens.access_token
    user.value = data.user
  }

  async function login(username, password) {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Login failed')
    setSession(data)
  }

  async function register(payload) {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Registration failed')
    setSession(data)
  }

  async function logout() {
    await apiFetch('/api/auth/logout', { method: 'POST' }).catch(() => {})
    clearAuth()
    accessToken.value = null
    user.value = null
    router.push('/auth')
  }

  return { user, isLoggedIn, login, register, logout }
}

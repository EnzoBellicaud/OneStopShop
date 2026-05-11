import { ref, readonly } from 'vue'
import { api } from '../services/api.js'

const _user = ref(JSON.parse(localStorage.getItem('user') ?? 'null'))

window.addEventListener('auth:logout', () => { _user.value = null })

function _persist(data) {
  localStorage.setItem('access_token', data.tokens.access_token)
  localStorage.setItem('refresh_token', data.tokens.refresh_token)
  localStorage.setItem('user', JSON.stringify(data.user))
  _user.value = data.user
}

export function useAuth() {
  const loading = ref(false)
  const error = ref(null)

  async function login(username, password) {
    loading.value = true
    error.value = null
    try {
      const res = await api.post('/api/auth/login', { username, password })
      const data = await res.json()
      if (!res.ok) { error.value = data.detail ?? 'Login failed'; return false }
      _persist(data)
      return true
    } catch {
      error.value = 'Network error — is the backend running?'
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(username, email, password, profile) {
    loading.value = true
    error.value = null
    try {
      const res = await api.post('/api/auth/register', { username, email, password, profile })
      const data = await res.json()
      if (!res.ok) { error.value = data.detail ?? 'Registration failed'; return false }
      _persist(data)
      return true
    } catch {
      error.value = 'Network error — is the backend running?'
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    _user.value = null
  }

  return {
    user: readonly(_user),
    loading: readonly(loading),
    error,
    login,
    register,
    logout,
    isLoggedIn: () => !!localStorage.getItem('access_token'),
  }
}

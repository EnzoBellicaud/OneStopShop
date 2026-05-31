import { ref, readonly, computed } from 'vue'
import { api } from '../services/api.js'

const _user = ref(JSON.parse(localStorage.getItem('user') ?? 'null'))
const _token = ref(localStorage.getItem('access_token') ?? null)
const _isLoggedIn = computed(() => !!_user.value)

window.addEventListener('auth:logout', () => { _user.value = null; _token.value = null })
window.addEventListener('auth:login', (e) => { _user.value = e.detail })

function _persist(data) {
  localStorage.setItem('access_token', data.tokens.access_token)
  localStorage.setItem('refresh_token', data.tokens.refresh_token)
  localStorage.setItem('user', JSON.stringify(data.user))
  _user.value = data.user
  _token.value = data.tokens.access_token
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
      if (res.status === 403) {
        if (data.error === 'pending_approval') {
          error.value = 'Your account is pending admin approval.'
        } else if (data.error === 'account_rejected') {
          error.value = 'Your account registration was rejected.'
        } else if (data.error === 'inactive') {
          error.value = 'Your account has been deactivated.'
        } else {
          error.value = data.detail ?? 'Login failed'
        }
        return false
      }
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

  async function register(username, email, password, profile, extraFields = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await api.post('/api/auth/register', { username, email, password, profile, ...extraFields })
      const data = await res.json()
      if (!res.ok) {
        error.value = data.detail ?? data.error ?? 'Registration failed'
        return false
      }
      if (data.status === 'pending_approval') {
        return { pending: true, user: data.user }
      }
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
    _token.value = null
  }

  return {
    user: readonly(_user),
    token: readonly(_token),
    loading: readonly(loading),
    error,
    login,
    register,
    logout,
    isLoggedIn: _isLoggedIn,
  }
}

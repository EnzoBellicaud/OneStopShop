const BASE_URL = import.meta.env.VITE_API_BASE_URL

let refreshPromise = null

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem('access_token')
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (res.status === 401) {
    const refreshed = await tryRefresh()
    if (!refreshed) {
      clearAuth()
      window.location.href = '/auth'
      return res
    }
    headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`
    res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  }

  return res
}

async function tryRefresh() {
  if (refreshPromise) return refreshPromise
  refreshPromise = _doRefresh().finally(() => { refreshPromise = null })
  return refreshPromise
}

async function _doRefresh() {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return false
  try {
    const res = await fetch(`${BASE_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!res.ok) return false
    const data = await res.json()
    localStorage.setItem('access_token', data.tokens.access_token)
    localStorage.setItem('refresh_token', data.tokens.refresh_token)
    return true
  } catch {
    return false
  }
}

function clearAuth() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
}

export { apiFetch, clearAuth }

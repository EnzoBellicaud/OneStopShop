const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

function getToken() {
  return localStorage.getItem('access_token')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers ?? {}),
  }
  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  if (res.status === 401) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    window.dispatchEvent(new Event('auth:logout'))
  }
  return res
}

export const api = {
  get:    (path)       => request(path),
  post:   (path, body) => request(path, { method: 'POST',  body: JSON.stringify(body) }),
  patch:  (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (path)       => request(path, { method: 'DELETE' }),
  upload: (path, formData) => {
    const token = getToken()
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    return fetch(`${BASE}${path}`, { method: 'POST', body: formData, headers })
  },
}

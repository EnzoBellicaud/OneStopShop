
<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { api } from './services/api.js'

onMounted(async () => {
  const params = new URLSearchParams(window.location.search)
  const ssoToken = params.get('sso_token')
  if (!ssoToken) return
  // Always override stale session — new SSO token takes precedence
  window.dispatchEvent(new Event('auth:logout'))
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
  localStorage.setItem('access_token', ssoToken)
  try {
    const res = await api.get('/api/auth/me')
    if (res.ok) {
      const data = await res.json()
      const user = data.user ?? data
      localStorage.setItem('user', JSON.stringify(user))
      window.dispatchEvent(new CustomEvent('auth:login', { detail: user }))
    } else {
      localStorage.removeItem('access_token')
    }
  } catch {
    localStorage.removeItem('access_token')
  }
  window.history.replaceState({}, '', window.location.pathname + window.location.hash)
})
</script>

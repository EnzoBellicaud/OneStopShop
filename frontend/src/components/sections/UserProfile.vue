<template>
  <div>
    <AppHeader />

    <div v-if="!user" class="pf-empty-page">
      Please <router-link to="/login">log in</router-link> to view your profile.
    </div>

    <template v-else>
      <section class="page-hero pf-page-hero">
        <div class="page-hero-inner pf-hero-inner">
          <div class="pf-avatar">{{ initials }}</div>
          <div class="pf-hero-text">
            <p class="section-eyebrow">{{ user.profile }}</p>
            <h1 class="page-title">{{ fullName }}</h1>
          </div>
          <router-link to="/dashboard" class="btn-nav pf-dash-btn">Dashboard</router-link>
        </div>
      </section>

      <main class="pf-page">
        <div class="pf-grid">

          <section class="pf-card">
            <h2 class="pf-card-title">Account details</h2>
            <div class="pf-fields">
              <div class="pf-field">
                <label>Full name</label>
                <p>{{ fullName }}</p>
              </div>
              <div class="pf-field">
                <label>Email</label>
                <p>{{ user.email }}</p>
              </div>
              <div class="pf-field">
                <label>Username</label>
                <p>@{{ user.username }}</p>
              </div>
              <div class="pf-field">
                <label>Role</label>
                <p>{{ user.profile }}</p>
              </div>
            </div>

            <div class="pf-stats">
              <div class="pf-stat">
                <strong>{{ favLoading ? '—' : favorites.length }}</strong>
                <span>Saved favorites</span>
              </div>
            </div>
          </section>

          <section class="pf-card">
            <h2 class="pf-card-title">Saved Favorites</h2>

            <div v-if="favLoading" class="pf-loading">Loading…</div>

            <p v-else-if="favorites.length === 0" class="pf-empty-state">
              No saved favorites yet. Browse opportunities and star the ones you like.
            </p>

            <ul v-else class="pf-fav-list">
              <li v-for="fav in favorites" :key="fav.id" class="pf-fav-item">
                <div class="pf-fav-meta">
                  <span class="pf-fav-org">{{ fav.offer.organization }}</span>
                </div>
                <a
                  :href="fav.offer.link"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="pf-fav-title"
                >{{ fav.offer.title }}</a>
                <span class="pf-fav-hint">Open ↗</span>
              </li>
            </ul>

            <router-link v-if="favorites.length > 0" to="/dashboard" class="pf-manage-link">
              Manage all in Dashboard →
            </router-link>
          </section>

          <section class="pf-card">
            <h2 class="pf-card-title">Change Password</h2>
            <div v-if="pwSuccess" class="pw-success">Password changed successfully.</div>
            <div v-if="pwError" class="pw-error">{{ pwError }}</div>
            <div class="pf-fields">
              <div class="pf-field">
                <label>Current Password</label>
                <input type="password" v-model="pwForm.old_password" class="pw-input" />
              </div>
              <div class="pf-field">
                <label>New Password</label>
                <input type="password" v-model="pwForm.new_password" class="pw-input" />
              </div>
              <div class="pf-field">
                <label>Confirm New Password</label>
                <input type="password" v-model="pwForm.confirm" class="pw-input" />
              </div>
            </div>
            <button class="btn-primary pw-btn" :disabled="pwLoading" @click="submitChangePw">
              {{ pwLoading ? 'Saving…' : 'Change Password' }}
            </button>
          </section>

        </div>
      </main>
    </template>

    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuth } from '../../composables/useAuth.js'
import { api } from '../../services/api.js'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'

const { user, changePassword } = useAuth()

const favLoading = ref(false)
const favorites = ref([])

const fullName = computed(() => {
  if (!user.value) return ''
  const { first_name, last_name, username } = user.value
  return (first_name || last_name) ? `${first_name} ${last_name}`.trim() : username
})

const initials = computed(() =>
  fullName.value
    .split(' ')
    .map(w => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
)

const pwForm = ref({ old_password: '', new_password: '', confirm: '' })
const pwLoading = ref(false)
const pwError = ref(null)
const pwSuccess = ref(false)

async function submitChangePw() {
  pwError.value = null
  pwSuccess.value = false
  if (pwForm.value.new_password !== pwForm.value.confirm) {
    pwError.value = 'Passwords do not match.'
    return
  }
  if (pwForm.value.new_password.length < 8) {
    pwError.value = 'Password must be at least 8 characters.'
    return
  }
  pwLoading.value = true
  try {
    await changePassword(pwForm.value.old_password, pwForm.value.new_password)
    pwSuccess.value = true
    pwForm.value = { old_password: '', new_password: '', confirm: '' }
  } catch (e) {
    pwError.value = e.message
  } finally {
    pwLoading.value = false
  }
}

onMounted(async () => {
  if (!user.value) return
  favLoading.value = true
  try {
    const res = await api.get(`/api/users/${user.value.id}/favorites?page_size=10`)
    if (res?.ok) favorites.value = (await res.json()).results
  } finally {
    favLoading.value = false
  }
})
</script>

<style scoped>
.pf-empty-page {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  color: var(--ink-soft);
}
.pf-empty-page a { color: var(--ink); font-weight: 500; }

/* ── Hero ── */
.pf-page-hero {
  border-bottom: 1px solid var(--border);
  padding-bottom: 0;
}

.pf-hero-inner {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.pf-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--ink);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  font-weight: 700;
  font-family: 'DM Serif Display', serif;
  flex-shrink: 0;
}

.pf-hero-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.pf-hero-text .page-title {
  margin: 0;
}

.pf-dash-btn {
  flex-shrink: 0;
}

/* ── Body ── */
.pf-page {
  flex: 1;
  max-width: 1000px;
  width: 100%;
  margin: 0 auto;
  padding: 2rem 2rem 5rem;
}

.pf-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

.pf-card {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.pf-card-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--ink);
}

/* ── Fields ── */
.pf-fields {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.pf-field label {
  display: block;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--ink-faint);
  margin-bottom: 2px;
}

.pf-field p {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--ink);
}

/* ── Stats ── */
.pf-stats {
  display: flex;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  margin-top: auto;
}

.pf-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pf-stat strong {
  font-size: 1.6rem;
  font-family: 'DM Serif Display', serif;
  color: var(--ink);
}

.pf-stat span {
  font-size: 0.72rem;
  color: var(--ink-faint);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ── Favorites ── */
.pf-loading {
  font-size: 0.85rem;
  color: var(--ink-faint);
}

.pf-empty-state {
  font-size: 0.85rem;
  color: var(--ink-faint);
  line-height: 1.6;
}

.pf-fav-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  flex: 1;
  overflow-y: auto;
  max-height: 320px;
}

.pf-fav-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 0.85rem 1rem;
  border: 1px solid var(--border);
  border-radius: var(--r);
  transition: border-color 0.15s;
}

.pf-fav-item:hover { border-color: #bbb; }

.pf-fav-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pf-fav-org {
  font-size: 0.72rem;
  color: var(--ink-faint);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.pf-fav-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--ink);
  text-decoration: none;
  line-height: 1.4;
}

.pf-fav-title:hover { color: var(--ink-soft); }

.pf-fav-hint {
  font-size: 0.75rem;
  color: var(--ink-faint);
  font-weight: 500;
}

.pf-manage-link {
  font-size: 0.82rem;
  color: var(--ink-soft);
  text-decoration: none;
  font-weight: 500;
  margin-top: auto;
}

.pf-manage-link:hover { color: var(--ink); text-decoration: underline; }

.btn-nav {
  flex-shrink: 0;
}

/* ── Change password card ── */
.pw-input {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 0.38rem 0.55rem;
  font-size: 0.88rem;
  outline: none;
  font-family: 'DM Sans', sans-serif;
  background: var(--white);
  color: var(--ink);
  margin-top: 4px;
}

.pw-input:focus { border-color: var(--ink-soft); }

.pw-btn { align-self: flex-start; }

.pw-success {
  font-size: 0.85rem;
  color: #1d7347;
  background: #e7f4ea;
  border-radius: var(--r);
  padding: 0.45rem 0.7rem;
}

.pw-error {
  font-size: 0.85rem;
  color: #9e2a2a;
  background: #ffe4e4;
  border-radius: var(--r);
  padding: 0.45rem 0.7rem;
}
</style>

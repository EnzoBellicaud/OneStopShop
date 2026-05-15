<template>
  <div class="sharedbg">
    <AppHeader />

    <div v-if="!user" class="pf-empty-page">
      Please <router-link to="/login">log in</router-link> to view your profile.
    </div>

    <main v-else class="pf-page">

      <div class="pf-hero">
        <div class="pf-avatar">{{ initials }}</div>
        <div class="pf-hero-text">
          <h1 class="pf-name">{{ fullName }}</h1>
          <span class="pf-role-badge">{{ user.profile }}</span>
        </div>
        <router-link to="/dashboard" class="btn-nav">Dashboard</router-link>
      </div>

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

      </div>
    </main>

    <AppFooter />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuth } from '../../composables/useAuth.js'
import { api } from '../../services/api.js'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'

const { user } = useAuth()

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
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  font-size: 1rem;
  color: var(--ink-soft);
}
.pf-empty-page a { color: var(--accent-mid); }

.pf-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 3rem 2rem 5rem;
}

/* ── Hero strip ── */
.pf-hero {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 2rem 2rem;
  margin-bottom: 1.5rem;
}

.pf-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ef8023, #e62248);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  font-weight: 700;
  font-family: 'DM Serif Display', serif;
  flex-shrink: 0;
}

.pf-hero-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.pf-name {
  font-family: 'DM Serif Display', serif;
  font-size: clamp(1.4rem, 3vw, 1.9rem);
  color: var(--ink);
  line-height: 1.15;
}

.pf-role-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--accent-light);
  color: var(--accent-mid);
}

/* ── Two-column grid ── */
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

.pf-fav-title:hover { color: var(--accent-mid); }

.pf-fav-hint {
  font-size: 0.75rem;
  color: var(--accent-mid);
  font-weight: 500;
}

.pf-manage-link {
  font-size: 0.82rem;
  color: var(--accent-mid);
  text-decoration: none;
  font-weight: 500;
  margin-top: auto;
}

.pf-manage-link:hover { text-decoration: underline; }

/* re-use global nav button style */
.btn-nav {
  flex-shrink: 0;
}
</style>

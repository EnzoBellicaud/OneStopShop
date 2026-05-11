<template>
  <div>
    <div v-if="!user" class="profile-container">
      <div class="profile-card">
        <p style="text-align:center; color:#666;">
          Please <router-link to="/login" style="color:var(--accent-mid)">log in</router-link> to view your profile.
        </p>
      </div>
    </div>

    <div v-else class="profile-container">
      <div class="profile-card">
        <div class="profile-header">
          <div class="avatar-circle">{{ initials }}</div>
          <div class="header-info">
            <h2>{{ fullName }}</h2>
            <span class="role-badge">{{ user.profile }}</span>
          </div>
        </div>

        <div class="profile-details">
          <div class="detail-item">
            <label>Email Address</label>
            <p>{{ user.email }}</p>
          </div>
          <div class="detail-item">
            <label>Username</label>
            <p>{{ user.username }}</p>
          </div>
        </div>

        <div class="user-sections">
          <div class="section-box">
            <h3>Saved Favorites</h3>
            <div v-if="favLoading" class="placeholder-info">Loading…</div>
            <div v-else-if="favorites.length === 0" class="placeholder-info">No saved favorites yet.</div>
            <ul v-else class="favorites-list">
              <li v-for="fav in favorites" :key="fav.id" style="margin-bottom:8px;">
                <a :href="fav.offer.link" target="_blank" rel="noopener noreferrer" style="color:var(--accent-mid); text-decoration:none;">
                  ⭐ {{ fav.offer.title }} — {{ fav.offer.organization }}
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div class="profile-actions">
          <router-link to="/" class="edit-btn">Home page</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuth } from '../../composables/useAuth.js'
import { api } from '../../services/api.js'

const { user } = useAuth()

const favLoading = ref(false)
const favorites = ref([])

const fullName = computed(() => {
  if (!user.value) return ''
  const { first_name, last_name, username } = user.value
  return (first_name || last_name) ? `${first_name} ${last_name}`.trim() : username
})

const initials = computed(() => fullName.value.charAt(0).toUpperCase())

onMounted(async () => {
  if (!user.value) return
  favLoading.value = true
  try {
    const res = await api.get(`/api/users/${user.value.id}/favorites?page_size=10`)
    if (res && res.ok) {
      const data = await res.json()
      favorites.value = data.results
    }
  } finally {
    favLoading.value = false
  }
})
</script>

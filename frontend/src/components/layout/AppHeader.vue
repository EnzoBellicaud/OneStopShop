<template>
  <nav :style="cssVars">
    <router-link class="nav-logo" to="/">OneStop<span>Shop</span></router-link>

    <ul class="nav-links">
      <template v-if="route.name === 'landing'">
        <li><a href="#about">{{ t('nav.about') }}</a></li>
        <li><a href="#how">{{ t('nav.how') }}</a></li>
        <li><a href="#contact">{{ t('nav.contact') }}</a></li>
        <li>
          <router-link to="/forum" class="role-pill">{{ t('nav.forum') }}</router-link>
        </li>
      </template>
      <template v-else>
        <li>
          <router-link to="/student" class="role-pill" :class="{ active: route.name === 'student' }">
            {{ t('nav.student') }}
          </router-link>
        </li>
        <li>
          <router-link to="/staff" class="role-pill" :class="{ active: route.name === 'staff' }">
            {{ t('nav.staff') }}
          </router-link>
        </li>
        <li>
          <router-link to="/external_user" class="role-pill" :class="{ active: route.name === 'externaluser' }">
            {{ t('nav.external') }}
          </router-link>
        </li>
        <li>
          <router-link to="/forum" class="role-pill" :class="{ active: route.name === 'Forum' || route.name === 'QuestionDetail' || route.name === 'NewQuestion' }">
            {{ t('nav.forum') }}
          </router-link>
        </li>
      </template>
    </ul>

    <div class="nav-right">
      <!-- Language picker (self-contained, accessible component) -->
      <LanguageSwitcher />

      <template v-if="user">
        <span class="nav-username">{{ user.first_name || user.username }}</span>
        <a v-if="['Admin','Teacher','Company'].includes(user.profile)" :href="adminPortalUrlWithSso" target="_blank" class="btn-nav btn-portal">{{ t('nav.admin') }} ↗</a>
        <router-link to="/dashboard" class="btn-nav">{{ t('nav.dashboard') }}</router-link>
        <router-link to="/user_profile" class="btn-nav">{{ t('nav.profile') }}</router-link>
        <button class="btn-nav btn-logout" @click="handleLogout">{{ t('nav.logout') }}</button>
      </template>
      <template v-else>
        <router-link to="/login" class="btn-nav">{{ t('nav.login') }}</router-link>
      </template>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '../../composables/useAuth.js'
import LanguageSwitcher from './LanguageSwitcher.vue'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const { user, token, logout } = useAuth()

const adminPortalUrl = import.meta.env.VITE_ADMIN_URL || 'http://localhost:4200'
const adminPortalUrlWithSso = computed(() =>
  token.value
    ? `${adminPortalUrl}?sso_token=${encodeURIComponent(token.value)}`
    : adminPortalUrl
)

function handleLogout() {
  logout()
  router.push('/')
}

const isScrolled = ref(false)
const onScroll = () => { isScrolled.value = window.scrollY > 80 }
onMounted(() => window.addEventListener('scroll', onScroll))
onUnmounted(() => window.removeEventListener('scroll', onScroll))

const cssVars = computed(() => ({
  '--ink': isScrolled.value ? '#ffffff' : '#111110',
  '--ink-soft': isScrolled.value ? '#ffffff' : '#111110',
  '--blank': isScrolled.value ? '#111110' : '#ffffff00',
  '--surface': isScrolled.value ? '#111110' : '#fafaf8',
}))
</script>

<style scoped>
.btn-admin {
  background: var(--accent-mid, #9b2020) !important;
  color: #fff !important;
}

.btn-portal {
  font-size: 0.78rem;
  opacity: 0.85;
  text-decoration: none;
}
</style>

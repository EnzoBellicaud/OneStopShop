<template>
  <nav :style="cssVars">
    <router-link class="nav-logo" to="/">OneStop<span>Shop</span></router-link>

    <ul class="nav-links">
      <template v-if="route.name === 'landing'">
        <li><a href="#about">About</a></li>
        <li><a href="#how">How it works</a></li>
        <li><a href="#contact">Contact</a></li>
        <li>
          <router-link to="/forum" class="role-pill">Forum</router-link>
        </li>
      </template>
      <template v-else>
        <li>
          <router-link to="/student" class="role-pill" :class="{ active: route.name === 'student' }">
            Student
          </router-link>
        </li>
        <li>
          <router-link to="/staff" class="role-pill" :class="{ active: route.name === 'staff' }">
            Academic Staff
          </router-link>
        </li>
        <li>
          <router-link to="/external_user" class="role-pill" :class="{ active: route.name === 'externaluser' }">
            External
          </router-link>
        </li>
        <li>
          <router-link to="/forum" class="role-pill" :class="{ active: route.name === 'Forum' || route.name === 'QuestionDetail' || route.name === 'NewQuestion' }">
            Forum
          </router-link>
        </li>
      </template>
    </ul>

    <div class="nav-right">
      <!-- Language picker -->
      <div class="lang-picker" ref="langPickerRef">
        <button class="lang-btn" @click="langOpen = !langOpen" :aria-expanded="langOpen">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="8" cy="8" r="6.5"/>
            <path d="M8 1.5C8 1.5 6 4.5 6 8s2 6.5 2 6.5M8 1.5C8 1.5 10 4.5 10 8s-2 6.5-2 6.5M1.5 8h13"/>
            <path d="M2 5h12M2 11h12"/>
          </svg>
          <span>{{ currentLang.code.toUpperCase() }}</span>
          <svg class="chevron" :class="{ open: langOpen }" viewBox="0 0 10 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <path d="M1 1l4 4 4-4"/>
          </svg>
        </button>

        <div v-if="langOpen" class="lang-dropdown">
          <button
            v-for="lang in languages"
            :key="lang.code"
            class="lang-option"
            :class="{ active: lang.code === current }"
            @click="selectLang(lang.code)"
          >
            {{ lang.label }}
            <svg v-if="lang.code === current" viewBox="0 0 12 10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 5l3.5 3.5L11 1"/>
            </svg>
          </button>
        </div>
      </div>

      <template v-if="user">
        <span class="nav-username">{{ user.first_name || user.username }}</span>
        <router-link v-if="user.profile === 'Admin'" to="/admin" class="btn-nav btn-admin">Admin</router-link>
        <router-link to="/dashboard" class="btn-nav">Dashboard</router-link>
        <router-link to="/user_profile" class="btn-nav">Profile</router-link>
        <button class="btn-nav btn-logout" @click="handleLogout">Log out</button>
      </template>
      <template v-else>
        <router-link to="/login" class="btn-nav">Log in / Register</router-link>
      </template>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'
import { useLocale } from '../../composables/useLocale.js'

const router = useRouter()
const route = useRoute()
const { user, logout } = useAuth()
const { current, languages, setLocale } = useLocale()

const langOpen = ref(false)
const langPickerRef = ref(null)

const currentLang = computed(() => languages.find(l => l.code === current.value) ?? languages[0])

function selectLang(code) {
  setLocale(code)
  langOpen.value = false
}

function onClickOutside(e) {
  if (langPickerRef.value && !langPickerRef.value.contains(e.target)) {
    langOpen.value = false
  }
}

function handleLogout() {
  logout()
  router.push('/')
}

const isScrolled = ref(false)
const onScroll = () => { isScrolled.value = window.scrollY > 80 }
onMounted(() => {
  window.addEventListener('scroll', onScroll)
  document.addEventListener('mousedown', onClickOutside)
})
onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  document.removeEventListener('mousedown', onClickOutside)
})

const cssVars = computed(() => ({
  '--ink': isScrolled.value ? '#ffffff' : '#111110',
  '--ink-soft': isScrolled.value ? '#ffffff' : '#111110',
  '--blank': isScrolled.value ? '#111110' : '#ffffff00',
  '--surface': isScrolled.value ? '#111110' : '#fafaf8',
}))
</script>

<style scoped>
.lang-picker {
  position: relative;
}

.lang-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border: 1px solid var(--border, #e4e4e0);
  border-radius: var(--r, 6px);
  background: transparent;
  color: var(--ink-soft);
  font-size: 12px;
  font-weight: 500;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  white-space: nowrap;
}
.lang-btn:hover { border-color: var(--ink-soft); color: var(--ink); }
.lang-btn svg:first-child { width: 14px; height: 14px; flex-shrink: 0; }

.chevron { width: 8px; height: 6px; flex-shrink: 0; transition: transform 0.2s; }
.chevron.open { transform: rotate(180deg); }

.lang-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 140px;
  background: var(--white, #fff);
  border: 1px solid var(--border, #e4e4e0);
  border-radius: var(--r, 6px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  z-index: 200;
  overflow: hidden;
}

.lang-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 9px 14px;
  background: none;
  border: none;
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  color: #111110;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s;
  gap: 8px;
}
.lang-option:hover { background: var(--surface, #fafaf8); }
.lang-option.active { font-weight: 500; }
.lang-option svg { width: 12px; height: 10px; flex-shrink: 0; color: var(--accent-mid, #9b2020); }

.btn-admin {
  background: var(--accent-mid, #9b2020) !important;
  color: #fff !important;
}
</style>

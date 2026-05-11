<template>
  <nav :style="cssVars">
    <router-link class="nav-logo" to="/">Uni<span>Portal</span></router-link>
    <ul class="nav-links">
      <li><a href="#Opportunities">Opportunities</a></li>
      <li><a href="#about">About</a></li>
      <li><a href="#how">How it works</a></li>
      <li><a href="#contact">Contact</a></li>
    </ul>
    <div class="nav-right">
      <template v-if="user">
        <span class="nav-username">{{ user.first_name || user.username }}</span>
        <router-link to="/user_profile" class="btn-nav">Profile</router-link>
        <button class="btn-nav btn-logout" @click="handleLogout">Log out</button>
      </template>
      <template v-else>
        <router-link to="/login" class="btn-nav">Log in / Register</router-link>
      </template>
      <router-link to="/home" class="btn-nav">Browse opportunities</router-link>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth.js'

const router = useRouter()
const { user, logout } = useAuth()

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
  '--surface': isScrolled.value ? '111110' : '#fafaf8',
}))
</script>

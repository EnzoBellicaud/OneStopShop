<template>
    <nav :style="cssVars">
        <a class="nav-logo" href="/">Uni<span>Portal</span></a>
        <ul class="nav-links">
            <li><a href="#Opportunities">Opportunities</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#how">How it works</a></li>
            <li><a href="#contact">Contact</a></li>
        </ul>
        <div class="nav-right">
            <a class="btn-nav" href="#opportunities">Browse opportunities</a>
            <template v-if="isLoggedIn">
                <span class="nav-username">{{ user?.username }}</span>
                <button class="btn-login" @click="logout">Logout</button>
            </template>
            <RouterLink v-else to="/auth" class="btn-login">Login</RouterLink>
        </div>
    </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuth } from '../../composables/useAuth'

const { user, isLoggedIn, logout } = useAuth()

const isScrolled = ref(false)

const onScroll = () => {
  isScrolled.value = window.scrollY > 80
}

onMounted(() => window.addEventListener('scroll', onScroll))
onUnmounted(() => window.removeEventListener('scroll', onScroll))

const cssVars = computed(() => ({
  '--ink': isScrolled.value ? '#ffffff' : '#111110',
  '--ink-soft': isScrolled.value ? '#ffffff' : '#111110',
  '--surface': isScrolled.value ? '#111110' : '#ffffff'
}))
</script>

<style scoped>
.nav-username {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
  padding: 8px 4px;
}

.btn-login {
  padding: 8px 16px;
  border: 1px solid #111110;
  border-radius: 4px;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
  color: #111110;
  background: transparent;
  font-size: 14px;
}

.btn-login:hover {
  background: #111110;
  color: #ffffff;
}
</style>

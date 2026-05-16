<template>
    <nav :style="cssVars">
        <RouterLink class="nav-logo" :to="{ name: 'Home' }">One Stop<span> shop</span></RouterLink>
        <ul class="nav-links">
            <li><RouterLink :to="{ name: 'Home', hash: '#Opportunities' }">Opportunities</RouterLink></li>
            <li><RouterLink :to="{ name: 'Home', hash: '#about' }">About</RouterLink></li>
            <li><RouterLink :to="{ name: 'Home', hash: '#how' }">How it works</RouterLink></li>
            <li><RouterLink :to="{ name: 'Home', hash: '#contact' }">Contact</RouterLink></li>
            <li><RouterLink :to="{ name: 'Forum' }">Forum</RouterLink></li>
        </ul>
        <div class="nav-right">
            <RouterLink class="btn-nav" :to="{ name: 'Offers' }">Browse opportunities</RouterLink>
            <template v-if="isLoggedIn">
                <RouterLink :to="{ name: 'Profile' }" class="nav-username">{{ user?.username }}</RouterLink>
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
  text-decoration: none;
}

.nav-username:hover {
  text-decoration: underline;
}

.btn-login {
  padding: 8px 16px;
  border: 1px solid var(--ink);
  border-radius: 4px;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--ink);
  background: transparent;
  font-size: 14px;
}

.btn-login:hover {
  background: var(--ink);
  color: var(--surface);
}
</style>

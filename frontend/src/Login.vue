<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from './composables/useAuth.js'
import AppHeader from './components/layout/AppHeader.vue'

const router = useRouter()
const route = useRoute()
const { login, register, loading, error } = useAuth()

const mode = ref('login')

const form = ref({
  username: '',
  email: '',
  password: '',
  profile: 'Student',
})

async function submit() {
  let ok
  if (mode.value === 'login') {
    ok = await login(form.value.username, form.value.password)
  } else {
    ok = await register(form.value.username, form.value.email, form.value.password, form.value.profile)
  }
  if (ok) {
    router.push(route.query.redirect || '/')
  }
}
</script>

<template>
  <AppHeader />
  <div class="login-page">
    <div class="login-card">
      <div class="login-tabs">
        <button :class="['tab', { active: mode === 'login' }]" @click="mode = 'login'">Log in</button>
        <button :class="['tab', { active: mode === 'register' }]" @click="mode = 'register'">Register</button>
      </div>

      <form @submit.prevent="submit" class="login-form">
        <div v-if="error" class="form-error">{{ error }}</div>

        <label>
          Username
          <input v-model="form.username" type="text" required autocomplete="username" />
        </label>

        <template v-if="mode === 'register'">
          <label>
            Email
            <input v-model="form.email" type="email" required autocomplete="email" />
          </label>
        </template>

        <label>
          Password
          <input v-model="form.password" type="password" required :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" />
        </label>

        <template v-if="mode === 'register'">
          <label>
            Profile type
            <select v-model="form.profile">
              <option value="Student">Student</option>
              <option value="Academic staff">Academic staff</option>
              <option value="Company">Company</option>
            </select>
          </label>
        </template>

        <button type="submit" class="btn-submit-login" :disabled="loading">
          {{ loading ? 'Please wait…' : (mode === 'login' ? 'Log in' : 'Create account') }}
        </button>
      </form>
    </div>
  </div>
</template>

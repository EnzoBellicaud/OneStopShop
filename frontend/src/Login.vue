<template>
  <div class="auth-page">

    <!-- Left branding panel -->
    <div class="auth-brand">
      <router-link class="brand-logo" to="/">OneStop<span>Shop</span></router-link>
      <div class="brand-body">
        <h2>Your gateway to academic opportunities</h2>
        <p>Scholarships, internships, thesis projects, and research partnerships — all in one place.</p>
        <ul class="brand-features">
          <li><span class="feat-dot"></span>9 partner universities</li>
          <li><span class="feat-dot"></span>Smart need-matching</li>
          <li><span class="feat-dot"></span>Save & track favourites</li>
        </ul>
      </div>
      <p class="brand-footer">SUNRISE Academic Network · 2026</p>
    </div>

    <!-- Right form panel -->
    <div class="auth-form-panel">
      <div class="auth-card">

        <div class="auth-card-header">
          <h1>{{ mode === 'login' ? 'Welcome back' : 'Create account' }}</h1>
          <p>{{ mode === 'login' ? 'Sign in to your OneStopShop account' : 'Join the OneStopShop network' }}</p>
        </div>

        <div v-if="error" class="auth-error">{{ error }}</div>

        <!-- Pending approval success card — shown instead of form after Teacher/Company registers -->
        <div v-if="pendingApproval" class="pending-card">
          <div class="pending-icon">✓</div>
          <h3>Registration submitted</h3>
          <p>Your account is pending admin approval. You will be able to log in once an admin activates your account.</p>
          <button class="switch-btn" @click="switchMode">Back to login</button>
        </div>

        <form v-if="!pendingApproval" @submit.prevent="submit" class="auth-form">

          <div class="field">
            <label for="username">Username</label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              placeholder="your_username"
              required
              autocomplete="username"
            />
          </div>

          <template v-if="mode === 'register'">
            <div class="field">
              <label for="email">Email</label>
              <input
                id="email"
                v-model="form.email"
                type="email"
                placeholder="you@university.edu"
                required
                autocomplete="email"
              />
              <p v-if="form.profile === 'Teacher'" class="field-hint">
                ℹ Use your university email (e.g. you@mdu.se)
              </p>
            </div>

            <template v-if="form.profile === 'Company'">
              <div class="field">
                <label for="company_name">Company Name *</label>
                <input
                  id="company_name"
                  v-model="form.company_name"
                  type="text"
                  placeholder="Acme Corp"
                  autocomplete="organization"
                />
              </div>
              <div class="field">
                <label for="company_country">Country (2-letter code) *</label>
                <input
                  id="company_country"
                  v-model="form.company_country"
                  type="text"
                  maxlength="2"
                  placeholder="DE"
                  style="text-transform:uppercase"
                />
              </div>
              <div class="field">
                <label for="company_website">Website</label>
                <input
                  id="company_website"
                  v-model="form.company_website"
                  type="url"
                  placeholder="https://acme.com"
                />
              </div>
            </template>
          </template>

          <div class="field">
            <label for="password">Password</label>
            <div class="password-wrap">
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                required
                :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
              />
              <button type="button" class="pwd-toggle" @click="showPassword = !showPassword" tabindex="-1">
                {{ showPassword ? 'Hide' : 'Show' }}
              </button>
            </div>
          </div>

          <template v-if="mode === 'register'">
            <div class="field">
              <label>I am a…</label>
              <div class="role-picker">
                <button
                  v-for="role in roles"
                  :key="role.value"
                  type="button"
                  :class="['role-card', { selected: form.profile === role.value }]"
                  @click="form.profile = role.value"
                >
                  <span class="role-icon">{{ role.icon }}</span>
                  <span class="role-label">{{ role.label }}</span>
                </button>
              </div>
            </div>
          </template>

          <p v-if="mode === 'register' && (form.profile === 'Teacher' || form.profile === 'Company')" class="approval-note">
            ℹ Teacher and Company accounts require admin approval before you can log in.
          </p>

          <button type="submit" class="auth-submit" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            {{ loading ? 'Please wait…' : (mode === 'login' ? 'Log in' : 'Create account') }}
          </button>

        </form>

        <p class="auth-switch">
          {{ mode === 'login' ? "Don't have an account?" : 'Already have an account?' }}
          <button class="switch-btn" @click="switchMode">
            {{ mode === 'login' ? 'Register' : 'Log in' }}
          </button>
        </p>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from './composables/useAuth.js'

const router = useRouter()
const route = useRoute()
const { login, register, loading, error } = useAuth()

const mode = ref('login')
const showPassword = ref(false)
const pendingApproval = ref(false)

const roles = [
  { value: 'Student',        label: 'Student',    icon: '🎓' },
  { value: 'Academic staff', label: 'Researcher', icon: '🔬' },
  { value: 'Teacher',        label: 'Teacher',    icon: '📚' },
  { value: 'Company',        label: 'Company',    icon: '🏢' },
]

const form = ref({
  username: '', email: '', password: '', profile: 'Student',
  company_name: '', company_country: '', company_website: '',
})

function switchMode() {
  mode.value = mode.value === 'login' ? 'register' : 'login'
  showPassword.value = false
  pendingApproval.value = false
  error.value = null
}

async function submit() {
  if (mode.value === 'login') {
    const ok = await login(form.value.username, form.value.password)
    if (ok) router.push(route.query.redirect || '/')
  } else {
    if (form.value.profile === 'Company') {
      if (!form.value.company_name.trim()) {
        error.value = 'Company name is required.'
        return
      }
      if (form.value.company_country.trim().length !== 2) {
        error.value = 'Country must be a 2-letter code (e.g. DE, SE, IT).'
        return
      }
    }
    const extraFields = form.value.profile === 'Company'
      ? {
          company_name:    form.value.company_name.trim(),
          company_country: form.value.company_country.trim().toUpperCase(),
          company_website: form.value.company_website.trim(),
        }
      : {}
    const result = await register(form.value.username, form.value.email, form.value.password, form.value.profile, extraFields)
    if (result && result.pending) {
      pendingApproval.value = true
    } else if (result === true) {
      router.push(route.query.redirect || '/')
    }
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
}

/* ── Left panel ── */
.auth-brand {
  background: var(--ink);
  display: flex;
  flex-direction: column;
  padding: 3rem;
  position: relative;
  overflow: hidden;
}

.auth-brand::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255,255,255,0.07) 1px, transparent 1px);
  background-size: 24px 24px;
}

.brand-logo {
  font-family: 'DM Serif Display', serif;
  font-size: 1.5rem;
  color: #fff;
  text-decoration: none;
  position: relative;
  z-index: 1;
}
.brand-logo span { color: rgba(255,255,255,0.65); }

.brand-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.brand-body h2 {
  font-family: 'DM Serif Display', serif;
  font-size: clamp(1.6rem, 3vw, 2.4rem);
  color: #fff;
  line-height: 1.2;
  margin-bottom: 1rem;
}

.brand-body p {
  font-size: 0.95rem;
  color: rgba(255,255,255,0.8);
  line-height: 1.7;
  max-width: 340px;
  margin-bottom: 2rem;
}

.brand-features {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.brand-features li {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.88rem;
  color: rgba(255,255,255,0.9);
  font-weight: 500;
}

.feat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #fff;
  flex-shrink: 0;
}

.brand-footer {
  font-size: 0.72rem;
  color: rgba(255,255,255,0.45);
  position: relative;
  z-index: 1;
}

/* ── Right panel ── */
.auth-form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  background: var(--surface);
}

.auth-card {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.auth-card-header h1 {
  font-family: 'DM Serif Display', serif;
  font-size: 1.8rem;
  color: var(--ink);
  margin-bottom: 0.3rem;
}

.auth-card-header p {
  font-size: 0.88rem;
  color: var(--ink-soft);
}

/* ── Error ── */
.auth-error {
  padding: 0.75rem 1rem;
  background: var(--accent-light);
  color: var(--accent-mid);
  border-radius: var(--r);
  font-size: 0.85rem;
  border-left: 3px solid var(--accent-mid);
}

/* ── Form ── */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.field label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--ink-soft);
}

.field input {
  padding: 0.65rem 0.9rem;
  border: 1px solid var(--border);
  border-radius: var(--r);
  font-size: 0.9rem;
  font-family: 'DM Sans', sans-serif;
  color: var(--ink);
  background: var(--white);
  outline: none;
  transition: border-color 0.2s;
}

.field input:focus {
  border-color: var(--ink);
}

/* ── Password toggle ── */
.password-wrap {
  position: relative;
}

.password-wrap input {
  width: 100%;
  padding-right: 4rem;
}

.pwd-toggle {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--ink-faint);
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.pwd-toggle:hover { color: var(--ink); }

/* ── Role picker ── */
.role-picker {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.role-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  padding: 0.85rem 0.5rem;
  border: 1.5px solid var(--border);
  border-radius: var(--r);
  background: var(--white);
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  transition: all 0.15s;
}

.role-card:hover {
  border-color: #bbb;
}

.role-card.selected {
  border-color: var(--ink);
  background: var(--ink);
}

.role-icon { font-size: 1.4rem; }

.role-label {
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--ink-soft);
  text-align: center;
  line-height: 1.3;
}

.role-card.selected .role-label { color: #fff; }

/* ── Submit ── */
.auth-submit {
  padding: 0.75rem;
  background: var(--ink);
  color: var(--white);
  border: none;
  border-radius: var(--r);
  font-size: 0.9rem;
  font-weight: 500;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  transition: opacity 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.auth-submit:hover:not(:disabled) { opacity: 0.85; }
.auth-submit:disabled { opacity: 0.5; cursor: not-allowed; }

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ── Switch mode ── */
.auth-switch {
  text-align: center;
  font-size: 0.85rem;
  color: var(--ink-soft);
}

.switch-btn {
  background: none;
  border: none;
  color: var(--accent-mid);
  font-weight: 600;
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  font-size: 0.85rem;
  margin-left: 0.25rem;
}

.switch-btn:hover { text-decoration: underline; }

/* ── Field hint ── */
.field-hint {
  font-size: 0.78rem;
  color: var(--ink-soft);
  margin: 0;
}

/* ── Approval note ── */
.approval-note {
  font-size: 0.8rem;
  color: var(--ink-soft);
  background: #f0f4ff;
  border-left: 3px solid #6b8ccc;
  border-radius: 4px;
  padding: 0.5rem 0.75rem;
  margin: 0;
}

/* ── Pending approval card ── */
.pending-card {
  text-align: center;
  padding: 1.5rem 1rem;
  background: #f0fff4;
  border: 1.5px solid #86efac;
  border-radius: var(--r);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.pending-icon {
  width: 44px;
  height: 44px;
  background: #22c55e;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  font-weight: 700;
}

.pending-card h3 {
  font-size: 1.1rem;
  color: var(--ink);
  margin: 0;
}

.pending-card p {
  font-size: 0.85rem;
  color: var(--ink-soft);
  margin: 0;
  line-height: 1.6;
}
</style>

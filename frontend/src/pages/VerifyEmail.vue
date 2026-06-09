<template>
  <div class="verify-page">
    <div class="verify-card">

      <!-- Loading state -->
      <div v-if="state === 'loading'" class="verify-state">
        <div class="spinner"></div>
        <h2>Verifying your email...</h2>
        <p>Please wait a moment.</p>
      </div>

      <!-- Success state -->
      <div v-else-if="state === 'success'" class="verify-state">
        <div class="verify-icon success">✓</div>
        <h2>Email verified!</h2>
        <p>Your email address has been confirmed. You can now log in to your account.</p>
        <router-link to="/login" class="verify-btn">Go to Login</router-link>
      </div>

      <!-- Error state -->
      <div v-else-if="state === 'error'" class="verify-state">
        <div class="verify-icon error">✕</div>
        <h2>Verification failed</h2>
        <p>{{ errorMessage }}</p>
        <router-link to="/login" class="verify-btn secondary">Back to Login</router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../services/api.js'

const state = ref('loading')
const errorMessage = ref('This link may be invalid or expired. Please contact an admin.')

onMounted(async () => {
  const params = new URLSearchParams(window.location.search)
  const token = params.get('token')

  if (!token) {
    errorMessage.value = 'No verification token found. Please use the link sent to your email.'
    state.value = 'error'
    return
  }

  try {
    const res = await api.get(`/api/auth/verify-email?token=${token}`)
    if (res.ok) {
      state.value = 'success'
    } else {
      const data = await res.json()
      errorMessage.value = data.message || 'Verification failed. The link may have expired.'
      state.value = 'error'
    }
  } catch {
    errorMessage.value = 'Something went wrong. Please try again later.'
    state.value = 'error'
  }
})
</script>

<style scoped>
.verify-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.verify-card {
  background: white;
  border-radius: 16px;
  padding: 48px 40px;
  max-width: 440px;
  width: 100%;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.verify-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.verify-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 8px;
}

.verify-icon.success {
  background: #e2efda;
  color: #3a7d44;
}

.verify-icon.error {
  background: #fde8e8;
  color: #c0392b;
}

.verify-state h2 {
  font-size: 1.4rem;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.verify-state p {
  color: #666;
  font-size: 0.95rem;
  line-height: 1.5;
  margin: 0;
}

.verify-btn {
  margin-top: 12px;
  display: inline-block;
  padding: 12px 28px;
  background: #4472c4;
  color: white;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  transition: background 0.2s;
}

.verify-btn:hover {
  background: #2f5496;
}

.verify-btn.secondary {
  background: transparent;
  color: #4472c4;
  border: 2px solid #4472c4;
}

.verify-btn.secondary:hover {
  background: #f0f4ff;
}

/* Spinner */
.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e0e0e0;
  border-top-color: #4472c4;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

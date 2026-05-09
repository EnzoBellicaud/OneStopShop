<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1>{{ isLogin ? 'Login' : 'Create Account' }}</h1>
        <p>{{ isLogin ? 'Welcome back to UniPortal' : 'Join UniPortal today' }}</p>
      </div>

      <!-- Login Form -->
      <form v-if="isLogin" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="login-username">Username</label>
          <input
            id="login-username"
            v-model="loginForm.username"
            type="text"
            required
            placeholder="Enter your username"
          />
        </div>

        <div class="form-group">
          <label for="login-password">Password</label>
          <input
            id="login-password"
            v-model="loginForm.password"
            type="password"
            required
            placeholder="Enter your password"
          />
        </div>

        <button type="submit" class="btn-submit">Login</button>
        <div v-if="loginError" class="error-message">{{ loginError }}</div>
      </form>

      <!-- Register Form -->
      <form v-else @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="reg-username">Username</label>
          <input
            id="reg-username"
            v-model="registerForm.username"
            type="text"
            required
            placeholder="Choose a username"
          />
        </div>

        <div class="form-group">
          <label for="reg-email">Email</label>
          <input
            id="reg-email"
            v-model="registerForm.email"
            type="email"
            required
            placeholder="Enter your email"
          />
        </div>

        <div class="form-group">
          <label for="reg-password">Password</label>
          <input
            id="reg-password"
            v-model="registerForm.password"
            type="password"
            required
            placeholder="Minimum 8 characters"
          />
        </div>

        <div class="form-group">
          <label for="reg-first-name">First Name</label>
          <input
            id="reg-first-name"
            v-model="registerForm.firstName"
            type="text"
            placeholder="Optional"
          />
        </div>

        <div class="form-group">
          <label for="reg-last-name">Last Name</label>
          <input
            id="reg-last-name"
            v-model="registerForm.lastName"
            type="text"
            placeholder="Optional"
          />
        </div>

        <div class="form-group">
          <label for="reg-profile">Profile Type</label>
          <select id="reg-profile" v-model="registerForm.profile" required>
            <option value="">Select your profile</option>
            <option value="Student">Student</option>
            <option value="Academic staff">Academic Staff</option>
            <option value="Company">Company</option>
          </select>
        </div>

        <button type="submit" class="btn-submit">Create Account</button>
        <div v-if="registerError" class="error-message">{{ registerError }}</div>
      </form>

      <!-- Toggle between Login and Register -->
      <div class="auth-toggle">
        <p>
          {{ isLogin ? "Don't have an account?" : 'Already have an account?' }}
          <button
            type="button"
            @click="isLogin = !isLogin"
            class="toggle-btn"
          >
            {{ isLogin ? 'Register' : 'Login' }}
          </button>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { login, register } = useAuth()

const isLogin = ref(true)

const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ username: '', email: '', password: '', firstName: '', lastName: '', profile: '' })

const loginError = ref('')
const registerError = ref('')

const handleLogin = async () => {
  loginError.value = ''
  try {
    await login(loginForm.value.username, loginForm.value.password)
    router.push('/')
  } catch (error) {
    loginError.value = error.message
  }
}

const handleRegister = async () => {
  registerError.value = ''
  if (registerForm.value.password.length < 8) {
    registerError.value = 'Password must be at least 8 characters'
    return
  }
  if (!registerForm.value.profile) {
    registerError.value = 'Please select a profile type'
    return
  }
  try {
    await register({
      username: registerForm.value.username,
      email: registerForm.value.email,
      password: registerForm.value.password,
      first_name: registerForm.value.firstName,
      last_name: registerForm.value.lastName,
      profile: registerForm.value.profile,
    })
    router.push('/')
  } catch (error) {
    registerError.value = error.message
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%);
  padding: 20px;
}

.auth-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  padding: 40px;
}

.auth-header {
  text-align: center;
  margin-bottom: 30px;
}

.auth-header h1 {
  font-size: 28px;
  margin: 0 0 10px 0;
  color: #111110;
}

.auth-header p {
  color: #888;
  margin: 0;
  font-size: 14px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #111110;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #111110;
  box-shadow: 0 0 0 2px rgba(17, 17, 16, 0.1);
}

.btn-submit {
  width: 100%;
  padding: 12px;
  background: #111110;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-submit:hover {
  background: #333;
}

.error-message {
  color: #d32f2f;
  font-size: 13px;
  margin-top: 10px;
  padding: 10px;
  background: #ffebee;
  border-radius: 4px;
  text-align: center;
}

.auth-toggle {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.toggle-btn {
  background: none;
  border: none;
  color: #111110;
  cursor: pointer;
  font-weight: 500;
  text-decoration: underline;
  padding: 0;
  font-size: 14px;
}

.toggle-btn:hover {
  color: #333;
}
</style>

<template>
  <section class="selection-screen">
    <div class="container">
      <div class="text-center">
        <h1 class="title">Welcome to <span>UniPortal</span></h1>
        <p class="subtitle">Select your profile to view tailored content</p>
      </div>

      <div class="grid-profiles">
        <div class="profile-card" @click="navigateTo('student')">
          <div class="icon">🎓</div>
          <h3>Student</h3>
          <p>Access courses, grades, and campus services effortlessly.</p>
          <router-link to="/student" class="select-btn">Continue as Student</router-link>
        </div>

        <div class="profile-card" @click="navigateTo('staff')">
          <div class="icon">💼</div>
          <h3>Academic Staff</h3>
          <p>Manage teaching materials, research, and administrative tasks.</p>
          <router-link to="/staff" class="select-btn">Continue as Staff</router-link>
        </div>

        <div class="profile-card" @click="navigateTo('external')">
          <div class="icon">🌐</div>
          <h3>External User</h3>
          <p>Discover public events, partnerships, and general information.</p>
          <router-link to="/external_user" class="select-btn">Explore Portal</router-link>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const emit = defineEmits(['select-role']);

const navigateTo = (role) => {
  console.log('Selected role:', role);
  emit('select-role', role);
};
</script>


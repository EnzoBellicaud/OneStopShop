<script setup>
import RoleContent from './RoleContent.vue'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'
const items = ['thesis', 'training']
</script>

<template>
  <div class="sharedbg">
    <AppHeader />
    <RoleContent
      search-placeholder="Search internships, thesis topics..."
      :shortcuts="items"
      target-profile="Student"
    />
    <AppFooter />
  </div>
</template>

<script setup>
import RoleContent from './RoleContent.vue'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'
const items = ['funding_partner', 'research_group']
</script>

<template>
  <div class="sharedbg">
    <AppHeader />
    <RoleContent
      search-placeholder="Search funding partners, research groups..."
      :shortcuts="items"
      target-profile="company"
    />
    <AppFooter />
  </div>
</template>

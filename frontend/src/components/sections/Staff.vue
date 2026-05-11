<script setup>
import RoleContent from './RoleContent.vue'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'
const items = ['research_group', 'funding_partner', 'training']
</script>

<template>
  <div class="sharedbg">
    <AppHeader />
    <RoleContent
      search-placeholder="Search research groups, funding..."
      :shortcuts="items"
      target-profile="researcher"
    />
    <AppFooter />
  </div>
</template>

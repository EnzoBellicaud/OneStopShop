<script setup>
import RoleContent from './RoleContent.vue'
const items = ['infrastructure', 'research group', 'experts', 'events', 'demonstrators', 'project opportunities']
</script>

<template>
  <RoleContent 
    search-placeholder="Search research groups, infrastructure..." 
    :shortcuts="items" 
  />
</template>
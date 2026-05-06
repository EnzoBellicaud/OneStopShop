<script setup>
import RoleContent from './RoleContent.vue'
const items = ['internship', 'thesis', 'challenge', 'hackathon', 'event', 'mobility']
</script>

<template>
  <RoleContent 
    search-placeholder="Search internships, hackathons..." 
    :shortcuts="items" 
  />
</template>
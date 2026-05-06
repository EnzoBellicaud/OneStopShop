<script setup>
import RoleContent from './RoleContent.vue'
const items = ['life long learning (LLL)', 'experts', 'trainings', 'testbeds', 'labs']
</script>

<template>
  <RoleContent 
    search-placeholder="Search labs, trainings..." 
    :shortcuts="items" 
  />
</template>
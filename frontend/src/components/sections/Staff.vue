<script setup>
import RoleContent from './RoleContent.vue'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'

const items = [
  { label: 'Infrastructure',        type: 'offer_type', value: 'testbed' },
  { label: 'Research Group',        type: 'offer_type', value: 'research_group' },
  { label: 'Experts',               type: 'offer_type', value: 'service' },
  { label: 'Events',                type: 'offer_type', value: 'training' },
  { label: 'Demonstrators',         type: 'offer_type', value: 'co_creation' },
  { label: 'Project Opportunities', type: 'offer_type', value: 'project_opportunity' },
]
</script>

<template>
  <div>
    <AppHeader />
    <RoleContent
      title="Academic Staff"
      description="Discover research groups, infrastructure, expert services, and project opportunities."
      search-placeholder="Search research groups, infrastructure, projects..."
      :shortcuts="items"
      target-profile="researcher"
    />
    <AppFooter />
  </div>
</template>

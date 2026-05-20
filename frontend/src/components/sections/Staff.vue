<script setup>
import RoleContent from './RoleContent.vue'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'

const items = [
  { label: 'Research Groups',       type: 'offer_type', value: 'research_group' },
  { label: 'Funding Partners',      type: 'offer_type', value: 'funding_partner' },
  { label: 'Expert Services',       type: 'offer_type', value: 'service' },
  { label: 'Thesis',                type: 'offer_type', value: 'thesis' },
  { label: 'Labs',                  type: 'offer_type', value: 'lab' },
  { label: 'Projects',              type: 'offer_type', value: 'project_opportunity' },
  { label: 'Co-creation',           type: 'offer_type', value: 'co_creation' },
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

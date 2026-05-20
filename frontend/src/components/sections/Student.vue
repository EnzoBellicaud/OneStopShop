<script setup>
import RoleContent from './RoleContent.vue'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'

const items = [
  { label: 'Programs',         type: 'offer_type', value: 'training' },
  { label: 'Thesis',           type: 'offer_type', value: 'thesis' },
  { label: 'Expert Services',  type: 'offer_type', value: 'service' },
  { label: 'Co-creation',      type: 'offer_type', value: 'co_creation' },
  { label: 'Internship',       type: 'offer_type', value: 'internship' },
  { label: 'Funding',          type: 'offer_type', value: 'funding_partner' },
  { label: 'Research Groups',  type: 'offer_type', value: 'research_group' },
  { label: 'Projects',         type: 'offer_type', value: 'project_opportunity' },
]
</script>

<template>
  <div>
    <AppHeader />
    <RoleContent
      title="Student Opportunities"
      description="Find internships, thesis projects, challenges, hackathons, and more across our partner universities."
      search-placeholder="Search internships, thesis topics..."
      :shortcuts="items"
      target-profile="student"
    />
    <AppFooter />
  </div>
</template>

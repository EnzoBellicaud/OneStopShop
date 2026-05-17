<script setup>
import RoleContent from './RoleContent.vue'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'

const items = [
  { label: 'Internship',  type: 'offer_type', value: 'internship' },
  { label: 'Thesis',      type: 'offer_type', value: 'thesis' },
  { label: 'Challenge',   type: 'offer_type', value: 'challenge' },
  { label: 'Hackathon',   type: 'offer_type', value: 'hackathon' },
  { label: 'Mobility',    type: 'domain',     value: 'Mobility' },
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
      target-profile="Student"
    />
    <AppFooter />
  </div>
</template>

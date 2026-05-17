<script setup>
import RoleContent from './RoleContent.vue'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'

const items = [
  { label: 'Life Long Learning (LLL)', type: 'offer_type', value: 'co_creation' },
  { label: 'Experts',                  type: 'offer_type', value: 'service' },
  { label: 'Trainings',                type: 'offer_type', value: 'training' },
  { label: 'Testbeds',                 type: 'offer_type', value: 'testbed' },
  { label: 'Labs',                     type: 'offer_type', value: 'lab' },
]
</script>

<template>
  <div>
    <AppHeader />
    <RoleContent
      title="External Programs"
      description="Explore lifelong learning, expert services, trainings, testbeds, and labs."
      search-placeholder="Search trainings, labs, testbeds, experts..."
      :shortcuts="items"
      target-profile="company"
    />
    <AppFooter />
  </div>
</template>

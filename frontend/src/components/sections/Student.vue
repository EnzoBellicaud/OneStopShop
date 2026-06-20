<script setup>
import RoleContent from './RoleContent.vue'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const items = [
  { labelKey: 'role.sc.programs',        type: 'offer_type', value: 'training' },
  { labelKey: 'role.sc.thesis',          type: 'offer_type', value: 'thesis' },
  { labelKey: 'role.sc.expertServices',  type: 'offer_type', value: 'service' },
  { labelKey: 'role.sc.coCreation',      type: 'offer_type', value: 'co_creation' },
  { labelKey: 'role.sc.internship',      type: 'offer_type', value: 'internship' },
  { labelKey: 'role.sc.funding',         type: 'offer_type', value: 'funding_partner' },
  { labelKey: 'role.sc.researchGroups',  type: 'offer_type', value: 'research_group' },
  { labelKey: 'role.sc.projects',        type: 'offer_type', value: 'project_opportunity' },
]
</script>

<template>
  <div>
    <AppHeader />
    <RoleContent
      :title="t('roles.student.title')"
      :description="t('roles.student.description')"
      :search-placeholder="t('roles.student.searchPlaceholder')"
      :shortcuts="items"
      target-profile="student"
    />
    <AppFooter />
  </div>
</template>

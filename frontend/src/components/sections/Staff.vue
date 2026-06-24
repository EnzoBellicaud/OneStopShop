<script setup>
import RoleContent from './RoleContent.vue'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const items = [
  { labelKey: 'role.sc.researchGroups',  type: 'offer_type', value: 'research_group' },
  { labelKey: 'role.sc.fundingPartners', type: 'offer_type', value: 'funding_partner' },
  { labelKey: 'role.sc.expertServices',  type: 'offer_type', value: 'service' },
  { labelKey: 'role.sc.thesis',          type: 'offer_type', value: 'thesis' },
  { labelKey: 'role.sc.labs',            type: 'offer_type', value: 'lab' },
  { labelKey: 'role.sc.projects',        type: 'offer_type', value: 'project_opportunity' },
  { labelKey: 'role.sc.coCreation',      type: 'offer_type', value: 'co_creation' },
]
</script>

<template>
  <div>
    <AppHeader />
    <RoleContent
      :title="t('roles.staff.title')"
      :description="t('roles.staff.description')"
      :search-placeholder="t('roles.staff.searchPlaceholder')"
      :shortcuts="items"
      target-profile="researcher"
    />
    <AppFooter />
  </div>
</template>

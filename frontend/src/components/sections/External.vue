<script setup>
import RoleContent from './RoleContent.vue'
import AppHeader from '../layout/AppHeader.vue'
import AppFooter from '../layout/AppFooter.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const items = [
  { labelKey: 'role.sc.lll',       type: 'offer_type', value: 'co_creation' },
  { labelKey: 'role.sc.experts',   type: 'offer_type', value: 'service' },
  { labelKey: 'role.sc.trainings', type: 'offer_type', value: 'training' },
  { labelKey: 'role.sc.testbeds',  type: 'offer_type', value: 'testbed' },
  { labelKey: 'role.sc.labs',      type: 'offer_type', value: 'lab' },
]
</script>

<template>
  <div>
    <AppHeader />
    <RoleContent
      :title="t('roles.external.title')"
      :description="t('roles.external.description')"
      :search-placeholder="t('roles.external.searchPlaceholder')"
      :shortcuts="items"
      target-profile="company"
      :skip-validation="true"
    />
    <AppFooter />
  </div>
</template>

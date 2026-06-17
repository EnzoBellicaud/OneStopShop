import { computed } from 'vue'
import { i18n, setI18nLocale, SUPPORTED_LOCALES } from '../i18n/index.js'

const current = computed(() => i18n.global.locale.value)

function setLocale(code) {
  setI18nLocale(code)
}

export function useLocale() {
  return { current, languages: SUPPORTED_LOCALES, setLocale }
}

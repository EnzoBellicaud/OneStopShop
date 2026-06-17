import { createI18n } from 'vue-i18n'
import { messages } from './messages.js'

export const SUPPORTED_LOCALES = [
  { code: 'en', label: 'English' },
  { code: 'it', label: 'Italiano' },
  { code: 'fr', label: 'Francais' },
]

const FALLBACK_LOCALE = 'en'
const savedLocale = localStorage.getItem('locale')
const browserLocale = navigator.language?.slice(0, 2)

function resolveLocale(locale) {
  return SUPPORTED_LOCALES.some(item => item.code === locale) ? locale : FALLBACK_LOCALE
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: resolveLocale(savedLocale || browserLocale),
  fallbackLocale: FALLBACK_LOCALE,
  messages,
})

export function setI18nLocale(locale) {
  const resolved = resolveLocale(locale)
  i18n.global.locale.value = resolved
  document.documentElement.lang = resolved
  localStorage.setItem('locale', resolved)
  return resolved
}

setI18nLocale(i18n.global.locale.value)

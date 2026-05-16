import { ref } from 'vue'

const LANGUAGES = [
  { code: 'en', label: 'English' },
]

const current = ref(localStorage.getItem('locale') || 'en')

function setLocale(code) {
  current.value = code
  localStorage.setItem('locale', code)
}

export function useLocale() {
  return { current, languages: LANGUAGES, setLocale }
}

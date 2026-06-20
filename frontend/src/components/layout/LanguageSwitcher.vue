<!--
  LanguageSwitcher
  A self-contained, accessible language dropdown.

  - Globe icon (no flags), languages shown in their native label.
  - Reads/writes locale through useLocale() -> setI18nLocale(), which already
    persists to localStorage AND sets <html lang="..."> (see src/i18n/index.js).
  - Keyboard accessible: button toggles, Escape closes, click-outside closes.

  Usage: drop <LanguageSwitcher /> anywhere (it lives in AppHeader's .nav-right).
-->
<template>
  <div class="lang-picker" ref="rootRef">
    <button
      class="lang-btn"
      data-testid="lang-button"
      :aria-expanded="open"
      aria-haspopup="menu"
      :aria-label="t('nav.language')"
      @click="open = !open"
      @keydown.esc="open = false"
    >
      <!-- globe -->
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="8" cy="8" r="6.5" />
        <path d="M8 1.5C8 1.5 6 4.5 6 8s2 6.5 2 6.5M8 1.5C8 1.5 10 4.5 10 8s-2 6.5-2 6.5M1.5 8h13" />
        <path d="M2 5h12M2 11h12" />
      </svg>
      <span data-testid="lang-current">{{ currentLang.code.toUpperCase() }}</span>
      <svg class="chevron" :class="{ open }" viewBox="0 0 10 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">
        <path d="M1 1l4 4 4-4" />
      </svg>
    </button>

    <ul v-if="open" class="lang-dropdown" role="menu" data-testid="lang-menu">
      <li v-for="lang in languages" :key="lang.code" role="none">
        <button
          role="menuitemradio"
          :aria-checked="lang.code === current"
          :lang="lang.code"
          class="lang-option"
          :class="{ active: lang.code === current }"
          :data-testid="`lang-option-${lang.code}`"
          @click="select(lang.code)"
        >
          {{ lang.label }}
          <svg v-if="lang.code === current" viewBox="0 0 12 10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M1 5l3.5 3.5L11 1" />
          </svg>
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLocale } from '../../composables/useLocale.js'

const { t } = useI18n()
const { current, languages, setLocale } = useLocale()

const open = ref(false)
const rootRef = ref(null)

const currentLang = computed(
  () => languages.find(l => l.code === current.value) ?? languages[0]
)

function select(code) {
  setLocale(code) // persists to localStorage + updates <html lang> via i18n/index.js
  open.value = false
}

function onClickOutside(e) {
  if (rootRef.value && !rootRef.value.contains(e.target)) open.value = false
}

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))
</script>

<style scoped>
.lang-picker { position: relative; }

.lang-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border: 1px solid var(--border, #e4e4e0);
  border-radius: var(--r, 6px);
  background: transparent;
  color: var(--ink-soft);
  font-size: 12px;
  font-weight: 500;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  white-space: nowrap;
}
.lang-btn:hover { border-color: var(--ink-soft); color: var(--ink); }
.lang-btn svg:first-of-type { width: 14px; height: 14px; flex-shrink: 0; }

.chevron { width: 8px; height: 6px; flex-shrink: 0; transition: transform 0.2s; }
.chevron.open { transform: rotate(180deg); }

.lang-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 140px;
  margin: 0;
  padding: 0;
  list-style: none;
  background: var(--white, #fff);
  border: 1px solid var(--border, #e4e4e0);
  border-radius: var(--r, 6px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  z-index: 200;
  overflow: hidden;
}

.lang-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 9px 14px;
  background: none;
  border: none;
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  color: #111110;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s;
  gap: 8px;
}
.lang-option:hover { background: var(--surface, #fafaf8); }
.lang-option.active { font-weight: 500; }
.lang-option svg { width: 12px; height: 10px; flex-shrink: 0; color: var(--accent-mid, #9b2020); }
</style>

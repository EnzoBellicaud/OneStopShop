import { test, expect } from '@playwright/test'

/**
 * E2E: Language switching across pages.
 *
 * Covers project-tracker task "Test language switching across all pages":
 *  1. Visit homepage (landing) — assert it renders in English.
 *  2. Switch language to Italiano via the LanguageSwitcher.
 *  3. Assert the UI text changes (nav + hero) and <html lang> updates.
 *  4. Navigate to a second page (Forum) and verify the language persists.
 *  5. Reload — verify persistence survives a full page load (localStorage).
 *
 * Selectors rely on data-testid hooks added in LanguageSwitcher.vue plus the
 * i18n strings from src/i18n/messages.js (en + it).
 */

// Known translations we assert against (from src/i18n/messages.js)
const T = {
  en: { about: 'About', forum: 'Forum', heroTitle: 'Your gateway to university opportunities', footerPrivacy: 'Privacy policy' },
  it: { about: 'Chi siamo', forum: 'Forum', heroTitle: 'Il tuo accesso alle opportunita universitarie', footerPrivacy: 'Informativa sulla privacy' },
}

test.beforeEach(async ({ page }) => {
  // Start from a clean slate so the saved-locale assertions are meaningful.
  await page.goto('/')
  await page.evaluate(() => localStorage.removeItem('locale'))
  await page.reload()
})

test('switches language on the homepage and persists across pages', async ({ page }) => {
  await page.goto('/')

  // 1. Default render is English.
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  await expect(page.getByTestId('lang-current')).toHaveText('EN')
  await expect(page.getByRole('link', { name: T.en.about })).toBeVisible()

  // 2. Open the switcher and choose Italiano.
  await page.getByTestId('lang-button').click()
  await expect(page.getByTestId('lang-menu')).toBeVisible()
  await page.getByTestId('lang-option-it').click()

  // 3. UI text + <html lang> reflect Italian.
  await expect(page.locator('html')).toHaveAttribute('lang', 'it')
  await expect(page.getByTestId('lang-current')).toHaveText('IT')
  await expect(page.getByRole('link', { name: T.it.about })).toBeVisible()
  // English label should no longer be present.
  await expect(page.getByRole('link', { name: T.en.about })).toHaveCount(0)
  // Footer links are translated too.
  await expect(page.getByRole('link', { name: T.it.footerPrivacy })).toBeVisible()
  await expect(page.getByRole('link', { name: T.en.footerPrivacy })).toHaveCount(0)

  // Persisted to localStorage.
  await expect.poll(() => page.evaluate(() => localStorage.getItem('locale'))).toBe('it')

  // Landing section content is translated too (ProfileSelection).
  await expect(page.getByText('Scegli il tuo ruolo')).toBeVisible()
  await expect(page.getByText('Choose your role')).toHaveCount(0)

  // 4. Navigate to a second page — language must persist.
  await page.getByRole('link', { name: T.it.forum }).first().click()
  await expect(page).toHaveURL(/\/forum$/)
  await expect(page.locator('html')).toHaveAttribute('lang', 'it')
  await expect(page.getByTestId('lang-current')).toHaveText('IT')
  // Forum page chrome is translated (button + eyebrow).
  await expect(page.getByRole('button', { name: 'Fai una domanda' })).toBeVisible()

  // 5. Hard reload — survives a fresh page load.
  await page.reload()
  await expect(page.locator('html')).toHaveAttribute('lang', 'it')
  await expect(page.getByTestId('lang-current')).toHaveText('IT')
})

test('hero heading is translated on switch', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText(T.en.heroTitle)).toBeVisible()

  await page.getByTestId('lang-button').click()
  await page.getByTestId('lang-option-it').click()

  await expect(page.getByText(T.it.heroTitle)).toBeVisible()
})

import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config for the Vue frontend.
 *
 * baseURL points at the running app. The Docker `oss-vue` container already
 * serves it on http://localhost:5173, so by default we just reuse that.
 *
 * If you'd rather have Playwright boot its own dev server, uncomment the
 * `webServer` block below (and stop the container to free the port).
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'list',

  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],

  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:5173',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120_000,
  // },
})

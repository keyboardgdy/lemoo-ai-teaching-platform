import { defineConfig } from '@playwright/test'

const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  workers: 1,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    launchOptions: executablePath ? { executablePath } : undefined,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: process.env.CI ? 'off' : 'retain-on-failure',
  },
  webServer: [
    {
      command: 'uv run --project ../cloud lem-api',
      url: 'http://127.0.0.1:8000/health/ready',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: 'pnpm dev',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
})

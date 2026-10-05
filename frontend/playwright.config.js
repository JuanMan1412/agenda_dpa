import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  use: {
    baseURL: 'http://localhost:5174',
    browserName: 'chromium',
    launchOptions: {
      ...(process.platform === 'win32' ? { channel: 'chrome' } : {}),
    },
  },
  webServer: {
    command: 'npm run dev -- --host localhost',
    url: 'http://localhost:5174',
    reuseExistingServer: !process.env.CI,
  },
});

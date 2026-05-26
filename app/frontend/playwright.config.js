// PMD 前端 E2E 测试配置
// 约束对齐:CLAUDE.md "本地测试 / 截图输出" — 所有截图落 .cache/screenshots/
// design/12 §前端测试 — Playwright 用于视觉验收 + 关键流程回归

import { defineConfig, devices } from '@playwright/test'

const FRONTEND_URL = process.env.PMD_FRONTEND_URL || 'http://localhost:15173'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: '../../.cache/playwright-report', open: 'never' }],
  ],
  outputDir: '../../.cache/playwright-results',
  use: {
    baseURL: FRONTEND_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1440, height: 900 },
    locale: 'zh-CN',
    timezoneId: 'Asia/Shanghai',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})

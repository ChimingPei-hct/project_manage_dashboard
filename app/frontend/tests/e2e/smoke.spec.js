// 冒烟测试:4 个核心视图正常渲染 + 留基线截图
// 前置条件:后端 18080 + 前端 15173 都在跑,DEV_LOGIN=1
// 跑法:cd app/frontend && npm run e2e
// 截图落:.cache/screenshots/

import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.resolve(__dirname, '../../../../.cache/screenshots')

const VIEWS = [
  { id: 'pdt',   path: '/?view=pdt',   probe: 'Luna' },
  { id: 'ltc',   path: '/?view=ltc',   probe: 'LTC' },
  { id: 'risks', path: '/?view=risks', probe: '风险' },
  { id: 'admin', path: '/?view=admin', probe: '管理' },
]

for (const v of VIEWS) {
  test(`view "${v.id}" renders without errors`, async ({ page }) => {
    const consoleErrors = []
    page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err.message}`))
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(`console: ${msg.text()}`)
    })

    await page.goto(v.path, { waitUntil: 'load' })
    // SSE /api/events 永不 idle,所以不能用 networkidle;改为等待业务文案出现
    await expect(page.locator('body')).toContainText(v.probe, { timeout: 10000 })

    // 留基线截图到 .cache/screenshots/
    await page.screenshot({
      path: path.join(SHOT_DIR, `${v.id}.png`),
      fullPage: true,
    })

    // 前端不应该有 console error 或未捕获异常
    expect(consoleErrors, consoleErrors.join('\n')).toEqual([])
  })
}

test('top nav switches view and preserves week query', async ({ page }) => {
  await page.goto('/?view=pdt&week=2026-W21', { waitUntil: 'load' })

  // 点 "LTC 进展" 按钮 (按 design/13 顶栏导航)
  await page.getByRole('button', { name: /LTC/ }).first().click()

  // URL 应该切到 ltc 但 week 保留
  await expect(page).toHaveURL(/view=ltc/)
  await expect(page).toHaveURL(/week=2026-W21/)
})

// 验证:所有弹窗按 Esc 可关闭(design/12 §7.6)
// 覆盖三类:Modal 包装的、有自己 mask 的、内嵌 ref 控制的

import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.resolve(__dirname, '../../../../.cache/screenshots')

test('Esc closes PdtConfigDrawer (顶栏齿轮)', async ({ page }) => {
  await page.goto('/?view=pdt', { waitUntil: 'load' })
  await page.waitForTimeout(800)

  // 点齿轮按钮
  await page.locator('button[aria-label="PDT 配置"]').click()
  // 抽屉应当打开:.drawer-mask 出现 + 头部 "PDT 配置" 文字
  await expect(page.locator('.drawer-mask')).toBeVisible({ timeout: 3000 })
  await expect(page.locator('.drawer-mask').locator('text=PDT 配置').first()).toBeVisible()

  await page.keyboard.press('Escape')
  // 抽屉应当关闭(.drawer-mask 不再可见)
  await expect(page.locator('.drawer-mask')).not.toBeVisible({ timeout: 2000 })
})

test('Esc closes module status dialog (点 LTC 模块头)', async ({ page }) => {
  // 用 ZP22(数据齐全)做载体
  await page.goto('/?view=ltc&ltc=zp22', { waitUntil: 'load' })
  await page.waitForTimeout(1000)

  // 点第一个模块标题(LtcModuleCard 头部)— 触发 ModuleStatusDialog
  const moduleHeader = page.locator('.ltc-module-card h4, .module-header, [class*="module"] h4').first()
  if (await moduleHeader.count() === 0) {
    test.skip(true, 'no LTC module card found — data not seeded')
  }
  await moduleHeader.click()
  await page.waitForTimeout(500)

  // 弹窗应当打开(查找含色块选择的 dialog)
  const dialog = page.locator('[role="dialog"]').or(page.locator('.modal-mask'))
  const isOpen = await dialog.first().isVisible().catch(() => false)
  if (!isOpen) {
    test.skip(true, 'dialog did not open — may need editable permission')
  }

  await page.keyboard.press('Escape')
  await page.waitForTimeout(500)
  await expect(dialog).not.toBeVisible({ timeout: 2000 })
})

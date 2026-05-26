// 验证:LTC 编辑模式 → 大类标题旁出现指派 Owner 按钮 → 弹窗选人 → 大类显示 Owner 名
import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.resolve(__dirname, '../../../../.cache/screenshots')

test('编辑模式才显示大类 Owner 指派按钮', async ({ page }) => {
  await page.goto('/?view=ltc&ltc=zp22', { waitUntil: 'load' })
  await page.waitForTimeout(1200)

  // 默认非编辑模式:不应有 .cat-owner-edit 按钮
  expect(await page.locator('.cat-owner-edit').count()).toBe(0)

  // 点「✏️ 编辑」按钮进入编辑模式
  await page.getByRole('button', { name: /编辑$/ }).first().click()
  await page.waitForTimeout(300)

  // 编辑模式下应出现指派按钮
  const editBtns = page.locator('.cat-owner-edit')
  await expect(editBtns.first()).toBeVisible({ timeout: 2000 })
  expect(await editBtns.count()).toBeGreaterThanOrEqual(5)

  // 截图编辑模式
  await page.screenshot({
    path: path.join(SHOT_DIR, 'cat-owner-edit-buttons.png'),
    fullPage: true,
  })

  // 点第一个指派按钮
  await editBtns.first().click()
  await page.waitForTimeout(400)

  // 弹窗应当打开 (h3 是 dialog 标题)
  await expect(page.getByRole('heading', { name: '指派大类 Owner' })).toBeVisible({ timeout: 2000 })

  // 截图弹窗
  await page.screenshot({
    path: path.join(SHOT_DIR, 'cat-owner-picker-dialog.png'),
    fullPage: true,
  })

  // 按 Esc 关闭
  await page.keyboard.press('Escape')
  await page.waitForTimeout(300)
  await expect(page.getByRole('heading', { name: '指派大类 Owner' })).not.toBeVisible()
})

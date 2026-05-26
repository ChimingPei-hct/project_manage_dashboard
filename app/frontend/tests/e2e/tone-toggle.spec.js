// 验证:LTC 主页的「正常 / 预警 / 阻塞」三色 toggle 取代旧「看板/风险」
import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.resolve(__dirname, '../../../../.cache/screenshots')

test('LTC 顶部出现正常/预警/阻塞 三色 toggle', async ({ page }) => {
  await page.goto('/?view=ltc&ltc=zp22', { waitUntil: 'load' })
  await page.waitForTimeout(1200)

  // 旧的「看板 / 风险」chip 已下线
  expect(await page.getByRole('button', { name: /^看板$/ }).count()).toBe(0)
  expect(await page.getByRole('button', { name: /^风险$/ }).count()).toBe(0)

  // 新的三色 toggle 出现
  const greenBtn = page.locator('.tone-summary .chip.green')
  const yellowBtn = page.locator('.tone-summary .chip.yellow')
  const redBtn = page.locator('.tone-summary .chip.red')
  await expect(greenBtn).toBeVisible()
  await expect(yellowBtn).toBeVisible()
  await expect(redBtn).toBeVisible()

  await page.screenshot({ path: path.join(SHOT_DIR, 'ltc-tone-toggle-all-on.png'), fullPage: true })

  // 关掉「正常」:绿色 chip 变 off
  await greenBtn.click()
  await expect(greenBtn).toHaveClass(/off/)
  await page.waitForTimeout(200)
  await page.screenshot({ path: path.join(SHOT_DIR, 'ltc-tone-toggle-green-off.png'), fullPage: true })

  // 至少保留一个:再关「预警」「阻塞」,最后一个不能再关
  await yellowBtn.click()
  await expect(yellowBtn).toHaveClass(/off/)
  await redBtn.click()
  // 红色仍然 on(被规则拦截)
  await expect(redBtn).not.toHaveClass(/off/)

  await page.screenshot({ path: path.join(SHOT_DIR, 'ltc-tone-toggle-only-red.png'), fullPage: true })
})

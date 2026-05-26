// 验证:PDT 配置抽屉的 LTC 模板 tab 模块清单按 大类 → 模块 树形渲染
import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.resolve(__dirname, '../../../../.cache/screenshots')

test('PDT 配置 → LTC 模板 tab 按大类 → 模块树形展示', async ({ page }) => {
  await page.goto('/?view=pdt', { waitUntil: 'load' })
  await page.waitForTimeout(800)

  // 打开 PDT 配置抽屉
  await page.locator('button[aria-label="PDT 配置"]').click()
  await expect(page.locator('.drawer-mask')).toBeVisible({ timeout: 3000 })

  // 切到 LTC 模板 tab
  await page.getByRole('button', { name: 'LTC 模板' }).click()
  await page.waitForTimeout(500)

  // 树形结构断言:.tree-cat 至少 5 个(模板池 6 个大类)
  const cats = page.locator('.tree-cat')
  await expect(cats.first()).toBeVisible({ timeout: 3000 })
  expect(await cats.count()).toBeGreaterThanOrEqual(5)

  // 默认展开,看得到模块行
  const modRows = page.locator('.mod-row')
  expect(await modRows.count()).toBeGreaterThanOrEqual(10)

  // 截图
  await page.screenshot({
    path: path.join(SHOT_DIR, 'pdt-config-template-tree.png'),
    fullPage: true,
  })

  // 测折叠首个大类
  const firstCaret = page.locator('.tree-cat').first().locator('.caret-btn').first()
  await firstCaret.click()
  await page.waitForTimeout(300)

  const firstBody = page.locator('.tree-cat').first().locator('.cat-body')
  await expect(firstBody).not.toBeVisible()
})

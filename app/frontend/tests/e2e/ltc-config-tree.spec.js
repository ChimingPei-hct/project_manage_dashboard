// 验证:LTC 配置抽屉的模块清单按 大类 → 模块 → 子项 树形渲染
import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.resolve(__dirname, '../../../../.cache/screenshots')

test('LTC 配置抽屉模块清单按 大类 → 模块 树形展示', async ({ page }) => {
  // ZP22 数据齐全(18 模块 / 6 大类)
  await page.goto('/?view=ltc&ltc=zp22', { waitUntil: 'load' })
  await page.waitForTimeout(1200)

  // 点「⚙ LTC 配置」按钮
  await page.getByRole('button', { name: /LTC 配置/ }).click()
  await page.waitForTimeout(600)

  // 期望:模块清单容器有 .tree-cat × N(N >= 5,对应大类)
  const cats = page.locator('.tree-cat')
  await expect(cats.first()).toBeVisible({ timeout: 3000 })
  const catCount = await cats.count()
  expect(catCount).toBeGreaterThanOrEqual(5)

  // 默认大类展开,模块行可见
  const modRows = page.locator('.mod-row')
  expect(await modRows.count()).toBeGreaterThanOrEqual(10)

  // 截图
  await page.screenshot({
    path: path.join(SHOT_DIR, 'ltc-config-tree.png'),
    fullPage: true,
  })

  // 试试折叠第一个大类
  const firstCatBtn = page.locator('.cat-row').first()
  await firstCatBtn.click()
  await page.waitForTimeout(300)

  // 折叠后该大类下的模块行不可见
  // (因为整页可能仍有其他大类的 mod-row,所以只看第一个 cat-body 里的)
  const firstCatBody = page.locator('.tree-cat').first().locator('.cat-body')
  await expect(firstCatBody).not.toBeVisible()
})

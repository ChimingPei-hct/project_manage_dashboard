// 验证:LTC 编辑模式可新建大类(本 LTC 私有,scope=ltc)
import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.resolve(__dirname, '../../../../.cache/screenshots')
const API = process.env.PMD_BACKEND_URL || 'http://127.0.0.1:18080'

async function api(method, p, body) {
  const init = { method, headers: { 'Content-Type': 'application/json' }, credentials: 'include' }
  if (body !== undefined) init.body = JSON.stringify(body)
  const res = await fetch(`${API}${p}`, init)
  if (!res.ok) throw new Error(`${method} ${p} → ${res.status}: ${await res.text()}`)
  return res.headers.get('content-type')?.includes('json') ? res.json() : null
}

const LTC_ID = 'e2e_new_cat'

test('LTC 编辑模式可新建大类', async ({ page }) => {
  // 准备:用 API 建一个无大类的 LTC (不走 init-from-template)
  try { await api('DELETE', `/api/ltcs/${LTC_ID}`) } catch {}
  await api('POST', '/api/ltcs', { id: LTC_ID, name: 'E2E New Cat', order: 998 })

  await page.goto(`/?view=ltc&ltc=${LTC_ID}`, { waitUntil: 'load' })
  await page.waitForTimeout(1000)

  // 默认非编辑模式:看不到 + 新建大类 按钮
  expect(await page.locator('.new-cat-btn').count()).toBe(0)

  // 进入编辑模式
  await page.getByRole('button', { name: /编辑$/ }).first().click()
  await page.waitForTimeout(300)

  // 按钮应出现(空态卡片里 OR 顶部 bar — 此 LTC 无模块无大类,走空态分支)
  const btn = page.locator('.new-cat-btn').first()
  await expect(btn).toBeVisible({ timeout: 2000 })

  // 截图编辑模式
  await page.screenshot({ path: path.join(SHOT_DIR, 'ltc-new-cat-empty-state.png'), fullPage: true })

  // 点按钮 → 弹窗
  await btn.click()
  await page.waitForTimeout(300)
  await expect(page.getByRole('heading', { name: '新建大类' })).toBeVisible({ timeout: 2000 })

  // 输入名字 + 创建
  const input = page.locator('input[placeholder*="感知"]')
  await input.fill('感知')
  await page.getByRole('button', { name: '创建' }).click()
  await page.waitForTimeout(800)

  // 弹窗关闭,页面应出现该大类(标题"感知")
  await expect(page.getByRole('heading', { name: '新建大类' })).not.toBeVisible()
  // 截图建好后效果
  await page.screenshot({ path: path.join(SHOT_DIR, 'ltc-new-cat-created.png'), fullPage: true })
  await expect(page.locator('.cat-name').filter({ hasText: '感知' }).first()).toBeVisible({ timeout: 2000 })

  // 清理:删除我们刚建的大类(API 直接拿 list 反查 ID 删)
  const cats = await api('GET', '/api/categories')
  const myCats = cats.filter((c) => c.ltc_id === LTC_ID)
  for (const c of myCats) {
    await api('DELETE', `/api/categories/${c.id}`).catch(() => {})
  }
  await api('DELETE', `/api/ltcs/${LTC_ID}`).catch(() => {})
})

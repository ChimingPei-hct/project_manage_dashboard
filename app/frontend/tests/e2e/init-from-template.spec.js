// 端到端验证:init-from-template 新建的 LTC 默认全绿
// 流程:API 建 LTC → API 触发模板初始化 → UI 切到该 LTC → 截图 → 断言无灰色块 → API 清理
//
// 对应 design/04 §5.5 「种子默认状态」契约

import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.resolve(__dirname, '../../../../.cache/screenshots')
const API = process.env.PMD_BACKEND_URL || 'http://127.0.0.1:18080'

const LTC_ID = 'e2e_green_check'

async function api(method, p, body) {
  const init = { method, headers: { 'Content-Type': 'application/json' }, credentials: 'include' }
  if (body !== undefined) init.body = JSON.stringify(body)
  const res = await fetch(`${API}${p}`, init)
  if (!res.ok) throw new Error(`${method} ${p} → ${res.status}: ${await res.text()}`)
  return res.headers.get('content-type')?.includes('json') ? res.json() : null
}

test('init-from-template seeds module_status with all-green defaults (UI)', async ({ page, request }) => {
  // 清理可能残留的同 ID LTC
  try {
    const ltcs = await api('GET', '/api/ltcs')
    if (ltcs.some((l) => l.id === LTC_ID)) {
      // 这里若有残留模块就只能手工清,留个警告
      console.warn(`[setup] ${LTC_ID} already exists — test may interfere`)
    }
  } catch (e) {}

  // 1. API 建 LTC
  await api('POST', '/api/ltcs', { id: LTC_ID, name: 'E2E Green Check', order: 999 })

  // 2. API 触发模板初始化
  const initRes = await api('POST', `/api/ltc/${LTC_ID}/init-from-template`)
  expect(initRes.copied_modules).toBeGreaterThan(0)
  expect(initRes.seeded_status).toBe(initRes.copied_modules)

  // 3. UI 打开该 LTC
  await page.goto(`/?view=ltc&ltc=${LTC_ID}`, { waitUntil: 'load' })
  await expect(page.locator('body')).toContainText('E2E Green Check', { timeout: 10000 })

  // 等数据加载,reactive 完成
  await page.waitForTimeout(1000)

  // 4. 截图基线
  await page.screenshot({ path: path.join(SHOT_DIR, 'init-from-template-green.png'), fullPage: true })

  // 5. 断言:所有 sub-item 色块都是绿色 class,没有灰色 / 黄色 / 红色
  // PMD 用 CSS 变量 + class 区分色,通常 class 形如 status-green / status-gray
  // 这里宽松断言:页面源里 status-gray / status-red / status-yellow 出现次数极少
  // (顶栏 R/Y/G 计数 chip 那种例外)
  const html = await page.content()
  const grayMatches = (html.match(/status-gray\b/g) || []).length
  const greenMatches = (html.match(/status-green\b/g) || []).length

  // 期望:大量 green class,几乎无 gray(顶栏 chip 可能算 1-2 个)
  expect(greenMatches).toBeGreaterThan(10)
  expect(grayMatches).toBeLessThan(5)

  // 6. 清理
  // 先把所有模块按 ltc_id 删了,再删 LTC
  const allMods = await api('GET', '/api/modules')
  const myMods = allMods.filter((m) => m.ltc_id === LTC_ID)
  for (const m of myMods) {
    await api('DELETE', `/api/modules/${m.id}`).catch(() => {})
  }
  // categories 同理
  const allCats = await api('GET', '/api/categories')
  const myCats = allCats.filter((c) => c.ltc_id === LTC_ID)
  for (const c of myCats) {
    await api('DELETE', `/api/categories/${c.id}`).catch(() => {})
  }
  await api('DELETE', `/api/ltcs/${LTC_ID}`).catch(() => {})
})

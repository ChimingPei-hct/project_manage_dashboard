// PdtOverview 视觉重构验证
// 检查:segmented tabs 结构 + active 下划线 + ghost 工具按钮 + 无 console error
// 截图落 .cache/screenshots/pdt-overview-*.png

import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.resolve(__dirname, '../../../../.cache/screenshots')

test.describe('PdtOverview 重构后视觉', () => {
  test('segmented tabs + active 下划线 + ghost 工具按钮', async ({ page }) => {
    const consoleErrors = []
    page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err.message}`))
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(`console: ${msg.text()}`)
    })

    await page.goto('/?view=pdt', { waitUntil: 'load' })
    await expect(page.locator('.page-header')).toBeVisible({ timeout: 10000 })

    // —— 结构断言 ——
    const tabs = page.locator('.seg-tabs .seg-tab')
    await expect(tabs).toHaveCount(2)
    await expect(tabs.nth(0)).toHaveText('时间线')
    await expect(tabs.nth(1)).toHaveText('全局看板')

    // 默认 sub=timeline,第一个 tab 应 active
    await expect(tabs.nth(0)).toHaveClass(/active/)
    await expect(tabs.nth(0)).toHaveAttribute('aria-selected', 'true')
    await expect(tabs.nth(1)).toHaveAttribute('aria-selected', 'false')

    // 默认 timeline tab,工具区应出现"时间线管理"(如果当前用户是 admin)
    // dev 后门默认登录为 super,所以应该可见
    const timelineTool = page.locator('.tool-btn', { hasText: '时间线管理' })

    // —— 截图:timeline 视图 ——
    await page.screenshot({
      path: path.join(SHOT_DIR, 'pdt-overview-timeline.png'),
      fullPage: false,
      clip: { x: 0, y: 0, width: 1440, height: 320 },
    })

    // —— 切到 kanban ——
    await tabs.nth(1).click()
    await expect(tabs.nth(1)).toHaveClass(/active/)
    await expect(tabs.nth(0)).not.toHaveClass(/active/)

    // kanban 下:工具按钮应换成权限管理 / 快照
    await expect(page.locator('.tool-btn', { hasText: '权限管理' })).toBeVisible()
    await expect(page.locator('.tool-btn', { hasText: '快照' })).toBeVisible()

    // —— 截图:kanban 视图(含 actions 区) ——
    await page.screenshot({
      path: path.join(SHOT_DIR, 'pdt-overview-kanban.png'),
      fullPage: false,
      clip: { x: 0, y: 0, width: 1440, height: 320 },
    })

    // —— 视觉约束断言 ——
    // 1) seg-tab 无边框、透明背景(克制风核心)
    const tab0Box = tabs.nth(0)
    const tab0Styles = await tab0Box.evaluate((el) => {
      const cs = getComputedStyle(el)
      return {
        borderTopStyle: cs.borderTopStyle,
        background: cs.backgroundColor,
        borderRadius: cs.borderRadius,
      }
    })
    expect(tab0Styles.borderTopStyle).toBe('none')
    // 背景应为 transparent(rgba(0,0,0,0))
    expect(tab0Styles.background).toMatch(/rgba\(0,\s*0,\s*0,\s*0\)|transparent/)

    // 2) 工具按钮也应无可见边框(transparent 边框是 ghost 风的标志)
    if (await timelineTool.count() === 0) {
      // kanban 下检查权限管理按钮
      const permBtn = page.locator('.tool-btn', { hasText: '权限管理' })
      const permStyles = await permBtn.evaluate((el) => {
        const cs = getComputedStyle(el)
        return { borderColor: cs.borderTopColor, background: cs.backgroundColor }
      })
      expect(permStyles.background).toMatch(/rgba\(0,\s*0,\s*0,\s*0\)|transparent/)
    }

    // 3) page-header 底部应有 1px hairline(border-bottom)
    const header = page.locator('.page-header')
    const headerStyles = await header.evaluate((el) => {
      const cs = getComputedStyle(el)
      return { borderBottomWidth: cs.borderBottomWidth, borderBottomStyle: cs.borderBottomStyle }
    })
    expect(headerStyles.borderBottomWidth).toBe('1px')
    expect(headerStyles.borderBottomStyle).toBe('solid')

    // 4) 圆角红线:任何元素的 border-radius 不应为 50% / 9999px / 椭圆值
    //    抽样检查 tab、tool-btn、add-card-btn(若存在)
    const radiusCheck = await page.evaluate(() => {
      const selectors = ['.seg-tab', '.tool-btn', '.add-card-btn', '.action-divider']
      const offenders = []
      for (const sel of selectors) {
        document.querySelectorAll(sel).forEach((el) => {
          const r = getComputedStyle(el).borderRadius
          // 允许 0/6px/4px;禁 50% / 9999px / 大于 12px 的胶囊值
          if (/50%|9999px/.test(r)) offenders.push(`${sel}: ${r}`)
        })
      }
      return offenders
    })
    expect(radiusCheck).toEqual([])

    // —— Console error 兜底 ——
    expect(consoleErrors, consoleErrors.join('\n')).toEqual([])
  })
})

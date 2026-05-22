/**
 * v-tooltip 全局指令(参考 oversea_projects)。
 * 用法:<button v-tooltip="'点击切换 LTC'">...</button>
 * 文案规则见 design/12-前端实现约束.md §7.3。
 */

let tipEl = null

function ensureTip() {
  if (tipEl) return tipEl
  tipEl = document.createElement('div')
  tipEl.className = 'pmd-tooltip'
  tipEl.style.display = 'none'
  document.body.appendChild(tipEl)
  return tipEl
}

function show(el, text) {
  if (!text) return
  const t = ensureTip()
  t.textContent = text
  t.style.display = 'block'
  const r = el.getBoundingClientRect()
  // 默认显示在下方,边界保护
  const top = Math.min(r.bottom + 8, window.innerHeight - 60)
  const left = Math.max(8, Math.min(r.left, window.innerWidth - 300))
  t.style.top = `${top}px`
  t.style.left = `${left}px`
}

function hide() {
  if (tipEl) tipEl.style.display = 'none'
}

export const tooltipDirective = {
  mounted(el, binding) {
    el.__pmdTooltipShow = () => show(el, binding.value)
    el.__pmdTooltipHide = hide
    el.addEventListener('mouseenter', el.__pmdTooltipShow)
    el.addEventListener('mouseleave', el.__pmdTooltipHide)
    el.addEventListener('focus', el.__pmdTooltipShow)
    el.addEventListener('blur', el.__pmdTooltipHide)
  },
  updated(el, binding) {
    el.__pmdTooltipShow = () => show(el, binding.value)
  },
  beforeUnmount(el) {
    el.removeEventListener('mouseenter', el.__pmdTooltipShow)
    el.removeEventListener('mouseleave', el.__pmdTooltipHide)
    el.removeEventListener('focus', el.__pmdTooltipShow)
    el.removeEventListener('blur', el.__pmdTooltipHide)
    hide()
  },
}

/**
 * Focus trap composable — 弹窗焦点循环
 *
 * 用法:
 *   const boxRef = ref(null)
 *   useFocusTrap(boxRef, toRef(props, 'open'))
 *   // <div ref="boxRef" role="dialog">
 *
 * 打开时 Tab 在弹窗内循环,Shift+Tab 反向,关闭时恢复之前焦点。
 */
import { onBeforeUnmount, watch } from 'vue'

const FOCUSABLE = 'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'

export function useFocusTrap(elRef, isOpenRef) {
  let prevFocus = null

  watch(isOpenRef, (open) => {
    if (open) {
      prevFocus = document.activeElement
      requestAnimationFrame(() => {
        const el = elRef.value
        if (!el) return
        const focusable = el.querySelectorAll(FOCUSABLE)
        if (focusable.length) focusable[0].focus()
      })
    } else if (prevFocus && prevFocus.focus) {
      prevFocus.focus()
      prevFocus = null
    }
  })

  function onKeydown(e) {
    if (e.key !== 'Tab') return
    const el = elRef.value
    if (!el) return
    const focusable = [...el.querySelectorAll(FOCUSABLE)]
    if (!focusable.length) return
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault()
      last.focus()
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault()
      first.focus()
    }
  }

  watch(isOpenRef, (open, wasOpen) => {
    if (open && !wasOpen) {
      document.addEventListener('keydown', onKeydown)
    } else if (!open && wasOpen) {
      document.removeEventListener('keydown', onKeydown)
    }
  })

  onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
}
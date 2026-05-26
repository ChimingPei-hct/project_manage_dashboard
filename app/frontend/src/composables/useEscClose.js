/**
 * useEscClose — 弹窗 Esc 关闭统一处理
 *
 * 用法:
 *   const props = defineProps({ open: Boolean })
 *   const emit = defineEmits(['close'])
 *   useEscClose(toRef(props, 'open'), () => emit('close'))
 *
 * 设计:
 * - 全局只挂一个 keydown listener,模块加载时一次性挂上
 * - 用栈管理多层弹窗,Esc 只关闭最顶层(最后打开的)
 * - 组件 unmount 时自动清理栈,避免内存泄漏
 *
 * 约束对齐:design/12 §7.x 弹窗 Esc 关闭红线
 */

import { watch, onUnmounted } from 'vue'

const stack = []

function globalHandler(e) {
  if (e.key !== 'Escape') return
  const top = stack[stack.length - 1]
  if (!top) return
  e.stopPropagation()
  e.preventDefault()
  top()
}

if (typeof document !== 'undefined') {
  document.addEventListener('keydown', globalHandler)
}

export function useEscClose(isOpenRef, onClose) {
  const remove = () => {
    const i = stack.lastIndexOf(onClose)
    if (i >= 0) stack.splice(i, 1)
  }
  watch(
    isOpenRef,
    (v) => {
      remove() // 防重复 push
      if (v) stack.push(onClose)
    },
    { immediate: true }
  )
  onUnmounted(remove)
}

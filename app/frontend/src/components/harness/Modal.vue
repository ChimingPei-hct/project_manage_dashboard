<script setup>
import { toRef, ref } from 'vue'
import { useEscClose } from '../../composables/useEscClose.js'
import { useFocusTrap } from '../../composables/useFocusTrap.js'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  width: { type: String, default: '720px' },
})
const emit = defineEmits(['close'])

useEscClose(toRef(props, 'open'), () => emit('close'))

const modalBoxRef = ref(null)
useFocusTrap(modalBoxRef, toRef(props, 'open'))

function onBackdrop(e) {
  if (e.target === e.currentTarget) emit('close')
}
</script>

<template>
  <div v-if="open" class="modal-mask" @click="onBackdrop">
    <div ref="modalBoxRef" class="modal-box" role="dialog" :aria-label="title" :style="{ maxWidth: width }">
      <header class="modal-head">
        <h3>{{ title }}</h3>
        <button class="close" @click="emit('close')" v-tooltip="'关闭弹窗'" aria-label="关闭弹窗">×</button>
      </header>
      <div class="modal-body">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-mask {
  position: fixed; inset: 0; background: rgba(30, 27, 75, 0.55);
  display: flex; align-items: flex-start; justify-content: center;
  z-index: 9000; backdrop-filter: blur(6px);
  padding: 60px 16px 24px;
  overflow-y: auto;
  animation: mask-fade-in var(--duration-normal) var(--ease-out) both;
}
@keyframes mask-fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.modal-box {
  background: var(--panel); border-radius: var(--radius-lg);
  width: 100%;
  box-shadow: var(--shadow-dialog);
  display: flex; flex-direction: column;
  max-height: calc(100vh - 84px);
  border: 1px solid var(--border);
  animation: box-slide-up var(--duration-slow) var(--ease-out) both;
}
@keyframes box-slide-up {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid var(--border-subtle);
  position: relative;
}
.modal-head::after {
  content: '';
  position: absolute;
  bottom: -1px; left: 24px;
  width: 40px; height: 2px;
  background: var(--gradient-brand);
  border-radius: 1px;
}
.modal-head h3 { margin: 0; font-size: var(--fs-lg); font-weight: 600; font-family: var(--font-serif); color: var(--text-strong); letter-spacing: -0.01em; }
.close {
  border: none; background: transparent; font-size: 24px; line-height: 1;
  padding: 0 8px; cursor: pointer; color: var(--text-muted);
  border-radius: var(--radius-sm); transition: all var(--transition);
}
.close:hover { color: var(--text-strong); background: var(--panel-soft); }
.close:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--bg), 0 0 0 4px var(--accent-ring);
}
.modal-body { padding: 20px 24px 24px; overflow-y: auto; }
@media (prefers-reduced-motion: reduce) {
  .modal-mask, .modal-box { animation: none; }
}
</style>

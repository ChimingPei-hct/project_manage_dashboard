<script setup>
defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  width: { type: String, default: '720px' },
})
const emit = defineEmits(['close'])

function onBackdrop(e) {
  if (e.target === e.currentTarget) emit('close')
}
</script>

<template>
  <div v-if="open" class="modal-mask" @click="onBackdrop">
    <div class="modal-box" role="dialog" :style="{ maxWidth: width }">
      <header class="modal-head">
        <h3>{{ title }}</h3>
        <button class="close" @click="emit('close')" v-tooltip="'关闭弹窗'">×</button>
      </header>
      <div class="modal-body">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-mask {
  position: fixed; inset: 0; background: rgba(15,23,42,0.42);
  display: flex; align-items: flex-start; justify-content: center;
  z-index: 9000; backdrop-filter: blur(2px);
  padding: 60px 16px 24px;
  overflow-y: auto;
}
.modal-box {
  background: var(--panel); border-radius: var(--radius);
  width: 100%;
  box-shadow: var(--shadow-lg);
  display: flex; flex-direction: column;
  max-height: calc(100vh - 84px);
}
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
}
.modal-head h3 { margin: 0; font-size: 15px; font-weight: 700; }
.close {
  border: none; background: transparent; font-size: 22px; line-height: 1;
  padding: 0 6px; cursor: pointer; color: var(--text-muted);
}
.close:hover { color: var(--accent); }
.modal-body { padding: 16px 20px 20px; overflow-y: auto; }
</style>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '确认操作' },
  body: { type: String, default: '此操作不可撤销,确定继续?' },
  confirmText: { type: String, default: '确定' },
  cancelText: { type: String, default: '取消' },
  danger: { type: Boolean, default: true },
})
const emit = defineEmits(['confirm', 'cancel'])

function onBackdrop(e) {
  if (e.target === e.currentTarget) emit('cancel')
}
</script>

<template>
  <div v-if="open" class="confirm-mask" @click="onBackdrop">
    <div class="confirm-box" role="dialog">
      <h3>{{ title }}</h3>
      <p>{{ body }}</p>
      <div class="actions">
        <button @click="emit('cancel')" v-tooltip="'取消操作并关闭对话框'">{{ cancelText }}</button>
        <button :class="danger ? 'danger' : 'primary'" @click="emit('confirm')" v-tooltip="'确认执行此操作'">
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.confirm-mask {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.36);
  display: flex; align-items: center; justify-content: center;
  z-index: 9000;
}
.confirm-box {
  background: var(--panel); border-radius: var(--radius);
  padding: 20px 24px; min-width: 360px; max-width: 480px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
}
h3 { margin: 0 0 12px; font-size: 16px; }
p { margin: 0 0 20px; color: var(--text-muted); line-height: 1.6; white-space: pre-wrap; }
.actions { display: flex; gap: 8px; justify-content: flex-end; }
button.danger { background: var(--status-red); color: #fff; border-color: var(--status-red); }
button.danger:hover { opacity: 0.9; }
</style>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  color: { type: String, default: 'gray' }, // green / yellow / red / gray
  note: { type: String, default: '' },
  label: { type: String, default: '' },
  ownerName: { type: String, default: '' },
  editable: { type: Boolean, default: false },
  expanded: { type: Boolean, default: false },
  size: { type: String, default: 'md' }, // sm / md / lg
})

const emit = defineEmits(['edit'])

const bg = computed(() => `var(--status-${props.color})`)
const tip = computed(() => {
  const parts = []
  if (props.label) parts.push(props.label)
  if (props.ownerName) parts.push(`Owner: ${props.ownerName}`)
  if (props.note) parts.push(props.note)
  return parts.join(' · ')
})
</script>

<template>
  <div class="status-cell" :class="[`size-${size}`, { editable, expanded }]">
    <div
      class="dot"
      :style="{ background: bg }"
      v-tooltip="tip"
      @click="editable && emit('edit')"
    >
      <span v-if="label" class="label">{{ label }}</span>
    </div>
    <div v-if="expanded && note" class="note">{{ note }}</div>
  </div>
</template>

<style scoped>
.status-cell { display: inline-flex; flex-direction: column; gap: 4px; }
.dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
  padding: 4px 8px;
  min-width: 24px;
  min-height: 22px;
  cursor: default;
  user-select: none;
}
.size-sm .dot { min-width: 18px; min-height: 16px; padding: 2px 6px; font-size: 11px; }
.size-lg .dot { min-width: 60px; min-height: 36px; padding: 8px 14px; font-size: 14px; }
.editable .dot { cursor: pointer; }
.editable .dot:hover { outline: 2px solid var(--accent); outline-offset: 1px; }
.label { white-space: nowrap; }
.note {
  font-size: 12px;
  color: var(--text-muted);
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px 8px;
  max-width: 280px;
  line-height: 1.5;
  white-space: pre-wrap;
}
</style>

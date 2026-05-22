<script setup>
/**
 * HTML5 draggable 列表抽象。
 * props.items: 数组,每项需有 id 字段
 * 父组件用默认插槽渲染每行内容
 * 拖拽结束后 emit('reorder', newItems)
 */
import { ref } from 'vue'

const props = defineProps({
  items: { type: Array, required: true },
  disabled: { type: Boolean, default: false },
  itemKey: { type: String, default: 'id' },
})
const emit = defineEmits(['reorder'])

const dragIdx = ref(-1)
const overIdx = ref(-1)

function onDragStart(i, e) {
  if (props.disabled) return
  dragIdx.value = i
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(i))
}
function onDragOver(i, e) {
  if (props.disabled || dragIdx.value < 0) return
  e.preventDefault()
  overIdx.value = i
}
function onDragLeave(i) {
  if (overIdx.value === i) overIdx.value = -1
}
function onDrop(i, e) {
  if (props.disabled || dragIdx.value < 0) return
  e.preventDefault()
  const from = dragIdx.value
  const to = i
  dragIdx.value = -1
  overIdx.value = -1
  if (from === to) return
  const next = [...props.items]
  const [moved] = next.splice(from, 1)
  next.splice(to, 0, moved)
  emit('reorder', next)
}
function onDragEnd() {
  dragIdx.value = -1
  overIdx.value = -1
}
</script>

<template>
  <div class="draggable-list">
    <div
      v-for="(item, i) in items"
      :key="item[itemKey]"
      class="row"
      :class="{ dragging: dragIdx === i, over: overIdx === i }"
      :draggable="!disabled"
      @dragstart="e => onDragStart(i, e)"
      @dragover="e => onDragOver(i, e)"
      @dragleave="onDragLeave(i)"
      @drop="e => onDrop(i, e)"
      @dragend="onDragEnd"
    >
      <span v-if="!disabled" class="handle" v-tooltip="'拖拽改变顺序'">⋮⋮</span>
      <div class="content">
        <slot :item="item" :index="i" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.draggable-list { display: flex; flex-direction: column; gap: 4px; }
.row {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 8px; background: var(--panel);
  border: 1px solid var(--border); border-radius: var(--radius);
  transition: background 0.12s;
}
.row.dragging { opacity: 0.4; }
.row.over { background: #eef2ff; border-color: var(--accent); }
.handle { color: var(--text-muted); cursor: grab; user-select: none; font-size: 14px; }
.handle:active { cursor: grabbing; }
.content { flex: 1; min-width: 0; }
</style>

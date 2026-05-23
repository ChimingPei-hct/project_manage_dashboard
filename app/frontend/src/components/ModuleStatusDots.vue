<script setup>
/* 模块卡右上角的"三圆点"摘要,沿用截图设计:R/Y/G 三个色块表示该模块的整体灯 + 风险灯 */
import { computed } from 'vue'

const props = defineProps({
  color: { type: String, default: 'gray' },
  editable: { type: Boolean, default: false },
  note: { type: String, default: '' },
})

const emit = defineEmits(['edit'])

/* 三圆点:位置 0=green, 1=yellow, 2=red。当前色对应那格"亮",其他为浅灰背景 */
const tones = ['green', 'yellow', 'red']
const tip = computed(() => {
  if (props.color === 'gray') return '未填报'
  const map = { red: 'Delay/Block', yellow: '进展预警', green: '进展正常' }
  return map[props.color] || props.color
})
</script>

<template>
  <button
    type="button"
    class="dots"
    :class="{ editable }"
    v-tooltip="(tip) + (note ? ' · ' + note : (editable ? ' · 点击编辑' : ''))"
    :disabled="!editable"
    @click="editable && emit('edit')"
  >
    <span
      v-for="t in tones"
      :key="t"
      class="dot"
      :class="[t, { active: color === t }]"
    ></span>
  </button>
</template>

<style scoped>
.dots {
  display: inline-flex;
  gap: 3px;
  background: transparent;
  border: none;
  padding: 2px;
  border-radius: var(--radius);
}
.dots.editable { cursor: pointer; }
.dots.editable:hover { background: var(--accent-soft); }
.dots:disabled { cursor: default; }
.dot {
  width: 11px;
  height: 11px;
  border-radius: var(--radius-sm);
  background: #e5e9f0;
  border: 1px solid rgba(0,0,0,0.04);
  transition: transform 120ms;
}
.dot.active.green { background: var(--status-green); border-color: rgba(0,0,0,0.05); box-shadow: 0 0 0 1px rgba(22,163,74,0.30); }
.dot.active.yellow { background: var(--status-yellow); border-color: rgba(0,0,0,0.05); box-shadow: 0 0 0 1px rgba(217,119,6,0.30); }
.dot.active.red { background: var(--status-red); border-color: rgba(0,0,0,0.05); box-shadow: 0 0 0 1px rgba(220,38,38,0.30); }
.dots.editable:hover .dot.active { transform: scale(1.08); }
</style>

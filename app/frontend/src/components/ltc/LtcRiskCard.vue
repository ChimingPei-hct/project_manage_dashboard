<script setup>
import { computed } from 'vue'
import { risksOf, subRiskOf } from '../../composables/useStatusHelpers.js'

/**
 * LTC 风险版模块卡。只显示非绿态的内容:
 * - 模块整体若非绿,展示 module_color + risks[]/risk_note
 * - 子项中非绿者,展示 sub_items_risk[sid]
 * 全绿模块由父组件过滤掉,本组件假定至少有一项非绿。
 */
const props = defineProps({
  module: { type: Object, required: true },
  entry: { type: Object, default: () => ({}) },
  canEdit: { type: Boolean, default: false },
})
const emit = defineEmits(['edit-sub'])

const moduleColor = computed(() => props.entry?.module_color || 'gray')
const moduleRisks = computed(() => risksOf(props.entry))
const subs = computed(() => (props.module.sub_items || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0)))
const subColors = computed(() => props.entry?.sub_items_color || {})

const riskySubs = computed(() => subs.value
  .filter(s => {
    const c = subColors.value[s.id]
    return c && c !== 'green'
  })
  .map(s => ({
    sub: s,
    color: subColors.value[s.id],
    text: subRiskOf(props.entry, s.id),
  }))
)

const moduleHasRisk = computed(() => moduleColor.value !== 'green' && moduleColor.value !== 'gray')

function tipOf(sub) {
  if (!props.canEdit) return `${sub.name} · 查看(无编辑权限)`
  return `编辑「${sub.name}」状态与风险说明`
}
</script>

<template>
  <div class="risk-card">
    <header class="title" :class="`tone-${moduleColor}`">
      <span class="name">{{ module.name }}</span>
      <span class="color-tag" :class="`tone-${moduleColor}`">{{ moduleColor === 'red' ? '红' : moduleColor === 'yellow' ? '黄' : '' }}</span>
    </header>
    <div class="body">
      <div v-if="moduleHasRisk && moduleRisks.length" class="mod-risks">
        <div v-for="(r, i) in moduleRisks" :key="`m-${i}`" class="risk-line" :class="`tone-${r.severity}`">
          <span class="dot"></span>
          <span class="txt">{{ r.text }}</span>
        </div>
      </div>
      <div v-if="riskySubs.length" class="sub-risks">
        <div
          v-for="item in riskySubs"
          :key="item.sub.id"
          class="sub-line"
        >
          <button
            type="button"
            class="chip"
            :class="`tone-${item.color}`"
            :disabled="!canEdit"
            v-tooltip="tipOf(item.sub)"
            @click="emit('edit-sub', item.sub)"
          >{{ item.sub.name }}</button>
          <span class="sub-text">{{ item.text || '（未填写风险说明）' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.risk-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--panel);
  overflow: hidden;
}
.title {
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 10px;
  font-size: 12.5px; font-weight: 700;
  border-bottom: 1px solid var(--border-subtle);
}
.title.tone-yellow { background: var(--status-yellow-bg); color: var(--status-yellow); }
.title.tone-red { background: var(--status-red-bg); color: var(--status-red); }
.title.tone-green { background: var(--status-green-bg); color: var(--status-green); }
.title.tone-gray { background: var(--panel-soft); color: var(--text-muted); }
.color-tag { font-size: 11px; font-weight: 600; }

.body { padding: 6px 8px 8px; display: flex; flex-direction: column; gap: 6px; }

.mod-risks { display: flex; flex-direction: column; gap: 4px; }
.risk-line {
  display: flex; gap: 6px; align-items: flex-start;
  font-size: 11.5px; line-height: 1.4;
  padding: 4px 6px;
  border-radius: var(--radius);
  background: var(--panel-soft);
}
.risk-line.tone-red { background: var(--status-red-bg); color: var(--status-red); }
.risk-line.tone-yellow { background: var(--status-yellow-bg); color: var(--status-yellow); }
.risk-line .dot {
  width: 6px; height: 6px; border-radius: 2px;
  display: inline-block; margin-top: 5px; flex-shrink: 0;
}
.risk-line.tone-red .dot { background: var(--status-red); }
.risk-line.tone-yellow .dot { background: var(--status-yellow); }
.risk-line .txt { word-break: break-word; }

.sub-risks { display: flex; flex-direction: column; gap: 4px; }
.sub-line {
  display: grid; grid-template-columns: minmax(80px, auto) 1fr;
  gap: 6px; align-items: start;
}
.chip {
  font-size: 11px; line-height: 1.2;
  padding: 3px 6px;
  border-radius: var(--radius);
  border: 1px solid transparent;
  cursor: pointer; font-weight: 500;
  white-space: nowrap; align-self: start;
}
.chip:disabled { cursor: default; }
.chip.tone-red { background: var(--status-red); color: #fff; border-color: var(--status-red); }
.chip.tone-yellow { background: var(--status-yellow); color: #fff; border-color: var(--status-yellow); }
.chip:not(:disabled):hover { filter: brightness(0.92); }
.sub-text {
  font-size: 11.5px; line-height: 1.4;
  color: var(--text); word-break: break-word;
}
</style>

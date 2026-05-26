<script setup>
import { computed, onMounted } from 'vue'
import { useContactCache, displayName } from '../../composables/useContactCache.js'
import { risksOf, subRiskOf } from '../../composables/useStatusHelpers.js'

/**
 * LTC 看板模块卡(三级结构第二层)。
 * 单卡同时展示:
 *   - 模块名色块 + 一排子项色块(按 visibleTones 过滤)
 *   - 非绿子项的风险说明(只显示 yellow/red 中可见的)
 * visibleTones = { green, yellow, red };gray 跟随 green。
 * 卡片自身在所有内容都被过滤时自动 v-if 隐藏。
 * 与 PDT 看板的 ModuleCardGrid 独立(详见 CLAUDE.md 红线)。
 */
const props = defineProps({
  module: { type: Object, required: true },
  entry: { type: Object, default: () => ({}) },
  canEdit: { type: Boolean, default: false },
  visibleTones: { type: Object, default: () => ({ green: true, yellow: true, red: true }) },
})
const emit = defineEmits(['edit-sub', 'add-sub', 'edit-module-status', 'edit-module-structure'])

const { contacts, ensureContacts } = useContactCache()
onMounted(() => { ensureContacts() })

function toneKey(color) {
  if (color === 'gray') return 'green' // gray 视作"正常"分组
  return color
}
function toneVisible(color) {
  return !!props.visibleTones[toneKey(color)]
}

const moduleColor = computed(() => props.entry?.module_color || 'gray')
const subColors = computed(() => props.entry?.sub_items_color || {})
const subs = computed(() => (props.module.sub_items || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0)))
const ownerName = computed(() => {
  const oid = props.module?.owner_open_id
  if (!oid) return ''
  const u = (contacts.value || []).find(x => x.open_id === oid)
  return u?.name || displayName(oid) || ''
})

const visibleSubs = computed(() => subs.value.filter(s => toneVisible(subColors.value[s.id] || 'gray')))
const moduleTitleVisible = computed(() => toneVisible(moduleColor.value))

/* 卡片可见性:模块色或任一子项色在可见集合内,或处于编辑模式(允许加子项) */
const cardVisible = computed(() => {
  if (moduleTitleVisible.value) return true
  if (visibleSubs.value.length > 0) return true
  if (props.canEdit) return true // 编辑态保留卡片用于 + 子项 / ⚙
  return false
})

/* 风险段:模块级 + 子项级,均按可见色过滤 */
const moduleRisks = computed(() => {
  if (moduleColor.value === 'green' || moduleColor.value === 'gray') return []
  if (!toneVisible(moduleColor.value)) return []
  return risksOf(props.entry)
})
const riskySubs = computed(() => subs.value
  .filter(s => {
    const c = subColors.value[s.id]
    return (c === 'red' || c === 'yellow') && toneVisible(c)
  })
  .map(s => ({ sub: s, color: subColors.value[s.id], text: subRiskOf(props.entry, s.id) }))
)
const hasRiskContent = computed(() => moduleRisks.value.length > 0 || riskySubs.value.length > 0)

function colorOf(sid) { return subColors.value[sid] || 'gray' }
function tipOf(sub) {
  if (!props.canEdit) return `${sub.name} · 查看状态(无编辑权限)`
  return `编辑「${sub.name}」的状态灯与风险说明`
}
</script>

<template>
  <div v-if="cardVisible" class="ltc-mod-card">
    <header
      class="title"
      :class="[`tone-${moduleColor}`, { clickable: canEdit, dimmed: !moduleTitleVisible }]"
      v-tooltip="canEdit ? '点击编辑本模块的整体状态色与风险说明' : ''"
      @click="canEdit && emit('edit-module-status')"
    >
      <span class="name">{{ module.name }}</span>
      <span
        v-if="ownerName"
        class="owner"
        v-tooltip="'模块负责人'"
      >Owner · {{ ownerName }}</span>
      <button
        v-if="canEdit"
        type="button"
        class="cog"
        v-tooltip="'编辑模块结构(改名、Owner、子项、KPI)'"
        @click.stop="emit('edit-module-structure')"
      >⚙</button>
    </header>
    <!-- chips:按 tone 过滤 -->
    <div class="chips">
      <button
        v-for="s in visibleSubs"
        :key="s.id"
        type="button"
        class="chip"
        :class="`tone-${colorOf(s.id)}`"
        :disabled="!canEdit"
        v-tooltip="tipOf(s)"
        @click="emit('edit-sub', s)"
      >{{ s.name }}</button>
      <button
        v-if="canEdit"
        type="button"
        class="chip tile-add"
        v-tooltip="'为本模块新增一个子项色块'"
        @click="emit('add-sub')"
      >+ 子项</button>
      <span v-if="!visibleSubs.length && !canEdit" class="empty">
        {{ subs.length ? '当前过滤下无子项' : '无子项' }}
      </span>
    </div>

    <!-- 风险段:仅当有可见的 yellow/red 内容时出现 -->
    <template v-if="hasRiskContent">
      <div class="seg-divider"></div>
      <div class="risk-body">
        <div v-if="moduleRisks.length" class="mod-risks">
          <div
            v-for="(r, i) in moduleRisks"
            :key="`m-${i}`"
            class="risk-line"
            :class="`tone-${r.severity}`"
            v-tooltip="'模块级风险说明'"
          >
            <span class="dot"></span>
            <span class="txt">{{ r.text }}</span>
          </div>
        </div>
        <div v-if="riskySubs.length" class="sub-risks">
          <div v-for="item in riskySubs" :key="item.sub.id" class="sub-line">
            <button
              type="button"
              class="chip"
              :class="`tone-${item.color}`"
              :disabled="!canEdit"
              v-tooltip="tipOf(item.sub)"
              @click="emit('edit-sub', item.sub)"
            >{{ item.sub.name }}</button>
            <span class="sub-text">{{ item.text || '(未填写风险说明)' }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.ltc-mod-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--panel);
  overflow: hidden;
  display: flex; flex-direction: column;
}
.title {
  display: flex; justify-content: space-between; align-items: center;
  gap: 8px;
  padding: 5px 10px;
  font-size: 12.5px; font-weight: 700;
  color: var(--text);
  border-bottom: 1px solid var(--border-subtle);
}
.title .name { flex: 1 1 auto; min-width: 0; }
.title .owner {
  flex: 0 0 auto;
  font-size: 11px; font-weight: 500;
  color: var(--text-muted);
  padding: 1px 6px;
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.55);
  white-space: nowrap;
}
.title.tone-green .owner,
.title.tone-yellow .owner,
.title.tone-red .owner {
  color: rgba(0, 0, 0, 0.62);
  background: rgba(255, 255, 255, 0.7);
}
.title.tone-gray .owner { background: var(--panel); }
.title.tone-green { background: var(--status-green-bg); color: var(--status-green); }
.title.tone-yellow { background: var(--status-yellow-bg); color: var(--status-yellow); }
.title.tone-red { background: var(--status-red-bg); color: var(--status-red); }
.title.tone-gray { background: var(--panel-soft); color: var(--text-muted); }
.title.clickable { cursor: pointer; }
.title.clickable:hover { filter: brightness(0.96); }
.title.dimmed { opacity: 0.45; }
.cog {
  flex: 0 0 auto;
  border: none; background: transparent;
  font-size: 13px; line-height: 1;
  padding: 1px 4px; border-radius: var(--radius);
  cursor: pointer; color: inherit;
  opacity: 0.55;
}
.cog:hover { opacity: 1; background: rgba(255,255,255,0.55); }
.title.tone-gray .cog:hover { background: var(--panel); }

.chips {
  display: flex; flex-wrap: wrap; gap: 4px;
  padding: 6px 8px 8px;
}
.chip {
  font-size: 11.5px; line-height: 1.2;
  padding: 3px 7px;
  border-radius: var(--radius);
  border: 1px solid transparent;
  cursor: pointer;
  font-weight: 500;
  white-space: nowrap;
}
.chip:disabled { cursor: default; }
.chip.tone-green { background: var(--status-green); color: #fff; border-color: var(--status-green); }
.chip.tone-yellow { background: var(--status-yellow); color: #fff; border-color: var(--status-yellow); }
.chip.tone-red { background: var(--status-red); color: #fff; border-color: var(--status-red); }
.chip.tone-gray { background: var(--panel-soft); color: var(--text-muted); border-color: var(--border); }
.chip:not(:disabled):hover { filter: brightness(0.92); }
.chip.tile-add {
  background: transparent; color: var(--text-muted);
  border: 1px dashed var(--border); font-weight: 500;
}
.chip.tile-add:hover { color: var(--accent); border-color: var(--accent); background: var(--panel-soft); filter: none; }

.empty {
  font-size: 11.5px; color: var(--text-dim);
  padding: 6px 10px 8px;
}

/* 风险段 */
.seg-divider {
  height: 1px; margin: 0 10px;
  background: var(--border-subtle);
}
.risk-body {
  display: flex; flex-direction: column; gap: 6px;
  padding: 8px 8px;
}
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
.sub-line .chip { align-self: start; }
.sub-text {
  font-size: 11.5px; line-height: 1.4;
  color: var(--text); word-break: break-word;
}
</style>

<script setup>
import { computed, onMounted } from 'vue'
import { useContactCache, displayName } from '../../composables/useContactCache.js'
import { risksOf, subRiskOf } from '../../composables/useStatusHelpers.js'
import OwnerChip from '../OwnerChip.vue'

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
      <OwnerChip
        v-if="module?.owner_open_id"
        class="owner"
        :open-id="module.owner_open_id"
        :size="20"
        v-tooltip="'模块负责人'"
      />
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
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  display: flex; flex-direction: column;
  transition: box-shadow var(--transition), transform var(--transition), border-color var(--transition);
}
.ltc-mod-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-strong);
  transform: translateY(-1px);
}
.title {
  position: relative;
  display: flex; justify-content: space-between; align-items: center;
  gap: 10px;
  padding: 9px 12px 9px 18px;
  border-bottom: 1px solid var(--border-subtle);
  transition: background var(--transition), filter var(--transition);
}
.title .name {
  flex: 1 1 auto; min-width: 0;
  font-family: var(--font-serif);
  font-size: 15.5px; font-weight: 600;
  color: var(--text-strong);
  letter-spacing: 0.04em;
  line-height: 1.3;
}
.title::before {
  content: '';
  position: absolute;
  left: 8px; top: 50%; transform: translateY(-50%);
  width: 4px; height: 60%;
  border-radius: 2px;
  background: var(--text-dim);
  transition: background var(--transition);
}
.title .name { flex: 1 1 auto; min-width: 0; }
.title .owner {
  flex: 0 0 auto;
  padding: 2px 7px 2px 4px;
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.92);
  white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}
/* OwnerChip 在 tone 背景上的内部样式微调:头像 + 姓名都要清晰 */
.title .owner :deep(.owner-chip) { font-size: 12px; color: var(--text-strong); }
.title .owner :deep(.name) {
  font-family: var(--font-sans);
  color: var(--text-strong); font-weight: 600;
  letter-spacing: 0.03em;
}
.title .owner :deep(.avatar) { border-color: var(--border); }
.title.tone-gray .owner { background: var(--panel); }
.title.tone-green {
  background: var(--status-green-bg-strong);
  color: var(--text-strong);
  border-bottom-color: var(--status-green-border-strong);
}
.title.tone-green::before { background: var(--status-green); }
.title.tone-yellow {
  background: var(--status-yellow-bg-strong);
  color: var(--text-strong);
  border-bottom-color: var(--status-yellow-border-strong);
}
.title.tone-yellow::before { background: var(--status-yellow); }
.title.tone-red {
  background: var(--status-red-bg-strong);
  color: var(--text-strong);
  border-bottom-color: var(--status-red-border-strong);
}
.title.tone-red::before { background: var(--status-red); }
.title.tone-gray { background: var(--panel-soft); color: var(--text-muted); }
.title.clickable { cursor: pointer; }
.title.clickable:hover { filter: brightness(0.95); }
.title.dimmed { opacity: 0.42; }
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
  display: flex; flex-wrap: wrap; gap: 6px;
  padding: 8px 10px 10px;
}
.chip {
  font-family: var(--font-sans);
  font-size: 13px; line-height: 1.2;
  padding: 5px 12px;
  border-radius: var(--radius);
  border: 1px solid transparent;
  cursor: pointer;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: 0.06em;
  font-feature-settings: 'tnum', 'cv11', 'ss01';
  transition:
    filter var(--transition),
    transform 140ms cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow var(--transition);
}
.chip:disabled { cursor: default; }
.chip.tone-green {
  background: var(--status-green); color: #fff; border-color: var(--status-green);
  box-shadow: 0 1px 2px rgba(22, 163, 74, 0.25);
}
.chip.tone-yellow {
  background: var(--status-yellow); color: #fff; border-color: var(--status-yellow);
  box-shadow: 0 1px 2px rgba(217, 119, 6, 0.25);
}
.chip.tone-red {
  background: var(--status-red); color: #fff; border-color: var(--status-red);
  box-shadow: 0 1px 2px rgba(220, 38, 38, 0.25);
}
.chip.tone-gray { background: var(--panel-soft); color: var(--text-muted); border-color: var(--border); }
.chip:not(:disabled):hover {
  filter: brightness(1.06);
  transform: translateY(-1px) scale(1.03);
  box-shadow: var(--shadow-md);
}
.chip:not(:disabled):active { transform: translateY(0) scale(0.98); }
.chip.tile-add {
  background: transparent; color: var(--text-muted);
  border: 1px dashed var(--border); font-weight: 500;
  box-shadow: none;
}
.chip.tile-add:hover {
  color: var(--accent); border-color: var(--accent);
  background: var(--accent-soft); filter: none;
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

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
  padding: 10px 10px 12px;
}
.mod-risks { display: flex; flex-direction: column; gap: 6px; }
.risk-line {
  display: flex; gap: 9px; align-items: flex-start;
  font-family: var(--font-sans);
  font-size: 13.5px; line-height: 1.65;
  letter-spacing: 0.03em;
  padding: 9px 12px;
  border-radius: var(--radius);
  background: var(--panel-soft);
  border-left: 3px solid transparent;
  font-weight: 500;
  color: var(--text-strong);
  transition: transform var(--transition), box-shadow var(--transition), filter var(--transition);
}
.risk-line.tone-red {
  background: var(--status-red-bg-strong);
  color: var(--text-strong);
  border-left-color: var(--status-red);
  font-weight: 600;
}
.risk-line.tone-yellow {
  background: var(--status-yellow-bg-strong);
  color: var(--text-strong);
  border-left-color: var(--status-yellow);
  font-weight: 600;
}
.risk-line:hover {
  transform: translateX(2px);
  filter: brightness(0.98);
  box-shadow: var(--shadow-sm);
}
.risk-line .dot {
  width: 6px; height: 6px; border-radius: 2px;
  display: inline-block; margin-top: 5px; flex-shrink: 0;
}
.risk-line.tone-red .dot { background: var(--status-red); }
.risk-line.tone-yellow .dot { background: var(--status-yellow); }
.risk-line .txt { word-break: break-word; }

.sub-risks { display: flex; flex-direction: column; gap: 6px; }
.sub-line {
  display: grid; grid-template-columns: minmax(80px, auto) 1fr;
  gap: 10px; align-items: start;
}
.sub-line .chip { align-self: start; }
.sub-text {
  font-family: var(--font-sans);
  font-size: 13px; line-height: 1.6;
  letter-spacing: 0.025em;
  color: var(--text-strong); word-break: break-word;
  padding-top: 3px;
}
</style>

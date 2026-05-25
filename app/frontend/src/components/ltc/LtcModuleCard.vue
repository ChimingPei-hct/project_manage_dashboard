<script setup>
import { computed, onMounted } from 'vue'
import { useContactCache, displayName } from '../../composables/useContactCache.js'

/**
 * LTC 看板模块卡(三级结构第二层)。
 * 模块名背景按 module_color 上色;头部右上角显示 Owner(对齐设计稿);
 * 下方一排子项色块;点击子项触发 emit('edit-sub', sub)。
 * 与 PDT 看板的 ModuleCardGrid 独立(详见 CLAUDE.md 红线)。
 */
const props = defineProps({
  module: { type: Object, required: true },
  entry: { type: Object, default: () => ({}) },
  canEdit: { type: Boolean, default: false },
})
const emit = defineEmits(['edit-sub', 'add-sub', 'edit-module-status', 'edit-module-structure'])

const { contacts, ensureContacts } = useContactCache()
onMounted(() => { ensureContacts() })

const moduleColor = computed(() => props.entry?.module_color || 'gray')
const subColors = computed(() => props.entry?.sub_items_color || {})
const subs = computed(() => (props.module.sub_items || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0)))
const riskNote = computed(() => (props.entry?.risk_note || '').trim())
const ownerName = computed(() => {
  const oid = props.module?.owner_open_id
  if (!oid) return ''
  const u = (contacts.value || []).find(x => x.open_id === oid)
  return u?.name || displayName(oid) || ''
})

function colorOf(sid) { return subColors.value[sid] || 'gray' }
function tipOf(sub) {
  if (!props.canEdit) return `${sub.name} · 查看状态(无编辑权限)`
  return `编辑「${sub.name}」的状态灯与风险说明`
}
</script>

<template>
  <div class="ltc-mod-card">
    <header
      class="title"
      :class="[`tone-${moduleColor}`, { clickable: canEdit }]"
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
    <p v-if="riskNote" class="risk-line" v-tooltip="'模块级风险说明'">{{ riskNote }}</p>
    <div class="chips">
      <button
        v-for="s in subs"
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
      <span v-if="!subs.length && !canEdit" class="empty">无子项</span>
    </div>
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

.risk-line {
  margin: 0;
  padding: 4px 10px 0;
  font-size: 11.5px; line-height: 1.35;
  color: var(--text-muted);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

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
</style>

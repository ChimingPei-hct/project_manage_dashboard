<script setup>
import { computed, ref } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'

const props = defineProps({
  selected: { type: String, default: '' }, // node id like "pdt", "pdt:milestones", "ltc:xxx", "module:yyy", "people", "snapshots"
})
const emit = defineEmits(['select'])

const { pdt, ltcs, modules } = useDashboard()

const expanded = ref({ pdt: true, ltcs: true })
function toggle(key) { expanded.value[key] = !expanded.value[key] }

const pdtModules = computed(() => (modules.value || []).filter(m => m.scope === 'pdt'))
function ltcModules(ltcId) {
  return (modules.value || []).filter(m => m.scope === 'ltc' && m.ltc_id === ltcId)
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
}

function pick(id) { emit('select', id) }
</script>

<template>
  <div class="config-tree">
    <!-- PDT 信息 -->
    <div class="branch">
      <div
        class="node root"
        :class="{ active: selected === 'pdt' }"
        @click="pick('pdt')"
      >
        <span class="caret" @click.stop="toggle('pdt')">{{ expanded.pdt ? '▾' : '▸' }}</span>
        <span class="icon">📦</span>
        <span class="lbl">{{ pdt?.name || 'PDT 配置' }}</span>
        <span class="badge">PDT</span>
      </div>
      <div v-show="expanded.pdt" class="children">
        <div
          class="node sub"
          :class="{ active: selected === 'pdt:milestones' }"
          @click="pick('pdt:milestones')"
        >
          <span class="icon">🏁</span>
          <span class="lbl">里程碑</span>
          <span class="count">{{ (pdt?.milestones || []).length }}</span>
        </div>
        <div
          class="node sub"
          :class="{ active: selected === 'pdt:overview' }"
          @click="pick('pdt:overview')"
        >
          <span class="icon">📋</span>
          <span class="lbl">总览卡片</span>
          <span class="count">{{ pdtModules.length }}</span>
        </div>
      </div>
    </div>

    <!-- LTC 列表 -->
    <div class="branch">
      <div
        class="node root"
        :class="{ active: selected === 'ltcs' }"
        @click="pick('ltcs')"
      >
        <span class="caret" @click.stop="toggle('ltcs')">{{ expanded.ltcs ? '▾' : '▸' }}</span>
        <span class="icon">🚗</span>
        <span class="lbl">LTC 子项目</span>
        <span class="badge">{{ (ltcs || []).length }}</span>
      </div>
      <div v-show="expanded.ltcs" class="children">
        <div v-for="l in ltcs" :key="l.id" class="ltc-branch">
          <div
            class="node sub"
            :class="{ active: selected === 'ltc:' + l.id }"
            @click="pick('ltc:' + l.id)"
          >
            <span class="caret" @click.stop="toggle('ltc:' + l.id)">
              {{ expanded['ltc:' + l.id] ? '▾' : '▸' }}
            </span>
            <span class="icon">📁</span>
            <span class="lbl">{{ l.name }}</span>
            <span class="count">{{ ltcModules(l.id).length }}</span>
          </div>
          <div v-show="expanded['ltc:' + l.id]" class="children deep">
            <div
              v-for="m in ltcModules(l.id)"
              :key="m.id"
              class="node leaf"
              :class="{ active: selected === 'module:' + m.id }"
              @click="pick('module:' + m.id)"
            >
              <span class="icon">▪</span>
              <span class="lbl">{{ m.group ? `[${m.group}] ` : '' }}{{ m.name }}</span>
              <span class="count">{{ (m.sub_items || []).length }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- People -->
    <div class="branch">
      <div
        class="node root"
        :class="{ active: selected === 'people' }"
        @click="pick('people')"
      >
        <span class="icon">👥</span>
        <span class="lbl">人员与角色</span>
      </div>
    </div>

    <!-- Snapshots -->
    <div class="branch">
      <div
        class="node root"
        :class="{ active: selected === 'snapshots' }"
        @click="pick('snapshots')"
      >
        <span class="icon">📸</span>
        <span class="lbl">周快照</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.config-tree {
  font-size: 13px;
  padding: 6px 0;
  user-select: none;
}
.branch { margin-bottom: 4px; }
.node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background var(--transition);
  position: relative;
}
.node:hover { background: var(--accent-soft); }
.node.active { background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.node.active::before {
  content: '';
  position: absolute;
  left: 0; top: 4px; bottom: 4px;
  width: 3px;
  background: var(--accent);
  border-radius: var(--radius);
}
.node.root { font-weight: 600; padding: 7px 10px; }
.node.sub { padding-left: 22px; font-size: 12.5px; }
.node.leaf { padding-left: 38px; font-size: 12px; color: var(--text-muted); }
.node.leaf.active { color: var(--accent); }
.caret {
  width: 12px;
  text-align: center;
  color: var(--text-dim);
  font-size: 9px;
  cursor: pointer;
}
.icon { font-size: 13px; }
.lbl {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.badge {
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius);
  font-weight: 600;
  letter-spacing: 0.3px;
}
.count {
  font-size: 10px;
  color: var(--text-dim);
  background: var(--panel-soft);
  padding: 0 6px;
  border-radius: var(--radius);
  font-variant-numeric: tabular-nums;
}
.children { padding-left: 4px; }
.children.deep { padding-left: 6px; }
</style>

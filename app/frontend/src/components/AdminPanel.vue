<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth.js'
import { useDashboard } from '../composables/useDashboard.js'
import ConfigTree from './admin/ConfigTree.vue'
import PdtBaseDrawer from './admin/PdtBaseDrawer.vue'
import MilestonesDrawer from './admin/MilestonesDrawer.vue'
import OverviewCardsDrawer from './admin/OverviewCardsDrawer.vue'
import LtcsListDrawer from './admin/LtcsListDrawer.vue'
import LtcDrawer from './admin/LtcDrawer.vue'
import ModuleDrawer from './admin/ModuleDrawer.vue'
import AdminUsers from './admin/AdminUsers.vue'
import SnapshotPanel from './admin/SnapshotPanel.vue'

const { me } = useAuth()
const { modules } = useDashboard()

/* URL 同步:?view=admin&node=pdt|pdt:milestones|ltc:xxx|module:yyy|people|snapshots */
const initial = new URLSearchParams(window.location.search).get('node') || 'pdt'
const selected = ref(initial)

function setNode(node) {
  selected.value = node
  const url = new URL(window.location)
  url.searchParams.set('view', 'admin')
  url.searchParams.set('node', node)
  window.history.replaceState({}, '', url)
}

/* 当模块被删除时,自动回到父 LTC 或 LTCs 列表 */
function handleModuleDeleted() {
  const parts = selected.value.split(':')
  if (parts[0] === 'module') {
    /* 找原模块的 ltc_id */
    setNode('ltcs')
  }
}
function handleLtcDeleted() { setNode('ltcs') }

const canEnter = computed(() => me.value && (me.value.is_super || me.value.is_pdt_admin))
</script>

<template>
  <div v-if="!canEnter" class="no-perm">
    <h2>需要 PDT Admin 或以上权限才能访问管理后台</h2>
    <p>请联系超级管理员授予权限。</p>
  </div>
  <div v-else class="admin-shell">
    <aside class="tree-pane">
      <header class="tree-head">
        <span class="title">配置导航</span>
        <span class="hint" v-tooltip="'点击节点切换右侧编辑区'">ⓘ</span>
      </header>
      <ConfigTree :selected="selected" @select="setNode" />
    </aside>

    <main class="drawer-pane">
      <PdtBaseDrawer v-if="selected === 'pdt'" />
      <MilestonesDrawer v-else-if="selected === 'pdt:milestones'" />
      <OverviewCardsDrawer
        v-else-if="selected === 'pdt:overview'"
        @pick-module="id => setNode('module:' + id)"
      />
      <LtcsListDrawer
        v-else-if="selected === 'ltcs'"
        @pick-ltc="id => setNode('ltc:' + id)"
      />
      <LtcDrawer
        v-else-if="selected.startsWith('ltc:')"
        :key="selected"
        :ltc-id="selected.slice(4)"
        @pick-module="id => setNode('module:' + id)"
        @deleted="handleLtcDeleted"
      />
      <ModuleDrawer
        v-else-if="selected.startsWith('module:')"
        :key="selected"
        :module-id="selected.slice(7)"
        @deleted="handleModuleDeleted"
      />
      <div v-else-if="selected === 'people'" class="legacy-wrap">
        <header class="dh">
          <div>
            <div class="crumb">人员与角色</div>
            <h2>角色绑定</h2>
          </div>
        </header>
        <AdminUsers />
      </div>
      <div v-else-if="selected === 'snapshots'" class="legacy-wrap">
        <header class="dh">
          <div>
            <div class="crumb">周快照</div>
            <h2>历史周与定时冻结</h2>
          </div>
        </header>
        <SnapshotPanel />
      </div>
      <div v-else class="empty">请在左侧选择一个节点开始编辑</div>
    </main>
  </div>
</template>

<style scoped>
.no-perm { padding: 80px 24px; text-align: center; color: var(--text-muted); }
.no-perm h2 { color: var(--text); font-size: 18px; }

.admin-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  padding: 16px 24px 24px;
  min-height: calc(100vh - 80px);
}

.tree-pane {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px;
  height: fit-content;
  position: sticky;
  top: 80px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}
.tree-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 10px 8px;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 6px;
}
.tree-head .title { font-size: 12px; font-weight: 700; color: var(--text); letter-spacing: 0.4px; }
.tree-head .hint { font-size: 11px; color: var(--text-dim); cursor: help; }

.drawer-pane {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  box-shadow: var(--shadow-sm);
  min-height: 400px;
}
.legacy-wrap { display: flex; flex-direction: column; gap: 16px; }
.legacy-wrap .dh { padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.legacy-wrap .crumb { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
.legacy-wrap h2 { margin: 0; font-size: 18px; font-weight: 700; }
.empty { padding: 80px; text-align: center; color: var(--text-muted); }
</style>

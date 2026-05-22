<script setup>
import { ref } from 'vue'
const tab = ref('pdt')
const tabs = [
  { key: 'pdt', label: 'PDT 信息' },
  { key: 'ltcs', label: 'LTC 列表' },
  { key: 'modules', label: '模块管理' },
  { key: 'admins', label: '人员管理' },
  { key: 'snapshots', label: '快照管理' },
]
</script>

<template>
  <div class="admin">
    <h1>管理后台</h1>
    <p class="hint">骨架阶段:tab 占位,后续阶段实现 CRUD(详见 design/13 §6)。</p>
    <div class="tabs">
      <button
        v-for="t in tabs"
        :key="t.key"
        :class="{ primary: tab === t.key }"
        v-tooltip="`切换到「${t.label}」管理`"
        @click="tab = t.key"
      >{{ t.label }}</button>
    </div>
    <div class="panel">
      <div v-if="tab === 'pdt'">TBD · PDT 信息编辑(name/description/milestones)</div>
      <div v-else-if="tab === 'ltcs'">TBD · LTC 增删改、归档、重排</div>
      <div v-else-if="tab === 'modules'">TBD · 模块树编辑、Owner 绑定、kpi/sub_items 维护</div>
      <div v-else-if="tab === 'admins'">TBD · super_admins / pdt_admins / ltc_admins 维护</div>
      <div v-else-if="tab === 'snapshots'">TBD · 手动 freeze 本周、历史快照列表</div>
    </div>
  </div>
</template>

<style scoped>
.admin { padding: 16px 24px; }
h1 { margin: 0 0 8px; font-size: 20px; }
.hint { color: var(--text-muted); margin: 0 0 16px; }
.tabs { display: flex; gap: 8px; margin-bottom: 12px; }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; min-height: 240px; color: var(--text-muted); }
</style>

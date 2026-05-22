<script setup>
import { ref, computed, watch } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi, newId } from '../../composables/useAdminApi.js'
import DraggableList from '../harness/DraggableList.vue'
import ConfirmDialog from '../harness/ConfirmDialog.vue'
import UserSearchInput from '../UserSearchInput.vue'

const { ltcs, modules, refresh } = useDashboard()

// 当前作用域:'pdt' 或具体 ltc_id
const scopeKey = ref('pdt')
const ltcOptions = computed(() => ltcs.value || [])

const visible = computed(() => {
  const list = modules.value || []
  if (scopeKey.value === 'pdt') return list.filter(m => m.scope === 'pdt')
  return list.filter(m => m.scope === 'ltc' && m.ltc_id === scopeKey.value)
})
const sorted = computed(() => [...visible.value].sort((a, b) => (a.order ?? 0) - (b.order ?? 0)))

// 新增模块草稿
const draft = ref({ name: '', group: '' })
const adding = ref(false)
async function add() {
  if (!draft.value.name.trim() || !draft.value.group.trim()) return
  adding.value = true
  try {
    const body = {
      id: newId(),
      scope: scopeKey.value === 'pdt' ? 'pdt' : 'ltc',
      ltc_id: scopeKey.value === 'pdt' ? null : scopeKey.value,
      group: draft.value.group.trim(),
      name: draft.value.name.trim(),
      owner_open_id: null,
      kpi_fields: [],
      sub_items: [],
    }
    await adminApi.createModule(body)
    draft.value = { name: '', group: '' }
    await refresh()
  } finally { adding.value = false }
}

// 编辑单个字段(立即提交)
async function patch(m, field, value) {
  if (m[field] === value) return
  await adminApi.updateModule(m.id, { [field]: value })
  await refresh()
}

// sub_items 编辑
async function addSub(m) {
  const sub = { id: newId().slice(0, 12), name: '新子项', order: (m.sub_items?.length || 0) + 1 }
  await adminApi.updateModule(m.id, { sub_items: [...(m.sub_items || []), sub] })
  await refresh()
}
async function patchSub(m, idx, patchObj) {
  const next = [...(m.sub_items || [])]
  next[idx] = { ...next[idx], ...patchObj }
  await adminApi.updateModule(m.id, { sub_items: next })
  await refresh()
}
async function removeSub(m, idx) {
  const next = (m.sub_items || []).filter((_, i) => i !== idx)
  await adminApi.updateModule(m.id, { sub_items: next })
  await refresh()
}

// kpi_fields 编辑
async function addKpi(m) {
  const kpi = { key: `k${(m.kpi_fields?.length || 0) + 1}`, label: '新指标', hint: '' }
  await adminApi.updateModule(m.id, { kpi_fields: [...(m.kpi_fields || []), kpi] })
  await refresh()
}
async function patchKpi(m, idx, patchObj) {
  const next = [...(m.kpi_fields || [])]
  next[idx] = { ...next[idx], ...patchObj }
  await adminApi.updateModule(m.id, { kpi_fields: next })
  await refresh()
}
async function removeKpi(m, idx) {
  const next = (m.kpi_fields || []).filter((_, i) => i !== idx)
  await adminApi.updateModule(m.id, { kpi_fields: next })
  await refresh()
}

// 排序
async function onReorder(next) {
  await Promise.all(next.map((it, i) => adminApi.updateModule(it.id, { order: i + 1 })))
  await refresh()
}

// Owner 选择(UserSearchInput)
function ownerName(m, allUsers) {
  if (!m.owner_open_id) return ''
  const u = (allUsers || []).find(x => x.open_id === m.owner_open_id)
  return u?.name || m.owner_open_id
}

// 删除
const confirmState = ref({ open: false, target: null })
function askDelete(m) {
  confirmState.value = { open: true, target: m }
}
async function doDelete() {
  const m = confirmState.value.target
  confirmState.value = { open: false, target: null }
  if (!m) return
  await adminApi.deleteModule(m.id)
  await refresh()
}
</script>

<template>
  <div class="module-editor">
    <div class="scope-bar">
      <label v-tooltip="'选择要管理的模块作用域:PDT 级或某个 LTC 子项目'">作用域:</label>
      <select v-model="scopeKey">
        <option value="pdt">PDT 级总览</option>
        <option v-for="l in ltcOptions" :key="l.id" :value="l.id">LTC: {{ l.name }}</option>
      </select>
    </div>

    <div class="add-row">
      <input v-model="draft.group" placeholder="分组(如:质量、感知算法、硬件和底软)" />
      <input v-model="draft.name" placeholder="模块名" @keyup.enter="add" />
      <button class="primary" :disabled="adding || !draft.name.trim() || !draft.group.trim()" @click="add"
              v-tooltip="'在当前作用域下创建一个新模块,id 自动生成'">+ 添加模块</button>
    </div>

    <div v-if="!sorted.length" class="empty">当前作用域下还没有模块。</div>
    <DraggableList v-else :items="sorted" item-key="id" @reorder="onReorder">
      <template #default="{ item: m }">
        <div class="module-card">
          <header>
            <span class="grp">
              <span class="lbl">分组</span>
              <input :value="m.group" @change="e => patch(m, 'group', e.target.value)" />
            </span>
            <span class="nam">
              <span class="lbl">名称</span>
              <input :value="m.name" @change="e => patch(m, 'name', e.target.value)" />
            </span>
            <span class="owner">
              <span class="lbl">Owner</span>
              <UserSearchInput
                :modelValue="ownerName(m, [])"
                placeholder="搜索人员姓名…"
                @select="u => patch(m, 'owner_open_id', u.open_id)"
              />
              <button v-if="m.owner_open_id" class="clear" @click="patch(m, 'owner_open_id', null)"
                      v-tooltip="'清除 Owner 绑定'">×</button>
            </span>
            <span class="actions">
              <button class="danger" @click="askDelete(m)" v-tooltip="'删除此模块(状态同步删除,历史保留)'">删除</button>
            </span>
          </header>

          <div class="sub-section">
            <div class="sub-head">
              <span>子项色块 sub_items</span>
              <button @click="addSub(m)" v-tooltip="'添加一个子项色块(LTC 级模块常用)'">+ 子项</button>
            </div>
            <div v-if="!m.sub_items?.length" class="sub-empty">无子项,整模块只用一个状态灯。</div>
            <div v-else class="sub-rows">
              <div v-for="(s, i) in m.sub_items" :key="s.id" class="sub-row">
                <input :value="s.name" @change="e => patchSub(m, i, { name: e.target.value })" placeholder="子项名" />
                <span class="sid">id: {{ s.id }}</span>
                <button class="danger" @click="removeSub(m, i)" v-tooltip="'删除此子项(状态同步清除)'">×</button>
              </div>
            </div>
          </div>

          <div class="sub-section">
            <div class="sub-head">
              <span>KPI 字段 kpi_fields</span>
              <button @click="addKpi(m)" v-tooltip="'添加一个 KPI 字段(PDT 级卡片常用)'">+ KPI</button>
            </div>
            <div v-if="!m.kpi_fields?.length" class="sub-empty">无 KPI。</div>
            <div v-else class="sub-rows">
              <div v-for="(k, i) in m.kpi_fields" :key="k.key" class="kpi-row">
                <input :value="k.key" @change="e => patchKpi(m, i, { key: e.target.value })" placeholder="key" />
                <input :value="k.label" @change="e => patchKpi(m, i, { label: e.target.value })" placeholder="显示名" />
                <input :value="k.hint || ''" @change="e => patchKpi(m, i, { hint: e.target.value })" placeholder="提示(可选)" />
                <button class="danger" @click="removeKpi(m, i)" v-tooltip="'删除此 KPI'">×</button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </DraggableList>

    <ConfirmDialog
      :open="confirmState.open"
      title="删除模块"
      :body="`确认删除模块「${confirmState.target?.name}」?\n本模块的当前态会被清除,历史流(module_updates)保留。`"
      confirm-text="删除"
      @confirm="doDelete"
      @cancel="confirmState = { open: false, target: null }"
    />
  </div>
</template>

<style scoped>
.module-editor { max-width: 1100px; }
.scope-bar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; }
.scope-bar select { min-width: 240px; }
.add-row { display: grid; grid-template-columns: 1fr 1fr auto; gap: 8px; margin-bottom: 12px; }
.empty { color: var(--text-muted); padding: 16px; background: var(--panel); border: 1px dashed var(--border); border-radius: var(--radius); }

.module-card { width: 100%; }
.module-card header { display: grid; grid-template-columns: 1.4fr 1.6fr 2fr auto; gap: 12px; align-items: center; margin-bottom: 8px; }
.lbl { font-size: 11px; color: var(--text-muted); display: block; margin-bottom: 2px; }
.module-card input { width: 100%; }
.owner { display: flex; gap: 4px; align-items: flex-end; flex-direction: column; align-items: stretch; }
.owner :deep(.user-search-wrap) { display: inline-block; flex: 1; }
.clear { font-size: 12px; padding: 0 6px; }

.sub-section { margin-top: 8px; padding: 8px; background: #fafafa; border-radius: var(--radius); }
.sub-head { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
.sub-empty { font-size: 12px; color: var(--text-muted); padding: 4px 0; }
.sub-rows { display: flex; flex-direction: column; gap: 4px; }
.sub-row { display: grid; grid-template-columns: 1fr 160px auto; gap: 6px; align-items: center; }
.kpi-row { display: grid; grid-template-columns: 1fr 1.2fr 1.6fr auto; gap: 6px; align-items: center; }
.sid { font-size: 11px; color: var(--text-muted); font-family: ui-monospace, monospace; }
.danger { background: var(--status-red); color: #fff; border-color: var(--status-red); }
</style>

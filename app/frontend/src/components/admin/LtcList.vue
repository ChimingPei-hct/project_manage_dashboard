<script setup>
import { ref, computed } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi, newId } from '../../composables/useAdminApi.js'
import DraggableList from '../harness/DraggableList.vue'
import ConfirmDialog from '../harness/ConfirmDialog.vue'

const { ltcs, modules, refresh } = useDashboard()

const showArchived = ref(false)
const list = computed(() => {
  const rows = ltcs.value || []
  return [...rows].sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
})

const newName = ref('')
const adding = ref(false)
async function add() {
  if (!newName.value.trim()) return
  adding.value = true
  try {
    await adminApi.createLtc({ id: newId(), name: newName.value.trim() })
    newName.value = ''
    await refresh()
  } finally { adding.value = false }
}

async function rename(item, newValue) {
  if (newValue === item.name) return
  await adminApi.updateLtc(item.id, { name: newValue })
  await refresh()
}

async function toggleArchive(item) {
  await adminApi.updateLtc(item.id, { archived: !item.archived })
  await refresh()
}

async function onReorder(next) {
  // 重写 order 字段(1-based)并批量提交
  await Promise.all(next.map((it, i) => adminApi.updateLtc(it.id, { order: i + 1 })))
  await refresh()
}

const confirmState = ref({ open: false, target: null })
function askDelete(item) {
  const hasModules = (modules.value || []).some(m => m.ltc_id === item.id)
  if (hasModules) {
    alert(`LTC「${item.name}」下还有模块,请先删除/迁移模块后再删此 LTC,或选择归档。`)
    return
  }
  confirmState.value = { open: true, target: item }
}
async function doDelete() {
  const it = confirmState.value.target
  confirmState.value = { open: false, target: null }
  if (!it) return
  await adminApi.deleteLtc(it.id)
  await refresh()
}
</script>

<template>
  <div class="ltc-list">
    <div class="head">
      <h3>LTC 子项目列表</h3>
      <label v-tooltip="'显示已归档的 LTC'">
        <input type="checkbox" v-model="showArchived" /> 显示已归档
      </label>
    </div>

    <div class="add-row">
      <input v-model="newName" placeholder="新 LTC 名称(回车提交)" @keyup.enter="add" />
      <button class="primary" :disabled="adding || !newName.trim()" @click="add"
              v-tooltip="'创建一个新的 LTC 子项目,id 自动生成'">+ 添加 LTC</button>
    </div>

    <div v-if="!list.length" class="empty">暂无 LTC,先在上方添加一个。</div>
    <DraggableList v-else :items="list.filter(l => showArchived || !l.archived)" item-key="id" @reorder="onReorder">
      <template #default="{ item }">
        <div class="ltc-row" :class="{ archived: item.archived }">
          <span class="name">
            <input
              :value="item.name"
              @change="e => rename(item, e.target.value)"
              v-tooltip="'修改 LTC 名称(失焦或回车提交)'"
            />
          </span>
          <span class="meta">order: {{ item.order }} · {{ item.archived ? '已归档' : '活跃' }}</span>
          <span class="actions">
            <button @click="toggleArchive(item)"
                    v-tooltip="item.archived ? '取消归档,重新显示在看板' : '归档此 LTC(保留数据,不在默认视图显示)'">
              {{ item.archived ? '取消归档' : '归档' }}
            </button>
            <button class="danger" @click="askDelete(item)"
                    v-tooltip="'永久删除(仅当 LTC 下无模块时可用,否则请先归档)'">删除</button>
          </span>
        </div>
      </template>
    </DraggableList>

    <ConfirmDialog
      :open="confirmState.open"
      title="删除 LTC"
      :body="`确认删除 LTC「${confirmState.target?.name}」?\n该操作不可撤销,但所有 module_updates 历史会保留。`"
      confirm-text="删除"
      @confirm="doDelete"
      @cancel="confirmState = { open: false, target: null }"
    />
  </div>
</template>

<style scoped>
.ltc-list { max-width: 920px; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.head h3 { margin: 0; font-size: 14px; }
.add-row { display: flex; gap: 8px; margin-bottom: 12px; }
.add-row input { flex: 1; }
.empty { color: var(--text-muted); padding: 16px; background: var(--panel); border: 1px dashed var(--border); border-radius: var(--radius); }
.ltc-row { display: grid; grid-template-columns: 1.5fr 1fr auto; gap: 12px; align-items: center; }
.ltc-row.archived { opacity: 0.55; }
.ltc-row input { width: 100%; }
.meta { font-size: 12px; color: var(--text-muted); }
.actions { display: flex; gap: 6px; }
.danger { background: var(--status-red); color: #fff; border-color: var(--status-red); }
</style>

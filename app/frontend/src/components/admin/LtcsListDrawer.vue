<script setup>
/* 选中 "LTC 子项目" 根节点时显示:LTC 列表 + 新增 LTC */
import { ref, computed } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi, newId } from '../../composables/useAdminApi.js'

const emit = defineEmits(['pick-ltc'])

const { ltcs, modules, refresh } = useDashboard()

const newName = ref('')
const adding = ref(false)
const errMsg = ref('')

const list = computed(() => [...(ltcs.value || [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0)))

async function add() {
  if (!newName.value.trim()) return
  adding.value = true
  errMsg.value = ''
  try {
    const created = await adminApi.createLtc({ id: newId(), name: newName.value.trim() })
    newName.value = ''
    await refresh()
    emit('pick-ltc', created.id)
  } catch (e) { errMsg.value = e.payload?.detail || e.message || '创建失败' }
  finally { adding.value = false }
}

function moduleCount(ltcId) {
  return (modules.value || []).filter(m => m.ltc_id === ltcId).length
}

async function move(item, dir) {
  const idx = list.value.findIndex(x => x.id === item.id)
  const j = idx + dir
  if (j < 0 || j >= list.value.length) return
  const a = list.value[idx], b = list.value[j]
  await Promise.all([
    adminApi.updateLtc(a.id, { order: b.order ?? j + 1 }),
    adminApi.updateLtc(b.id, { order: a.order ?? idx + 1 }),
  ])
  await refresh()
}
</script>

<template>
  <div class="ltcs-list">
    <header class="dh">
      <div>
        <div class="crumb">总览</div>
        <h2>LTC 子项目列表</h2>
      </div>
    </header>

    <p v-if="errMsg" class="err-banner">{{ errMsg }}</p>

    <section class="block">
      <h3>新增 LTC</h3>
      <div class="add-row">
        <input v-model="newName" placeholder="LTC 名称(如:上汽 AS33)" @keyup.enter="add" />
        <button class="primary" :disabled="adding || !newName.trim()" v-tooltip="'创建后自动进入详情'" @click="add">+ 新建</button>
      </div>
    </section>

    <section class="block">
      <h3>现有 LTC({{ list.length }})</h3>
      <div v-if="!list.length" class="hint">还没有 LTC,先新建一个</div>
      <div v-else class="list">
        <div
          v-for="(item, i) in list"
          :key="item.id"
          class="row"
          :class="{ archived: item.archived }"
        >
          <button class="name" v-tooltip="'进入该 LTC 详情'" @click="emit('pick-ltc', item.id)">
            {{ item.name }}
          </button>
          <span class="badge">{{ moduleCount(item.id) }} 模块</span>
          <span class="state">{{ item.archived ? '已归档' : '活跃' }}</span>
          <span class="ops">
            <button v-tooltip="'上移'" :disabled="i === 0" @click="move(item, -1)">↑</button>
            <button v-tooltip="'下移'" :disabled="i === list.length - 1" @click="move(item, 1)">↓</button>
          </span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.ltcs-list { display: flex; flex-direction: column; gap: 16px; }
.dh { padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.crumb { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
h2 { margin: 0; font-size: 18px; font-weight: 700; }
.block h3 { font-size: 13px; margin: 0 0 8px; font-weight: 700; }
.add-row { display: grid; grid-template-columns: 1fr 100px; gap: 8px; }
.list { display: flex; flex-direction: column; gap: 4px; }
.row { display: grid; grid-template-columns: 1fr 80px 60px 80px; gap: 10px; align-items: center; padding: 6px 10px; border-radius: var(--radius); background: var(--panel-soft); border: 1px solid var(--border-subtle); }
.row.archived { opacity: 0.55; }
.name { text-align: left; background: transparent; border: none; padding: 0; font-weight: 600; color: var(--text); cursor: pointer; }
.name:hover { color: var(--accent); background: transparent; }
.badge { font-size: 11px; color: var(--accent); background: var(--accent-soft); padding: 1px 8px; border-radius: var(--radius); text-align: center; }
.state { font-size: 11px; color: var(--text-muted); }
.ops { display: flex; gap: 4px; justify-content: flex-end; }
.ops button { font-size: 11px; padding: 2px 6px; }
.hint { font-size: 12px; color: var(--text-dim); padding: 6px 0; }
.err-banner { background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30); color: var(--status-red); padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0; }
</style>

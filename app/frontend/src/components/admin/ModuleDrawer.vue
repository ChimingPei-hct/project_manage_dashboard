<script setup>
/* 单个模块的详细编辑抽屉:基础信息、KPI 字段、子项(sub_items)增删改、Owner 绑定 */
import { computed, ref, watch } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi, newId } from '../../composables/useAdminApi.js'
import UserSearchInput from '../UserSearchInput.vue'
import ConfirmDialog from '../harness/ConfirmDialog.vue'

const props = defineProps({ moduleId: { type: String, required: true } })
const emit = defineEmits(['deleted'])

const { modules, ltcs, refresh } = useDashboard()
const module = computed(() => (modules.value || []).find(m => m.id === props.moduleId))
const ltcName = computed(() => ltcs.value.find(l => l.id === module.value?.ltc_id)?.name || '')

const draft = ref(null)
const dirty = ref(false)
const saving = ref(false)
const errMsg = ref('')

watch(module, (m) => {
  if (!m) return
  draft.value = {
    name: m.name,
    group: m.group,
    owner_open_id: m.owner_open_id,
    kpi_fields: (m.kpi_fields || []).map(k => ({ ...k })),
    sub_items: (m.sub_items || []).map(s => ({
      id: s.id, name: s.name, order: s.order,
      owner_open_id: s.owner_open_id || null,
      risk_note: s.risk_note || '',
    })),
  }
  dirty.value = false
}, { immediate: true })

function touch() { dirty.value = true }

function addSub() {
  draft.value.sub_items.push({
    id: newId().slice(0, 12),
    name: '新子项',
    order: draft.value.sub_items.length + 1,
    owner_open_id: null,
    risk_note: '',
  })
  touch()
}
function removeSub(i) { draft.value.sub_items.splice(i, 1); touch() }
function moveSub(i, dir) {
  const j = i + dir
  if (j < 0 || j >= draft.value.sub_items.length) return
  const arr = draft.value.sub_items
  ;[arr[i], arr[j]] = [arr[j], arr[i]]
  arr.forEach((x, idx) => x.order = idx + 1)
  touch()
}

function addKpi() {
  draft.value.kpi_fields.push({ key: `k${draft.value.kpi_fields.length + 1}`, label: '新指标', hint: '' })
  touch()
}
function removeKpi(i) { draft.value.kpi_fields.splice(i, 1); touch() }

async function save() {
  errMsg.value = ''
  saving.value = true
  try {
    const body = {
      name: draft.value.name,
      group: draft.value.group,
      owner_open_id: draft.value.owner_open_id || null,
      kpi_fields: draft.value.kpi_fields,
      sub_items: draft.value.sub_items.map((s, i) => ({ ...s, order: i + 1 })),
    }
    await adminApi.updateModule(props.moduleId, body)
    await refresh()
    dirty.value = false
  } catch (e) {
    errMsg.value = e.payload?.detail || e.message || '保存失败'
  } finally { saving.value = false }
}

const confirmDel = ref(false)
async function doDelete() {
  confirmDel.value = false
  await adminApi.deleteModule(props.moduleId)
  await refresh()
  emit('deleted')
}
</script>

<template>
  <div v-if="module && draft" class="module-drawer">
    <header class="drawer-head">
      <div>
        <div class="crumb">{{ ltcName ? 'LTC: ' + ltcName : 'PDT 级' }} / {{ draft.group || '未分组' }}</div>
        <h2>{{ draft.name }}</h2>
      </div>
      <div class="head-actions">
        <button
          class="primary"
          :disabled="!dirty || saving"
          v-tooltip="dirty ? '保存所有修改' : '无未保存变更'"
          @click="save"
        >{{ saving ? '保存中…' : '保存' }}</button>
        <button class="danger" v-tooltip="'删除此模块(状态清除,历史保留)'" @click="confirmDel = true">删除模块</button>
      </div>
    </header>

    <p v-if="errMsg" class="err-banner">{{ errMsg }}</p>

    <section class="block">
      <h3>基础信息</h3>
      <div class="grid-2">
        <label>
          <span>模块名</span>
          <input v-model="draft.name" @input="touch" placeholder="如:MCU 底软" />
        </label>
        <label>
          <span>分组</span>
          <input v-model="draft.group" @input="touch" placeholder="如:硬件和底软" />
        </label>
        <label class="span-2">
          <span>Owner</span>
          <div class="user-row">
            <UserSearchInput
              :modelValue="draft.owner_open_id"
              placeholder="搜索人员姓名…"
              @select="u => { draft.owner_open_id = u.open_id; touch() }"
            />
            <span v-if="draft.owner_open_id" class="owner-pill">
              {{ draft.owner_open_id }}
              <button class="x" v-tooltip="'清除 Owner'" @click="draft.owner_open_id = null; touch()">×</button>
            </span>
          </div>
        </label>
      </div>
    </section>

    <section class="block">
      <header class="sec-head">
        <h3>子项(sub_items)</h3>
        <button v-tooltip="'添加一个子项色块'" @click="addSub">+ 子项</button>
      </header>
      <div v-if="!draft.sub_items.length" class="hint">无子项 · 整模块只用一个状态灯</div>
      <div v-else class="sub-table">
        <div class="sub-row head">
          <span>名称</span><span>Owner(可选)</span><span>风险说明默认值(可选)</span><span>操作</span>
        </div>
        <div v-for="(s, i) in draft.sub_items" :key="s.id" class="sub-row">
          <input v-model="s.name" @input="touch" placeholder="子项名" />
          <UserSearchInput
            :modelValue="s.owner_open_id"
            placeholder="可选"
            @select="u => { s.owner_open_id = u.open_id; touch() }"
          />
          <input v-model="s.risk_note" @input="touch" placeholder="可选,作为默认风险占位" />
          <div class="row-ops">
            <button v-tooltip="'上移'" :disabled="i === 0" @click="moveSub(i, -1)">↑</button>
            <button v-tooltip="'下移'" :disabled="i === draft.sub_items.length - 1" @click="moveSub(i, 1)">↓</button>
            <button class="danger" v-tooltip="'删除此子项'" @click="removeSub(i)">×</button>
          </div>
        </div>
      </div>
    </section>

    <section class="block">
      <header class="sec-head">
        <h3>KPI 字段(kpi_fields)</h3>
        <button v-tooltip="'添加一个 KPI 字段'" @click="addKpi">+ KPI</button>
      </header>
      <div v-if="!draft.kpi_fields.length" class="hint">无 KPI 字段 · PDT 级总览卡常用</div>
      <div v-else class="kpi-table">
        <div class="kpi-row head">
          <span>key</span><span>显示名 label</span><span>提示 hint</span><span></span>
        </div>
        <div v-for="(k, i) in draft.kpi_fields" :key="i" class="kpi-row">
          <input v-model="k.key" @input="touch" placeholder="如 bug_close_rate" />
          <input v-model="k.label" @input="touch" placeholder="如 Bug 闭环率" />
          <input v-model="k.hint" @input="touch" placeholder="如 周环比" />
          <button class="danger" v-tooltip="'删除此 KPI'" @click="removeKpi(i)">×</button>
        </div>
      </div>
    </section>

    <ConfirmDialog
      :open="confirmDel"
      title="删除模块"
      :body="`确认删除模块「${draft.name}」?\n模块当前态被清除,历史 module_updates 保留。`"
      confirm-text="删除"
      @confirm="doDelete"
      @cancel="confirmDel = false"
    />
  </div>
  <div v-else class="empty">模块不存在或已删除</div>
</template>

<style scoped>
.module-drawer { display: flex; flex-direction: column; gap: 16px; }
.drawer-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.crumb { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
h2 { margin: 0; font-size: 18px; font-weight: 700; }
.head-actions { display: flex; gap: 8px; }
.danger { background: var(--status-red); color: #fff; border-color: var(--status-red); }
.danger:hover { background: #b91c1c; border-color: #b91c1c; color: #fff; }

.block { background: var(--panel); }
.block > h3, .sec-head h3 { font-size: 13px; margin: 0 0 8px; font-weight: 700; color: var(--text); }
.sec-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 14px; }
.grid-2 label { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--text-muted); }
.grid-2 input { font-size: 13px; }
.span-2 { grid-column: span 2; }
.user-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.user-row :deep(.user-search-wrap) { flex: 1; min-width: 200px; }
.owner-pill { background: var(--accent-soft); color: var(--accent); padding: 2px 8px; border-radius: var(--radius); font-size: 12px; display: inline-flex; align-items: center; gap: 4px; }
.x { background: transparent; border: none; padding: 0 2px; cursor: pointer; color: inherit; font-size: 13px; }

.sub-table, .kpi-table { display: flex; flex-direction: column; gap: 4px; }
.sub-row { display: grid; grid-template-columns: 1.2fr 1.4fr 1.6fr 110px; gap: 6px; align-items: center; }
.kpi-row { display: grid; grid-template-columns: 1fr 1.2fr 1.6fr 32px; gap: 6px; align-items: center; }
.sub-row.head, .kpi-row.head { font-size: 11px; color: var(--text-dim); padding: 0 4px; }
.sub-row input, .kpi-row input { font-size: 12.5px; }
.row-ops { display: flex; gap: 2px; justify-content: flex-end; }
.row-ops button { font-size: 11px; padding: 2px 6px; }

.hint { font-size: 12px; color: var(--text-dim); padding: 6px 0; }
.err-banner { background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30); color: var(--status-red); padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0; }

.empty { padding: 48px; text-align: center; color: var(--text-muted); }
</style>

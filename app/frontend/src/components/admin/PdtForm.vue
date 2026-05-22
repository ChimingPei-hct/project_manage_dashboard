<script setup>
import { ref, watch, computed } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi } from '../../composables/useAdminApi.js'
import InlineEdit from '../harness/InlineEdit.vue'
import DraggableList from '../harness/DraggableList.vue'

const { pdt, refresh } = useDashboard()

// 本地草稿,避免每个字段都立刻 PUT
const draft = ref({ name: '', description: '', milestones: [] })

watch(pdt, (v) => {
  if (!v) return
  draft.value = {
    name: v.name || '',
    description: v.description || '',
    milestones: (v.milestones || []).map(m => ({ ...m, _key: crypto.randomUUID?.() || Math.random() })),
  }
}, { immediate: true })

const saving = ref(false)
const dirty = computed(() => JSON.stringify(stripped()) !== JSON.stringify(originStripped()))
function stripped() {
  return {
    name: draft.value.name,
    description: draft.value.description,
    milestones: draft.value.milestones.map(({ _key, ...rest }) => rest),
  }
}
function originStripped() {
  return {
    name: pdt.value?.name || '',
    description: pdt.value?.description || '',
    milestones: pdt.value?.milestones || [],
  }
}

async function save() {
  saving.value = true
  try {
    await adminApi.updatePdt(stripped())
    await refresh()
  } finally {
    saving.value = false
  }
}

function addMilestone() {
  draft.value.milestones.push({
    name: '新里程碑',
    date: '2026-12-31',
    type: 'TR',
    note: '',
    _key: crypto.randomUUID?.() || Math.random(),
  })
}
function removeMilestone(idx) {
  draft.value.milestones.splice(idx, 1)
}
function reorder(next) {
  draft.value.milestones = next
}
</script>

<template>
  <div class="pdt-form">
    <div class="row">
      <label>PDT 名称</label>
      <input v-model="draft.name" placeholder="如:Multicam Pilot 3.0" />
    </div>
    <div class="row">
      <label>描述</label>
      <textarea v-model="draft.description" rows="2" placeholder="可选,描述本产品线"></textarea>
    </div>

    <div class="section">
      <div class="section-head">
        <h3>里程碑</h3>
        <button @click="addMilestone" v-tooltip="'添加一个新的里程碑(可拖拽改顺序,展示按日期升序)'">+ 添加里程碑</button>
      </div>
      <div v-if="!draft.milestones.length" class="empty">暂无里程碑,点上方按钮添加。</div>
      <DraggableList v-else :items="draft.milestones" item-key="_key" @reorder="reorder">
        <template #default="{ item, index }">
          <div class="ms-row">
            <input class="ms-name" v-model="item.name" placeholder="里程碑名" />
            <input class="ms-date" type="date" v-model="item.date" />
            <select v-model="item.type" v-tooltip="'类型决定时间轴上的色块色调'">
              <option value="TR">TR(技术评审)</option>
              <option value="SOP">SOP(量产)</option>
              <option value="review">review(评审)</option>
              <option value="other">other</option>
            </select>
            <input class="ms-note" v-model="item.note" placeholder="备注(可选)" />
            <button class="danger" @click="removeMilestone(index)" v-tooltip="'删除此里程碑'">删</button>
          </div>
        </template>
      </DraggableList>
    </div>

    <div class="footer">
      <button class="primary" :disabled="!dirty || saving" @click="save"
              v-tooltip="dirty ? '保存所有修改并刷新看板' : '没有未保存的变更'">
        {{ saving ? '保存中…' : '保存修改' }}
      </button>
      <span v-if="!dirty" class="hint">无未保存变更</span>
    </div>
  </div>
</template>

<style scoped>
.pdt-form { max-width: 920px; }
.row { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 12px; }
.row label { width: 96px; padding-top: 6px; color: var(--text-muted); flex-shrink: 0; }
.row input[type="text"], .row input:not([type]), .row textarea { flex: 1; }
.section { margin: 20px 0; }
.section-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.section-head h3 { margin: 0; font-size: 14px; }
.empty { color: var(--text-muted); padding: 16px; background: var(--panel); border: 1px dashed var(--border); border-radius: var(--radius); }
.ms-row { display: grid; grid-template-columns: 1.4fr 0.8fr 0.8fr 1.4fr auto; gap: 6px; align-items: center; }
.ms-row input, .ms-row select { font-size: 13px; }
.footer { margin-top: 20px; display: flex; align-items: center; gap: 12px; }
.danger { background: var(--status-red); color: #fff; border-color: var(--status-red); }
.hint { color: var(--text-muted); font-size: 12px; }
</style>

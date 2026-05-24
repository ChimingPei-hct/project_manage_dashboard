<script setup>
/**
 * LTC 模板编辑器:管理 scope=ltc_template 的 Category + Module。
 * - 模板池全 PDT 共享一套(单一模板池)
 * - 字段仅暴露 name / order / group(module);sub_items / kpi_fields 留空,新 LTC 创建后再补
 * - 改模板纯快照语义:不影响已通过 init-from-template 拷贝出去的 LTC
 */
import { computed, onMounted, ref } from 'vue'
import { useCategories } from '../../composables/useCategories.js'
import { adminApi } from '../../composables/useAdminApi.js'
import { sseBus } from '../../composables/sseBus.js'

const { categories, reload: reloadCats } = useCategories()
const templateModules = ref([])
const loading = ref(false)

async function reloadModules() {
  loading.value = true
  try {
    templateModules.value = await adminApi.listModules({ scope: 'ltc_template' }) || []
  } finally { loading.value = false }
}

async function reloadAll() {
  await Promise.all([reloadCats(), reloadModules()])
}

onMounted(reloadAll)
sseBus.on('config:reload', (p) => {
  if (!p || p.kind === 'modules') reloadModules()
})

const templateCats = computed(() => (categories.value || [])
  .filter(c => c.scope === 'ltc_template')
  .slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0)))

function modulesOf(catId) {
  return templateModules.value
    .filter(m => m.category_id === catId)
    .slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
}

const errorMsg = ref('')
const toast = ref('')
function flashErr(m) { errorMsg.value = m; setTimeout(() => { errorMsg.value = '' }, 3500) }
function flashOk(m) { toast.value = m; setTimeout(() => { toast.value = '' }, 1800) }

function genCatId(name) {
  const slug = (name || '').toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return `tpl-cat-${slug || 'new'}-${Math.random().toString(36).slice(2, 6)}`
}
function genModId(name) {
  const slug = (name || '').toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return `tpl-mod-${slug || 'new'}-${Math.random().toString(36).slice(2, 6)}`
}

/* --- Category 操作 --- */
const showCreateCat = ref(false)
const catDraft = ref({ name: '' })
function openCreateCat() { catDraft.value = { name: '' }; showCreateCat.value = true }
async function saveCreateCat() {
  const name = (catDraft.value.name || '').trim()
  if (!name) { flashErr('大类名称不能为空'); return }
  try {
    await adminApi.createCategory({
      id: genCatId(name),
      name,
      scope: 'ltc_template',
      order: templateCats.value.length + 1,
    })
    showCreateCat.value = false
    flashOk('模板大类已创建')
    await reloadCats()
  } catch (e) { flashErr(e.payload?.detail || e.message || '创建失败') }
}

const editingCat = ref({})
function startEditCat(c) {
  editingCat.value = { ...editingCat.value, [c.id]: { name: c.name } }
}
function cancelEditCat(id) {
  const next = { ...editingCat.value }; delete next[id]; editingCat.value = next
}
async function saveEditCat(c) {
  const buf = editingCat.value[c.id]; if (!buf) return
  const name = (buf.name || '').trim()
  if (!name) { flashErr('大类名称不能为空'); return }
  try {
    await adminApi.updateCategory(c.id, { name })
    cancelEditCat(c.id)
    flashOk('模板大类已更新')
    await reloadCats()
  } catch (e) { flashErr(e.payload?.detail || e.message || '保存失败') }
}
async function removeCat(c) {
  const inUse = modulesOf(c.id)
  if (inUse.length) {
    if (!confirm(`「${c.name}」下还有 ${inUse.length} 个模板模块,需先逐个删除模板模块后再删大类。`)) return
    return
  }
  if (!confirm(`确认删除模板大类「${c.name}」?\n已通过模板拷贝出去的 LTC 不受影响。`)) return
  try {
    await adminApi.deleteCategory(c.id)
    flashOk('模板大类已删除')
    await reloadCats()
  } catch (e) {
    if (e.status === 409) flashErr('该大类仍有模块引用,先迁移或删除模块')
    else flashErr(e.payload?.detail || e.message || '删除失败')
  }
}
async function moveCat(c, delta) {
  const list = templateCats.value
  const i = list.findIndex(x => x.id === c.id); const j = i + delta
  if (i < 0 || j < 0 || j >= list.length) return
  const a = list[i], b = list[j]
  try {
    await adminApi.updateCategory(a.id, { order: b.order })
    await adminApi.updateCategory(b.id, { order: a.order })
    await reloadCats()
  } catch (e) { flashErr(e.payload?.detail || e.message || '排序失败') }
}

/* --- Module 操作 --- */
const showCreateMod = ref(false)
const modDraft = ref({ name: '', group: '', category_id: null })
function openCreateMod(catId) {
  modDraft.value = { name: '', group: '', category_id: catId }
  showCreateMod.value = true
}
async function saveCreateMod() {
  const name = (modDraft.value.name || '').trim()
  const group = (modDraft.value.group || '').trim() || templateCats.value.find(c => c.id === modDraft.value.category_id)?.name || '未分组'
  if (!name) { flashErr('模块名称不能为空'); return }
  try {
    await adminApi.createModule({
      id: genModId(name),
      scope: 'ltc_template',
      name,
      group,
      category_id: modDraft.value.category_id,
      order: modulesOf(modDraft.value.category_id).length + 1,
    })
    showCreateMod.value = false
    flashOk('模板模块已创建')
    await reloadModules()
  } catch (e) { flashErr(e.payload?.detail || e.message || '创建失败') }
}

const editingMod = ref({})
function startEditMod(m) {
  editingMod.value = { ...editingMod.value, [m.id]: { name: m.name, group: m.group || '' } }
}
function cancelEditMod(id) {
  const next = { ...editingMod.value }; delete next[id]; editingMod.value = next
}
async function saveEditMod(m) {
  const buf = editingMod.value[m.id]; if (!buf) return
  const name = (buf.name || '').trim()
  if (!name) { flashErr('模块名称不能为空'); return }
  try {
    await adminApi.updateModule(m.id, { name, group: (buf.group || '').trim() || m.group })
    cancelEditMod(m.id)
    flashOk('模板模块已更新')
    await reloadModules()
  } catch (e) { flashErr(e.payload?.detail || e.message || '保存失败') }
}
async function removeMod(m) {
  if (!confirm(`确认删除模板模块「${m.name}」?\n已通过模板拷贝出去的 LTC 不受影响。`)) return
  try {
    await adminApi.deleteModule(m.id)
    flashOk('模板模块已删除')
    await reloadModules()
  } catch (e) { flashErr(e.payload?.detail || e.message || '删除失败') }
}
async function moveMod(m, delta) {
  const list = modulesOf(m.category_id)
  const i = list.findIndex(x => x.id === m.id); const j = i + delta
  if (i < 0 || j < 0 || j >= list.length) return
  const a = list[i], b = list[j]
  try {
    await adminApi.updateModule(a.id, { order: b.order })
    await adminApi.updateModule(b.id, { order: a.order })
    await reloadModules()
  } catch (e) { flashErr(e.payload?.detail || e.message || '排序失败') }
}
</script>

<template>
  <div class="tpl-editor">
    <header class="head">
      <div>
        <h3>LTC 模板池</h3>
        <p class="hint">单一模板池,全 PDT 共享。新建 LTC 时勾选"从模板复制"即拷贝一份副本,后续改模板**不影响**已拷贝出去的 LTC。</p>
      </div>
      <button class="primary" v-tooltip="'新增一个模板大类'" @click="openCreateCat">+ 模板大类</button>
    </header>

    <p v-if="errorMsg" class="err-banner">{{ errorMsg }}</p>
    <p v-if="toast" class="ok-banner">{{ toast }}</p>

    <div v-if="!templateCats.length && !loading" class="empty">
      <p>模板池为空。新建大类后,新建 LTC 时即可勾选"从模板复制"快速初始化。</p>
    </div>

    <div v-for="(c, ci) in templateCats" :key="c.id" class="cat-card">
      <div class="cat-head">
        <div class="cat-name">
          <template v-if="!editingCat[c.id]">
            <span class="name">{{ c.name }}</span>
            <span class="cnt">{{ modulesOf(c.id).length }} 个模块</span>
          </template>
          <template v-else>
            <input v-model="editingCat[c.id].name" class="name-edit" maxlength="32" />
          </template>
        </div>
        <div class="cat-acts">
          <button class="mini" :disabled="ci === 0" v-tooltip="'上移大类'" @click="moveCat(c, -1)">↑</button>
          <button class="mini" :disabled="ci === templateCats.length - 1" v-tooltip="'下移大类'" @click="moveCat(c, 1)">↓</button>
          <template v-if="!editingCat[c.id]">
            <button class="mini" v-tooltip="'新增本大类下的模板模块'" @click="openCreateMod(c.id)">+ 模块</button>
            <button class="mini" v-tooltip="'重命名大类'" @click="startEditCat(c)">编辑</button>
            <button class="mini danger" v-tooltip="'删除大类(本大类下若有模板模块需先清空)'" @click="removeCat(c)">删除</button>
          </template>
          <template v-else>
            <button class="mini primary" v-tooltip="'保存修改'" @click="saveEditCat(c)">保存</button>
            <button class="mini" v-tooltip="'放弃修改'" @click="cancelEditCat(c.id)">取消</button>
          </template>
        </div>
      </div>
      <ul class="mod-list">
        <li v-if="!modulesOf(c.id).length" class="mod-empty">本大类下暂无模板模块</li>
        <li v-for="(m, mi) in modulesOf(c.id)" :key="m.id" class="mod-row">
          <div class="mod-main">
            <template v-if="!editingMod[m.id]">
              <span class="m-name">{{ m.name }}</span>
              <span class="m-group">分组 · {{ m.group || '未分组' }}</span>
            </template>
            <template v-else>
              <input v-model="editingMod[m.id].name" class="m-edit" placeholder="模块名" maxlength="48" />
              <input v-model="editingMod[m.id].group" class="m-edit" placeholder="分组(可选,留空沿用)" maxlength="32" />
            </template>
          </div>
          <div class="mod-acts">
            <button class="mini" :disabled="mi === 0" v-tooltip="'上移模块'" @click="moveMod(m, -1)">↑</button>
            <button class="mini" :disabled="mi === modulesOf(c.id).length - 1" v-tooltip="'下移模块'" @click="moveMod(m, 1)">↓</button>
            <template v-if="!editingMod[m.id]">
              <button class="mini" v-tooltip="'重命名 / 改分组'" @click="startEditMod(m)">编辑</button>
              <button class="mini danger" v-tooltip="'删除模板模块'" @click="removeMod(m)">删除</button>
            </template>
            <template v-else>
              <button class="mini primary" v-tooltip="'保存修改'" @click="saveEditMod(m)">保存</button>
              <button class="mini" v-tooltip="'放弃修改'" @click="cancelEditMod(m.id)">取消</button>
            </template>
          </div>
        </li>
      </ul>
    </div>

    <!-- 新建大类弹窗 -->
    <div v-if="showCreateCat" class="modal-mask" @click.self="showCreateCat = false">
      <div class="modal-box">
        <header class="mh"><h3>新建模板大类</h3><button class="close" v-tooltip="'关闭'" @click="showCreateCat = false">×</button></header>
        <label class="fld">
          <span>大类名称 *</span>
          <input v-model="catDraft.name" placeholder="如:感知" maxlength="32" @keyup.enter="saveCreateCat" />
        </label>
        <footer class="mf">
          <button v-tooltip="'放弃'" @click="showCreateCat = false">取消</button>
          <button class="primary" v-tooltip="'创建模板大类'" @click="saveCreateCat">创建</button>
        </footer>
      </div>
    </div>

    <!-- 新建模块弹窗 -->
    <div v-if="showCreateMod" class="modal-mask" @click.self="showCreateMod = false">
      <div class="modal-box">
        <header class="mh"><h3>新建模板模块</h3><button class="close" v-tooltip="'关闭'" @click="showCreateMod = false">×</button></header>
        <label class="fld">
          <span>模块名称 *</span>
          <input v-model="modDraft.name" placeholder="如:激光感知" maxlength="48" />
        </label>
        <label class="fld">
          <span>分组(可选,留空沿用大类名)</span>
          <input v-model="modDraft.group" placeholder="如:感知" maxlength="32" />
        </label>
        <footer class="mf">
          <button v-tooltip="'放弃'" @click="showCreateMod = false">取消</button>
          <button class="primary" v-tooltip="'创建模板模块'" @click="saveCreateMod">创建</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tpl-editor { display: flex; flex-direction: column; gap: 12px; padding: 4px 4px 16px; }
.head { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 10px; border-bottom: 1px solid var(--border); gap: 12px; }
.head h3 { margin: 0; font-size: 16px; font-weight: 700; }
.hint { margin: 4px 0 0; font-size: 12px; color: var(--text-muted); }

.primary {
  background: var(--accent); color: #fff; border-color: var(--accent);
  font-size: 12px; padding: 5px 10px; border-radius: 6px; cursor: pointer;
}
.primary:hover { opacity: 0.92; }

.empty { padding: 24px; background: var(--panel-soft); border: 1px dashed var(--border); border-radius: 6px; font-size: 13px; color: var(--text-muted); text-align: center; }

.cat-card {
  border: 1px solid var(--border-subtle); border-radius: 6px; background: var(--panel);
  display: flex; flex-direction: column;
}
.cat-head {
  display: flex; justify-content: space-between; align-items: center; gap: 12px;
  padding: 8px 10px; border-bottom: 1px solid var(--border-subtle);
  background: var(--panel-soft); border-radius: 6px 6px 0 0;
}
.cat-name { display: flex; align-items: center; gap: 10px; }
.name { font-size: 13px; font-weight: 700; }
.cnt { font-size: 11.5px; color: var(--text-muted); }
.name-edit { font-size: 13px; padding: 3px 6px; width: 180px; border: 1px solid var(--border); border-radius: 6px; }
.cat-acts { display: flex; gap: 4px; flex-wrap: wrap; }

.mod-list { list-style: none; padding: 6px 8px; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.mod-empty { font-size: 12px; color: var(--text-muted); padding: 4px 4px; }
.mod-row {
  display: flex; justify-content: space-between; align-items: center; gap: 8px;
  padding: 6px 8px; border: 1px solid var(--border-subtle); border-radius: 6px;
}
.mod-main { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex: 1; }
.m-name { font-size: 12.5px; font-weight: 600; }
.m-group { font-size: 11.5px; color: var(--text-muted); }
.m-edit { font-size: 12.5px; padding: 3px 6px; width: 160px; border: 1px solid var(--border); border-radius: 6px; }
.mod-acts { display: flex; gap: 4px; }

.mini {
  font-size: 11px; padding: 3px 7px; border-radius: 6px;
  border: 1px solid var(--border); background: var(--panel); cursor: pointer;
  color: var(--text-muted);
}
.mini:hover:not(:disabled) { color: var(--accent); border-color: var(--accent); }
.mini:disabled { opacity: 0.4; cursor: not-allowed; }
.mini.primary { color: #fff; background: var(--accent); border-color: var(--accent); }
.mini.danger { color: var(--status-red); border-color: var(--status-red); }
.mini.danger:hover { background: var(--status-red); color: #fff; }

.err-banner { background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30); color: var(--status-red); padding: 6px 10px; border-radius: 6px; font-size: 12px; margin: 0; }
.ok-banner { background: var(--status-green-bg); border: 1px solid rgba(82,196,26,0.30); color: var(--status-green); padding: 6px 10px; border-radius: 6px; font-size: 12px; margin: 0; }

.modal-mask {
  position: fixed; inset: 0; background: rgba(15,23,42,0.42);
  display: flex; align-items: center; justify-content: center;
  z-index: 9200; backdrop-filter: blur(2px);
}
.modal-box {
  background: var(--panel); border-radius: 6px;
  padding: 16px 20px; min-width: 320px; max-width: 460px; width: 92vw;
  box-shadow: var(--shadow-lg); display: flex; flex-direction: column; gap: 10px;
}
.mh { display: flex; justify-content: space-between; align-items: center; }
.mh h3 { margin: 0; font-size: 15px; font-weight: 700; }
.close { border: none; background: transparent; font-size: 22px; line-height: 1; padding: 0 6px; cursor: pointer; color: var(--text-muted); }
.close:hover { color: var(--accent); }
.fld { display: flex; flex-direction: column; gap: 4px; }
.fld > span { font-size: 11.5px; color: var(--text-muted); }
.fld input { font-size: 13px; padding: 5px 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--panel); }
.mf { display: flex; justify-content: flex-end; gap: 8px; padding-top: 8px; border-top: 1px solid var(--border-subtle); }
.mf button { font-size: 12px; padding: 5px 12px; border: 1px solid var(--border); background: var(--panel); border-radius: 6px; cursor: pointer; }
</style>

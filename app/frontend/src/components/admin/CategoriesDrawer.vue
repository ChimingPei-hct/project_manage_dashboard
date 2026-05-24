<script setup>
import { computed, onMounted, ref } from 'vue'
import { useCategories } from '../../composables/useCategories.js'
import { useContactCache, displayName } from '../../composables/useContactCache.js'
import { adminApi } from '../../composables/useAdminApi.js'
import UserSearchInput from '../UserSearchInput.vue'

/**
 * LTC 大类(Category)管理:
 * - 列出 scope=ltc & ltc_id=本 LTC 的大类(模板池 ltc_template 不在此展示,通过「从模板初始化」拷贝)
 * - 新增/重命名/改 Owner/排序/删除
 * - 空态显示「从模板初始化本 LTC」按钮
 * - 删除前若有 module 引用,后端返 409,前端 toast 提示
 */
const props = defineProps({
  ltcId: { type: String, required: true },
})

const { categories, reload } = useCategories()
const { contacts, ensureContacts } = useContactCache()

onMounted(() => { reload(); ensureContacts() })

const visible = computed(() => (categories.value || [])
  .filter(c => c.scope === 'ltc' && c.ltc_id === props.ltcId)
  .slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0)))

const hasTemplate = computed(() => (categories.value || [])
  .some(c => c.scope === 'ltc_template'))

const errorMsg = ref('')
const toast = ref('')
function flashErr(msg) { errorMsg.value = msg; setTimeout(() => { errorMsg.value = '' }, 3500) }
function flashOk(msg) { toast.value = msg; setTimeout(() => { toast.value = '' }, 1800) }

function ownerName(openId) {
  if (!openId) return ''
  const u = (contacts.value || []).find(x => x.open_id === openId)
  return u?.name || displayName(openId) || openId
}

/* 新增表单 */
const showCreate = ref(false)
const draft = ref({ id: '', name: '', owner_open_id: null, owner_name: '' })
function openCreate() {
  draft.value = { id: '', name: '', owner_open_id: null, owner_name: '' }
  showCreate.value = true
  errorMsg.value = ''
}
function genId(name) {
  const slug = (name || '').toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return `cat-${slug || 'new'}-${Math.random().toString(36).slice(2, 6)}`
}
function pickOwner(u) {
  draft.value.owner_open_id = u?.open_id || null
  draft.value.owner_name = u?.name || ''
}
async function saveCreate() {
  errorMsg.value = ''
  const name = draft.value.name.trim()
  if (!name) { flashErr('大类名称不能为空'); return }
  if (name.length > 32) { flashErr('大类名最多 32 字'); return }
  const body = {
    id: draft.value.id || genId(name),
    name,
    scope: 'ltc',
    ltc_id: props.ltcId,
    owner_open_id: draft.value.owner_open_id || null,
    order: visible.value.length + 1,
  }
  try {
    await adminApi.createCategory(body)
    showCreate.value = false
    flashOk('大类已创建')
    await reload()
  } catch (e) {
    flashErr(e.payload?.detail || e.message || '创建失败')
  }
}

/* 行内编辑 */
const editing = ref({}) // {id: {name, owner_open_id, owner_name}}
function startEdit(c) {
  editing.value = {
    ...editing.value,
    [c.id]: { name: c.name, owner_open_id: c.owner_open_id || null, owner_name: ownerName(c.owner_open_id) },
  }
}
function cancelEdit(id) {
  const next = { ...editing.value }
  delete next[id]
  editing.value = next
}
async function saveEdit(c) {
  const buf = editing.value[c.id]
  if (!buf) return
  const name = (buf.name || '').trim()
  if (!name) { flashErr('大类名称不能为空'); return }
  try {
    await adminApi.updateCategory(c.id, {
      name,
      owner_open_id: buf.owner_open_id || null,
    })
    cancelEdit(c.id)
    flashOk('大类已更新')
    await reload()
  } catch (e) {
    flashErr(e.payload?.detail || e.message || '保存失败')
  }
}

async function remove(c) {
  if (!confirm(`确认删除大类「${c.name}」?\n该大类下若有模块仍在引用,会被后端拒绝。`)) return
  try {
    await adminApi.deleteCategory(c.id)
    flashOk('大类已删除')
    await reload()
  } catch (e) {
    if (e.status === 409) flashErr('该大类仍有模块引用,先迁移模块再删除')
    else flashErr(e.payload?.detail || e.message || '删除失败')
  }
}

const initing = ref(false)
async function initFromTemplate() {
  if (initing.value) return
  if (!confirm('将「模板池」的大类与示例模块拷贝到本 LTC,之后可自由删改。\n模板后续修改不影响已拷贝的副本。继续?')) return
  initing.value = true
  try {
    const r = await adminApi.initLtcFromTemplate(props.ltcId)
    flashOk(`已初始化:${r.copied_categories} 个大类、${r.copied_modules} 个模块`)
    await reload()
  } catch (e) {
    if (e.status === 409) flashErr('本 LTC 已有大类或模块,无法重复初始化')
    else flashErr(e.payload?.detail || e.message || '初始化失败')
  } finally {
    initing.value = false
  }
}

async function move(c, delta) {
  /* 简单 order 微调:与相邻项交换 order,再各自 PUT */
  const list = visible.value
  const idx = list.findIndex(x => x.id === c.id)
  const j = idx + delta
  if (idx < 0 || j < 0 || j >= list.length) return
  const a = list[idx], b = list[j]
  try {
    await adminApi.updateCategory(a.id, { order: b.order })
    await adminApi.updateCategory(b.id, { order: a.order })
    await reload()
  } catch (e) {
    flashErr(e.payload?.detail || e.message || '排序失败')
  }
}
</script>

<template>
  <div class="cat-drawer">
    <header class="dh">
      <div>
        <div class="crumb">LTC 配置 / 大类(Category)</div>
        <h2>大类管理</h2>
        <p class="hint">本 LTC 私有大类。可从模板池一次性初始化,之后自由删改 —— 模板的后续改动不影响本 LTC。模块通过 <code>category_id</code> 关联到大类。</p>
      </div>
      <button class="primary" v-tooltip="'新增一个本 LTC 私有大类'" @click="openCreate">+ 新建大类</button>
    </header>

    <p v-if="errorMsg" class="err-banner">{{ errorMsg }}</p>
    <p v-if="toast" class="ok-banner">{{ toast }}</p>

    <div v-if="!visible.length" class="empty">
      <p class="empty-line">本 LTC 尚未配置任何大类。</p>
      <div class="empty-acts">
        <button
          v-if="hasTemplate"
          class="primary"
          :disabled="initing"
          v-tooltip="'拷贝模板池(感知/规控/HMI/基建/安全/工具)的大类与示例模块到本 LTC,可随后自由删改'"
          @click="initFromTemplate"
        >
          {{ initing ? '初始化中…' : '从模板初始化本 LTC' }}
        </button>
        <button v-tooltip="'手动新建一个本 LTC 私有大类'" @click="openCreate">手动新建</button>
      </div>
    </div>

    <ul v-else class="list">
      <li v-for="(c, i) in visible" :key="c.id" class="row">
        <div class="row-main">
          <template v-if="!editing[c.id]">
            <span class="name">{{ c.name }}</span>
            <span class="owner">Owner · {{ ownerName(c.owner_open_id) || '未指派' }}</span>
          </template>
          <template v-else>
            <input v-model="editing[c.id].name" class="name-edit" placeholder="大类名" maxlength="32" />
            <div class="owner-edit">
              <UserSearchInput
                :modelValue="editing[c.id].owner_name"
                @update:modelValue="v => editing[c.id].owner_name = v"
                @select="u => { editing[c.id].owner_open_id = u?.open_id || null; editing[c.id].owner_name = u?.name || '' }"
                placeholder="搜索 Owner…"
              />
              <button
                v-if="editing[c.id].owner_open_id"
                class="mini-del"
                v-tooltip="'清除 Owner'"
                @click="editing[c.id].owner_open_id = null; editing[c.id].owner_name = ''"
              >×</button>
            </div>
          </template>
        </div>
        <div class="row-acts">
          <button class="mini" :disabled="i === 0" v-tooltip="'上移'" @click="move(c, -1)">↑</button>
          <button class="mini" :disabled="i === visible.length - 1" v-tooltip="'下移'" @click="move(c, 1)">↓</button>
          <template v-if="!editing[c.id]">
            <button class="mini" v-tooltip="'重命名 / 改 Owner'" @click="startEdit(c)">编辑</button>
            <button class="mini danger" v-tooltip="'删除大类(若仍有模块引用会被拒绝)'" @click="remove(c)">删除</button>
          </template>
          <template v-else>
            <button class="mini primary" v-tooltip="'保存修改'" @click="saveEdit(c)">保存</button>
            <button class="mini" v-tooltip="'放弃修改'" @click="cancelEdit(c.id)">取消</button>
          </template>
        </div>
      </li>
    </ul>

    <!-- 新建表单 -->
    <div v-if="showCreate" class="create-mask" @click.self="showCreate = false">
      <div class="create-box">
        <header class="ch">
          <h3>新建大类</h3>
          <button class="close" @click="showCreate = false" v-tooltip="'关闭'">×</button>
        </header>
        <label class="fld">
          <span>大类名称 *</span>
          <input v-model="draft.name" placeholder="如:硬件和底软" maxlength="32" />
        </label>
        <div class="fld">
          <span>Owner(可选)</span>
          <UserSearchInput
            :modelValue="draft.owner_name"
            @update:modelValue="v => draft.owner_name = v"
            @select="pickOwner"
            placeholder="搜索人员姓名…"
          />
        </div>
        <footer class="cf">
          <button @click="showCreate = false" v-tooltip="'放弃'">取消</button>
          <button class="primary" v-tooltip="'创建大类'" @click="saveCreate">创建</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cat-drawer { display: flex; flex-direction: column; gap: 12px; padding: 4px 4px 16px; }
.dh {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding-bottom: 10px; border-bottom: 1px solid var(--border); gap: 12px;
}
.crumb { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
h2 { margin: 0; font-size: 16px; font-weight: 700; }
.hint { margin: 4px 0 0; font-size: 12px; color: var(--text-muted); }
.hint code { background: var(--panel-soft); padding: 1px 5px; border-radius: 3px; font-size: 11.5px; }

.primary {
  background: var(--accent); color: #fff; border-color: var(--accent);
  font-size: 12px; padding: 5px 10px; border-radius: var(--radius); cursor: pointer;
}
.primary:hover { opacity: 0.92; }
.danger { color: var(--status-red); border-color: var(--status-red); }
.danger:hover { background: var(--status-red); color: #fff; }

.empty {
  padding: 24px; background: var(--panel-soft); border: 1px dashed var(--border);
  border-radius: var(--radius); font-size: 13px; color: var(--text-muted); text-align: center;
}
.empty-line { margin: 0 0 12px; }
.empty-acts { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
.empty-acts button {
  font-size: 12px; padding: 6px 14px; border-radius: var(--radius);
  border: 1px solid var(--border); background: var(--panel); cursor: pointer;
}
.empty-acts button.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.empty-acts button.primary:hover:not(:disabled) { opacity: 0.92; }
.empty-acts button:disabled { opacity: 0.5; cursor: not-allowed; }

.list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.row {
  display: flex; justify-content: space-between; align-items: center; gap: 12px;
  padding: 8px 10px; border: 1px solid var(--border-subtle);
  border-radius: var(--radius); background: var(--panel);
}
.row-main { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex: 1; }
.scope-tag {
  font-size: 10.5px; padding: 1px 6px; border-radius: var(--radius);
  font-weight: 600; letter-spacing: 0.3px;
}
.scope-ltc_template { background: var(--status-green-bg); color: var(--status-green); }
.scope-ltc { background: var(--accent-soft, var(--panel-soft)); color: var(--accent); border: 1px solid var(--border); }

.name { font-size: 13px; font-weight: 600; }
.owner { font-size: 11.5px; color: var(--text-muted); }
.name-edit { font-size: 13px; padding: 3px 6px; width: 180px; }
.owner-edit { display: inline-flex; gap: 4px; align-items: center; width: 220px; }

.row-acts { display: flex; gap: 4px; }
.mini {
  font-size: 11px; padding: 3px 7px; border-radius: var(--radius);
  border: 1px solid var(--border); background: var(--panel); cursor: pointer;
  color: var(--text-muted);
}
.mini:hover:not(:disabled) { color: var(--accent); border-color: var(--accent); }
.mini:disabled { opacity: 0.4; cursor: not-allowed; }
.mini.primary { color: #fff; background: var(--accent); border-color: var(--accent); }
.mini.danger { color: var(--status-red); border-color: var(--status-red); }
.mini.danger:hover { background: var(--status-red); color: #fff; }

.err-banner {
  background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30);
  color: var(--status-red); padding: 6px 10px; border-radius: var(--radius);
  font-size: 12px; margin: 0;
}
.ok-banner {
  background: var(--status-green-bg); border: 1px solid rgba(82,196,26,0.30);
  color: var(--status-green); padding: 6px 10px; border-radius: var(--radius);
  font-size: 12px; margin: 0;
}

.create-mask {
  position: fixed; inset: 0; background: rgba(15,23,42,0.42);
  display: flex; align-items: center; justify-content: center;
  z-index: 9200; backdrop-filter: blur(2px);
}
.create-box {
  background: var(--panel); border-radius: var(--radius);
  padding: 16px 20px; min-width: 360px; max-width: 480px; width: 92vw;
  box-shadow: var(--shadow-lg); display: flex; flex-direction: column; gap: 10px;
}
.ch { display: flex; justify-content: space-between; align-items: center; }
.ch h3 { margin: 0; font-size: 15px; font-weight: 700; }
.close { border: none; background: transparent; font-size: 22px; line-height: 1; padding: 0 6px; cursor: pointer; color: var(--text-muted); }
.close:hover { color: var(--accent); }
.fld { display: flex; flex-direction: column; gap: 4px; }
.fld > span { font-size: 11.5px; color: var(--text-muted); }
.fld input, .fld select { font-size: 13px; padding: 5px 8px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--panel); }
.cf { display: flex; justify-content: flex-end; gap: 8px; padding-top: 8px; border-top: 1px solid var(--border-subtle); }
</style>

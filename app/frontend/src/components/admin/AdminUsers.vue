<script setup>
import { ref, onMounted, computed } from 'vue'
import { adminApi } from '../../composables/useAdminApi.js'
import { useDashboard } from '../../composables/useDashboard.js'
import { useContactCache } from '../../composables/useContactCache.js'
import UserSearchInput from '../UserSearchInput.vue'
import ConfirmDialog from '../harness/ConfirmDialog.vue'

const { ltcs } = useDashboard()
const { contacts, ensureContacts } = useContactCache()
onMounted(() => ensureContacts())

const admins = ref({ super: [], pdt: [], ltc: {} })
const loading = ref(false)

async function refresh() {
  loading.value = true
  try { admins.value = await adminApi.getAdmins() }
  finally { loading.value = false }
}
onMounted(refresh)

function nameOf(openId) {
  const u = contacts.value.find(x => x.open_id === openId)
  return u?.name || openId
}

const queryStr = ref({ super: '', pdt: '' })

async function addSuper(u) {
  if (!u?.open_id) return
  const next = [...admins.value.super]
  if (next.some(a => a.open_id === u.open_id)) return
  next.push({ open_id: u.open_id, name: u.name })
  await adminApi.updateAdmins('super', next)
  queryStr.value.super = ''
  await refresh()
}
async function removeSuper(idx) {
  const next = [...admins.value.super]; next.splice(idx, 1)
  await adminApi.updateAdmins('super', next); await refresh()
}

async function addPdt(u) {
  if (!u?.open_id) return
  const next = [...admins.value.pdt]
  if (next.includes(u.open_id)) return
  next.push(u.open_id)
  await adminApi.updateAdmins('pdt', next)
  queryStr.value.pdt = ''
  await refresh()
}
async function removePdt(idx) {
  const next = [...admins.value.pdt]; next.splice(idx, 1)
  await adminApi.updateAdmins('pdt', next); await refresh()
}

async function addLtcAdmin(ltcId, u) {
  if (!u?.open_id) return
  const cur = admins.value.ltc[ltcId] || []
  if (cur.includes(u.open_id)) return
  const next = { ...admins.value.ltc, [ltcId]: [...cur, u.open_id] }
  await adminApi.updateAdmins('ltc', next); await refresh()
}
async function removeLtcAdmin(ltcId, idx) {
  const cur = [...(admins.value.ltc[ltcId] || [])]
  cur.splice(idx, 1)
  const next = { ...admins.value.ltc, [ltcId]: cur }
  await adminApi.updateAdmins('ltc', next); await refresh()
}
</script>

<template>
  <div class="admin-users">
    <section>
      <h3>Super Admin <span class="hint">— 系统超管,可改一切配置</span></h3>
      <div class="adder">
        <UserSearchInput
          v-model="queryStr.super"
          placeholder="搜索姓名添加 Super Admin…"
          @select="addSuper"
        />
      </div>
      <div v-if="!admins.super.length" class="empty">尚无 Super Admin。</div>
      <div v-else class="chips">
        <span v-for="(a, i) in admins.super" :key="a.open_id" class="chip">
          {{ a.name || a.open_id }}
          <button class="x" @click="removeSuper(i)" v-tooltip="'从 Super Admin 移除'">×</button>
        </span>
      </div>
    </section>

    <section>
      <h3>PDT Admin <span class="hint">— 本 PDT 管理者,可改 PDT/LTC/模块/Owner</span></h3>
      <div class="adder">
        <UserSearchInput
          v-model="queryStr.pdt"
          placeholder="搜索姓名添加 PDT Admin…"
          @select="addPdt"
        />
      </div>
      <div v-if="!admins.pdt.length" class="empty">尚无 PDT Admin。</div>
      <div v-else class="chips">
        <span v-for="(oid, i) in admins.pdt" :key="oid" class="chip">
          {{ nameOf(oid) }}
          <button class="x" @click="removePdt(i)" v-tooltip="'从 PDT Admin 移除'">×</button>
        </span>
      </div>
    </section>

    <section>
      <h3>LTC Admin <span class="hint">— 限于自己负责的 LTC</span></h3>
      <div v-if="!ltcs.length" class="empty">先创建 LTC 才能指派 LTC Admin。</div>
      <div v-for="l in ltcs" :key="l.id" class="ltc-block">
        <div class="ltc-title">{{ l.name }}</div>
        <div class="adder">
          <UserSearchInput
            placeholder="为本 LTC 添加管理员…"
            @select="u => addLtcAdmin(l.id, u)"
          />
        </div>
        <div class="chips">
          <span v-for="(oid, i) in (admins.ltc[l.id] || [])" :key="oid" class="chip">
            {{ nameOf(oid) }}
            <button class="x" @click="removeLtcAdmin(l.id, i)" v-tooltip="'移除此 LTC Admin'">×</button>
          </span>
          <span v-if="!(admins.ltc[l.id] || []).length" class="empty-inline">尚无</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.admin-users { max-width: 920px; }
section { margin-bottom: 24px; }
h3 { font-size: 14px; margin: 0 0 8px; }
.hint { color: var(--text-muted); font-weight: 400; font-size: 12px; margin-left: 6px; }
.adder { max-width: 380px; margin-bottom: 8px; }
.empty, .empty-inline { color: var(--text-muted); font-size: 13px; padding: 8px 0; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 8px; background: #eef2ff; color: #3730a3;
  border-radius: var(--radius); font-size: 13px;
}
.chip .x { padding: 0 4px; font-size: 14px; line-height: 1; background: transparent; border: none; color: inherit; }
.chip .x:hover { color: var(--status-red); }
.ltc-block { padding: 10px; background: #fafafa; border-radius: var(--radius); margin-bottom: 8px; }
.ltc-title { font-weight: 500; margin-bottom: 6px; }
</style>

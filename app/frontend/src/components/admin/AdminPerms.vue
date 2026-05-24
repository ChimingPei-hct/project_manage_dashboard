<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '../../composables/useAdminApi.js'
import { useAuth } from '../../composables/useAuth.js'
import { useContactCache } from '../../composables/useContactCache.js'
import UserSearchInput from '../UserSearchInput.vue'

const { me } = useAuth()
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

const queryStr = ref({ owner: '', admin: '' })

async function addOwner(u) {
  if (!u?.open_id) return
  const next = [...admins.value.super]
  if (next.some(a => a.open_id === u.open_id)) return
  next.push({ open_id: u.open_id, name: u.name })
  await adminApi.updateAdmins('super', next)
  queryStr.value.owner = ''
  await refresh()
}
async function removeOwner(idx) {
  const next = [...admins.value.super]; next.splice(idx, 1)
  await adminApi.updateAdmins('super', next); await refresh()
}

async function addAdmin(u) {
  if (!u?.open_id) return
  const next = [...admins.value.pdt]
  if (next.includes(u.open_id)) return
  next.push(u.open_id)
  await adminApi.updateAdmins('pdt', next)
  queryStr.value.admin = ''
  await refresh()
}
async function removeAdmin(idx) {
  const next = [...admins.value.pdt]; next.splice(idx, 1)
  await adminApi.updateAdmins('pdt', next); await refresh()
}
</script>

<template>
  <div class="admin-perms">
    <p class="intro">
      Owner 与管理员可<strong>编辑/删除任意卡片</strong>;其他人仅能管理自己创建的卡片。
    </p>

    <section>
      <h3>Owner <span class="hint">— 项目拥有者,可增删管理员</span></h3>
      <div v-if="me?.is_super" class="adder">
        <UserSearchInput
          v-model="queryStr.owner"
          placeholder="搜索姓名添加 Owner…"
          @select="addOwner"
        />
      </div>
      <div v-if="!admins.super.length" class="empty">尚未设置 Owner。</div>
      <div v-else class="chips">
        <span v-for="(a, i) in admins.super" :key="a.open_id" class="chip">
          {{ a.name || a.open_id }}
          <button
            v-if="me?.is_super"
            class="x"
            @click="removeOwner(i)"
            v-tooltip="'移除 Owner'"
          >×</button>
        </span>
      </div>
    </section>

    <section>
      <h3>管理员 <span class="hint">— 可编辑/删除任意卡片</span></h3>
      <div class="adder">
        <UserSearchInput
          v-model="queryStr.admin"
          placeholder="搜索姓名添加管理员…"
          @select="addAdmin"
        />
      </div>
      <div v-if="!admins.pdt.length" class="empty">尚无管理员。</div>
      <div v-else class="chips">
        <span v-for="(oid, i) in admins.pdt" :key="oid" class="chip">
          {{ nameOf(oid) }}
          <button class="x" @click="removeAdmin(i)" v-tooltip="'移除管理员'">×</button>
        </span>
      </div>
    </section>
  </div>
</template>

<style scoped>
.admin-perms { max-width: 600px; }
.intro {
  margin: 0 0 18px;
  padding: 10px 12px;
  background: var(--panel-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-muted);
  font-size: 13px;
}
.intro strong { color: var(--text); }
section { margin-bottom: 22px; }
h3 { font-size: 14px; margin: 0 0 8px; }
.hint { color: var(--text-muted); font-weight: 400; font-size: 12px; margin-left: 6px; }
.adder { max-width: 380px; margin-bottom: 8px; }
.empty { color: var(--text-muted); font-size: 13px; padding: 8px 0; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 8px; background: #eef2ff; color: #3730a3;
  border-radius: var(--radius); font-size: 13px;
}
.chip .x { padding: 0 4px; font-size: 14px; line-height: 1; background: transparent; border: none; color: inherit; cursor: pointer; }
.chip .x:hover { color: var(--status-red); }
</style>

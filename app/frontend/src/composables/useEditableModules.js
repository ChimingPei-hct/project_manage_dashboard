import { computed } from 'vue'
import { useAuth } from './useAuth.js'
import { useDashboard } from './useDashboard.js'
import { useAdmins } from './useAdmins.js'

/**
 * 计算当前用户可编辑 status 的 module_id 集合,镜像后端 can_edit_module_status:
 * - super / pdt admin → 全部
 * - module.owner_open_id == me → 该模块
 * - module.scope=ltc 且 me ∈ ltc_admins[ltc_id] → 该 LTC 下所有模块
 * 历史周(isReadonly)下统一返回 false。
 * 约束:design/10、design/13 §3.3 / §4.3 / §5.3。
 */
export function useEditableModules() {
  const { me } = useAuth()
  const { modules, isReadonly } = useDashboard()
  const { admins } = useAdmins()

  const editableSet = computed(() => {
    const set = new Set()
    if (isReadonly.value) return set
    const u = me.value
    if (!u?.open_id) return set
    const all = modules.value || []
    if (u.is_super || u.is_pdt_admin) {
      for (const m of all) set.add(m.id)
      return set
    }
    const ltcMap = admins.value?.ltc || {}
    const myLtcs = new Set(
      Object.entries(ltcMap)
        .filter(([, oids]) => Array.isArray(oids) && oids.includes(u.open_id))
        .map(([k]) => k)
    )
    for (const m of all) {
      if (m.owner_open_id === u.open_id) { set.add(m.id); continue }
      if (m.scope === 'ltc' && m.ltc_id && myLtcs.has(m.ltc_id)) set.add(m.id)
    }
    return set
  })

  function canEdit(moduleId) {
    return editableSet.value.has(moduleId)
  }

  return { canEdit, editableSet, isReadonly }
}

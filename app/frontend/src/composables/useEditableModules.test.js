/** @vitest-environment jsdom */
import { describe, it, expect, beforeEach } from 'vitest'
import { useAuth } from './useAuth.js'
import { useDashboard } from './useDashboard.js'
import { useAdmins } from './useAdmins.js'
import { useEditableModules } from './useEditableModules.js'

// 这些 composable 是模块单例;每个用例直接覆盖 ref 值即可。
function setState({ me, modules, admins, week = null }) {
  const auth = useAuth()
  auth.me.value = me
  const dash = useDashboard()
  dash.modules.value = modules
  dash.week.value = week
  const a = useAdmins()
  a.admins.value = admins
}

const MODULES = [
  { id: 'm-pdt', scope: 'pdt', owner_open_id: 'u_owner1' },
  { id: 'm-ltc1-a', scope: 'ltc', ltc_id: 'ltc1', owner_open_id: 'u_owner2' },
  { id: 'm-ltc1-b', scope: 'ltc', ltc_id: 'ltc1', owner_open_id: 'u_other' },
  { id: 'm-ltc2-a', scope: 'ltc', ltc_id: 'ltc2', owner_open_id: 'u_other' },
]

describe('useEditableModules', () => {
  beforeEach(() => {
    setState({ me: null, modules: [], admins: { super: [], pdt: [], ltc: {} } })
  })

  it('未登录 → 空集合', () => {
    setState({ me: null, modules: MODULES, admins: { super: [], pdt: [], ltc: {} } })
    const { editableSet } = useEditableModules()
    expect(editableSet.value.size).toBe(0)
  })

  it('super → 全部', () => {
    setState({
      me: { open_id: 'u_super', is_super: true, is_pdt_admin: true },
      modules: MODULES,
      admins: { super: [], pdt: [], ltc: {} },
    })
    const { canEdit } = useEditableModules()
    expect(canEdit('m-pdt')).toBe(true)
    expect(canEdit('m-ltc2-a')).toBe(true)
  })

  it('module owner → 仅自己的模块', () => {
    setState({
      me: { open_id: 'u_owner1', is_super: false, is_pdt_admin: false },
      modules: MODULES,
      admins: { super: [], pdt: [], ltc: {} },
    })
    const { canEdit } = useEditableModules()
    expect(canEdit('m-pdt')).toBe(true)
    expect(canEdit('m-ltc1-a')).toBe(false)
  })

  it('ltc admin → 该 ltc 下所有模块', () => {
    setState({
      me: { open_id: 'u_ltc1_admin', is_super: false, is_pdt_admin: false },
      modules: MODULES,
      admins: { super: [], pdt: [], ltc: { ltc1: ['u_ltc1_admin'] } },
    })
    const { canEdit } = useEditableModules()
    expect(canEdit('m-ltc1-a')).toBe(true)
    expect(canEdit('m-ltc1-b')).toBe(true)
    expect(canEdit('m-ltc2-a')).toBe(false)
    expect(canEdit('m-pdt')).toBe(false)
  })

  it('历史周(isReadonly)→ 一律不可编辑', () => {
    setState({
      me: { open_id: 'u_super', is_super: true, is_pdt_admin: true },
      modules: MODULES,
      admins: { super: [], pdt: [], ltc: {} },
      week: '2026-W21',
    })
    const { canEdit, isReadonly } = useEditableModules()
    expect(isReadonly.value).toBe(true)
    expect(canEdit('m-pdt')).toBe(false)
  })
})

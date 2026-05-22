/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import StatusEditDialog from './StatusEditDialog.vue'
import { api } from '../api/client.js'

const tooltipStub = { mounted() {}, updated() {}, unmounted() {} }

const MOD = {
  id: 'm1',
  name: '测试模块',
  sub_items: [{ id: 's1', name: '子项 A' }],
  kpi_fields: [{ key: 'progress', label: '进度', hint: '%' }],
}

function wrap(currentStatus = {}) {
  return mount(StatusEditDialog, {
    props: { open: true, module: MOD, current: currentStatus },
    global: { directives: { tooltip: tooltipStub } },
  })
}

describe('StatusEditDialog', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('非绿且 risk_note 为空时,保存按钮禁用并提示', async () => {
    const w = wrap({ module_color: 'yellow', sub_items_color: { s1: 'green' }, risk_note: '' })
    await flushPromises()
    const saveBtn = w.findAll('button').find(b => b.text().includes('保存'))
    expect(saveBtn.attributes('disabled')).toBeDefined()
    expect(w.text()).toContain('风险说明不能为空')
  })

  it('全绿时无需 risk_note,可保存', async () => {
    const putSpy = vi.spyOn(api, 'put').mockResolvedValue({})
    const w = wrap({ module_color: 'green', sub_items_color: { s1: 'green' }, risk_note: '' })
    await flushPromises()
    const saveBtn = w.findAll('button').find(b => b.text().includes('保存'))
    await saveBtn.trigger('click')
    await flushPromises()
    expect(putSpy).toHaveBeenCalledWith('/api/status/m1', expect.objectContaining({
      module_color: 'green',
      risk_note: '',
    }))
  })

  it('422 错误内联显示', async () => {
    const err = new Error('risk_note required when not all green')
    err.status = 422
    err.payload = { detail: 'risk_note required when not all green' }
    vi.spyOn(api, 'put').mockRejectedValue(err)
    const w = wrap({ module_color: 'red', sub_items_color: {}, risk_note: 'something' })
    await flushPromises()
    const saveBtn = w.findAll('button').find(b => b.text().includes('保存'))
    await saveBtn.trigger('click')
    await flushPromises()
    expect(w.text()).toContain('risk_note required')
  })

  it('403 错误以 toast 形式提示', async () => {
    const err = new Error('forbidden')
    err.status = 403
    err.payload = { detail: 'forbidden' }
    vi.spyOn(api, 'put').mockRejectedValue(err)
    const w = wrap({ module_color: 'red', sub_items_color: {}, risk_note: '风险' })
    await flushPromises()
    const saveBtn = w.findAll('button').find(b => b.text().includes('保存'))
    await saveBtn.trigger('click')
    await flushPromises()
    expect(w.find('.toast').exists()).toBe(true)
    expect(w.find('.toast').text()).toContain('无权编辑')
  })
})

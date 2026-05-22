/** @vitest-environment jsdom */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusCell from './StatusCell.vue'

const tooltipStub = { mounted() {}, updated() {}, unmounted() {} }

function wrap(props) {
  return mount(StatusCell, { props, global: { directives: { tooltip: tooltipStub } } })
}

describe('StatusCell', () => {
  it('editable=false 时点击不触发 edit', async () => {
    const w = wrap({ color: 'green', editable: false })
    await w.find('.dot').trigger('click')
    expect(w.emitted('edit')).toBeFalsy()
  })

  it('editable=true 时点击触发 edit', async () => {
    const w = wrap({ color: 'yellow', editable: true })
    await w.find('.dot').trigger('click')
    expect(w.emitted('edit')).toBeTruthy()
  })
})

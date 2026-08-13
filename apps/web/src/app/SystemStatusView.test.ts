import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'

import { messages } from './i18n'
import SystemStatusView from './SystemStatusView.vue'

describe('SystemStatusView', () => {
  it('states the simulator-only scope and blocked production boundary', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages,
    })

    const wrapper = mount(SystemStatusView, {
      global: { plugins: [i18n] },
    })

    expect(wrapper.get('h1').text()).toBe('Lemoo 教育机器人云平台')
    expect(wrapper.text()).toContain('Gate 0 已通过')
    expect(wrapper.text()).toContain('真实设备与生产发布保持阻断')
    expect(wrapper.get('ul').attributes('aria-label')).toBe('工程状态')
  })
})

import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'

import type { DeviceResponse, SessionResponse } from '../shared/api/generated/web'
import type * as WebApi from '../shared/api/generated/web'
import { messages } from './i18n'
import SystemStatusView from './SystemStatusView.vue'

const api = vi.hoisted(() => ({
  createCommand: vi.fn(),
  createSession: vi.fn(),
  deleteSession: vi.fn(),
  getDevice: vi.fn(),
  getSession: vi.fn(),
  listDevices: vi.fn(),
}))

vi.mock('../shared/api/generated/web', async (importOriginal) => {
  const original = await importOriginal<typeof WebApi>()
  return {
    ...original,
    createCommandApiV1DeviceCommandsPost: api.createCommand,
    createSimulatorSessionApiV1SimulatorSessionPost: api.createSession,
    deleteSessionApiV1SessionDelete: api.deleteSession,
    getDeviceApiV1DevicesDeviceIdGet: api.getDevice,
    getSessionApiV1SessionGet: api.getSession,
    listDevicesApiV1DevicesGet: api.listDevices,
  }
})

const operatorSession: SessionResponse = {
  actor_id: 'USR-SIM-A-OPS-001',
  organization_id: '0198f001-6000-7000-8000-000000000001',
  roles: ['device_operator'],
  simulator_only: true,
  production_supported: false,
}

const adminSession: SessionResponse = {
  ...operatorSession,
  actor_id: 'USR-SIM-A-ORG-001',
  roles: ['organization_admin'],
}

const primaryDevice: DeviceResponse = {
  id: '0198f001-6200-7000-8000-000000000001',
  code: 'SIM-A-001',
  organization_id: '0198f001-6000-7000-8000-000000000001',
  site_id: '0198f001-6100-7000-8000-000000000001',
  model_code: 'SIM_EDU_ROBOT_V1',
  hardware_revision: 'sim-r1',
  lifecycle: 'active',
  certificate_status: 'active',
  presence: 'online',
  last_seen_at: '2026-08-14T02:00:00Z',
  reported_shadow_version: 3,
  reported_shadow: {
    firmware_major: 'sim-1',
    bootloader_major: 'sim-1',
  },
  is_synthetic: true,
  is_physical_hardware: false,
  production_supported: false,
}

const secondaryDevice: DeviceResponse = {
  id: '0198f001-6200-7000-8000-000000000002',
  code: 'SIM-A-002',
  organization_id: '0198f001-6000-7000-8000-000000000001',
  site_id: '0198f001-6100-7000-8000-000000000001',
  model_code: 'SIM_EDU_ROBOT_V1',
  hardware_revision: 'sim-r1',
  lifecycle: 'active',
  certificate_status: 'active',
  presence: 'offline',
  last_seen_at: null,
  reported_shadow_version: 0,
  reported_shadow: {},
  is_synthetic: true,
  is_physical_hardware: false,
  production_supported: false,
}

const devices: DeviceResponse[] = [primaryDevice, secondaryDevice]

function mountWorkspace() {
  const i18n = createI18n({
    legacy: false,
    locale: 'zh-CN',
    messages,
  })
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return mount(SystemStatusView, {
    attachTo: document.body,
    global: {
      plugins: [i18n, [VueQueryPlugin, { queryClient }]],
    },
  })
}

describe('SystemStatusView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = ''
    api.getSession.mockRejectedValue(new Error('authentication required'))
    api.createSession.mockResolvedValue(operatorSession)
    api.listDevices.mockResolvedValue({ items: devices, next_cursor: null })
    api.getDevice.mockResolvedValue(primaryDevice)
    api.deleteSession.mockResolvedValue(undefined)
    api.createCommand.mockResolvedValue({
      command_type: 'refresh_shadow',
      created_at: '2026-08-14T02:01:00Z',
      device_id: primaryDevice.id,
      expires_at: '2026-08-14T02:03:00Z',
      id: '0198f001-6500-7000-8000-000000000001',
      idempotency_key: '0198f001-5200-7000-8000-000000000001',
      organization_id: operatorSession.organization_id,
      production_supported: false,
      reason: '核对模拟设备 Shadow',
      requested_by: operatorSession.actor_id,
      state: 'approved',
      updated_at: '2026-08-14T02:01:00Z',
    })
  })

  it('enters the workspace through an explicit synthetic actor session', async () => {
    const wrapper = mountWorkspace()
    await flushPromises()

    expect(wrapper.get('h1').text()).toBe('进入模拟器工作台')
    expect(wrapper.text()).toContain('仅限合成身份与虚拟设备')
    expect(wrapper.find('table').exists()).toBe(false)

    await wrapper.get('select[name="simulator-actor"]').setValue('org_a_operator')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(api.createSession).toHaveBeenCalledWith({ actor: 'org_a_operator' })
    expect(wrapper.get('h1').text()).toBe('设备运维')
    expect(wrapper.text()).toContain('ORG-SIM-A')
    expect(wrapper.text()).toContain('2 台虚拟设备')
  })

  it('supports scannable filters and an API-backed device detail', async () => {
    api.getSession.mockResolvedValue(operatorSession)
    const wrapper = mountWorkspace()
    await flushPromises()

    expect(wrapper.get('[aria-label="设备概览"]').text()).toContain('在线1')
    expect(wrapper.get('table').text()).toContain('SIM-A-001')
    expect(wrapper.get('table').text()).toContain('离线')

    await wrapper.get('input[type="search"]').setValue('002')
    expect(wrapper.get('tbody').text()).not.toContain('SIM-A-001')
    expect(wrapper.get('tbody').text()).toContain('SIM-A-002')
    await wrapper.get('input[type="search"]').setValue('not-present')
    expect(wrapper.text()).toContain('没有符合当前筛选条件的虚拟设备')
    await wrapper.get('input[type="search"]').setValue('')

    await wrapper.get('button[aria-label="查看 SIM-A-001 详情"]').trigger('click')
    await flushPromises()

    expect(api.getDevice).toHaveBeenCalledWith(primaryDevice.id, undefined)
    expect(wrapper.get('[aria-labelledby="device-detail-title"]').text()).toContain('Shadow v3')
    expect(wrapper.get('[aria-labelledby="device-detail-title"]').text()).toContain(
      'firmware_major',
    )
    await wrapper.get('button[aria-label="关闭设备详情"]').trigger('click')
    expect(wrapper.find('[aria-labelledby="device-detail-title"]').exists()).toBe(false)

    api.getDevice.mockResolvedValue({ ...secondaryDevice, lifecycle: 'suspended' })
    await wrapper.get('button[aria-label="查看 SIM-A-002 详情"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('已暂停')
    expect(wrapper.text()).toContain('设备尚未上报 Shadow')
    expect(wrapper.get('[data-command-trigger]').attributes('disabled')).toBeDefined()
  })

  it('requires a reason and confirms the only allowed command with an accessible receipt', async () => {
    api.getSession.mockResolvedValue(operatorSession)
    const wrapper = mountWorkspace()
    await flushPromises()
    await wrapper.get('button[aria-label="查看 SIM-A-001 详情"]').trigger('click')
    await flushPromises()

    const trigger = wrapper.get('[data-command-trigger]')
    await trigger.trigger('click')
    await wrapper.vm.$nextTick()
    let reason = wrapper.get('textarea[name="command-reason"]')
    expect(document.activeElement).toBe(reason.element)

    await wrapper.get('form[aria-label="确认刷新 Shadow"]').trigger('keydown', { key: 'Escape' })
    await wrapper.vm.$nextTick()
    expect(wrapper.find('form[aria-label="确认刷新 Shadow"]').exists()).toBe(false)
    const restoredTrigger = wrapper.get('[data-command-trigger]')
    expect(document.activeElement).toBe(restoredTrigger.element)
    await restoredTrigger.trigger('click')
    await wrapper.vm.$nextTick()
    reason = wrapper.get('textarea[name="command-reason"]')

    await reason.setValue('x')
    await wrapper.get('form[aria-label="确认刷新 Shadow"]').trigger('submit')
    expect(wrapper.get('[role="alert"]').text()).toContain('至少输入 3 个字符')
    expect(api.createCommand).not.toHaveBeenCalled()

    await reason.setValue('核对模拟设备 Shadow')
    await wrapper.get('form[aria-label="确认刷新 Shadow"]').trigger('submit')
    await flushPromises()

    expect(api.createCommand).toHaveBeenCalledOnce()
    expect(api.createCommand.mock.calls[0]?.[0]).toMatchObject({
      command_type: 'refresh_shadow',
      device_id: primaryDevice.id,
      parameters: {},
      reason: '核对模拟设备 Shadow',
    })
    expect(api.createCommand.mock.calls[0]?.[1]?.headers).toHaveProperty('Idempotency-Key')
    expect(wrapper.get('[aria-live="polite"]').text()).toContain('命令已受理')
    expect(wrapper.text()).toContain('approved')
  })

  it('does not expose command controls to a read-only organization administrator', async () => {
    api.getSession.mockResolvedValue(adminSession)
    const wrapper = mountWorkspace()
    await flushPromises()
    await wrapper.get('button[aria-label="查看 SIM-A-001 详情"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前身份仅可查看设备事实')
    expect(wrapper.find('button[data-command-trigger]').exists()).toBe(false)
  })

  it('fails visibly without inventing device state when the API is unavailable', async () => {
    api.getSession.mockResolvedValue(operatorSession)
    api.listDevices.mockRejectedValue(new Error('database unavailable'))
    const wrapper = mountWorkspace()
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('设备数据暂不可用')
    expect(wrapper.get('[role="alert"]').text()).toContain('不会显示伪造的在线状态')
    expect(wrapper.find('table').exists()).toBe(false)

    await wrapper.get('[role="alert"] button').trigger('click')
    expect(api.listDevices).toHaveBeenCalledTimes(2)
  })

  it('reports a rejected command and supports refresh plus session exit', async () => {
    api.getSession.mockResolvedValue(operatorSession)
    api.createCommand.mockRejectedValue(new Error('broker unavailable'))
    const wrapper = mountWorkspace()
    await flushPromises()

    await wrapper.get('.section-heading .quiet-button').trigger('click')
    await flushPromises()
    expect(api.listDevices).toHaveBeenCalledTimes(2)

    await wrapper.get('button[aria-label="查看 SIM-A-001 详情"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-command-trigger]').trigger('click')
    await wrapper.get('textarea[name="command-reason"]').setValue('验证失败状态')
    await wrapper.get('form[aria-label="确认刷新 Shadow"]').trigger('submit')
    await flushPromises()
    expect(wrapper.get('.command-zone [role="alert"]').text()).toContain('命令未被受理')

    await wrapper.get('button[aria-label="退出模拟器会话"]').trigger('click')
    await flushPromises()
    expect(api.deleteSession).toHaveBeenCalledOnce()
    expect(wrapper.get('h1').text()).toBe('进入模拟器工作台')
  })
})

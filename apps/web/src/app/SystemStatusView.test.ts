import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'

import type { DeviceResponse, SessionResponse } from '../shared/api/generated/web'
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
  const original = await importOriginal<typeof import('../shared/api/generated/web')>()
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

const devices: DeviceResponse[] = [
  {
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
  },
  {
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
  },
]

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
    api.getDevice.mockResolvedValue(devices[0])
    api.deleteSession.mockResolvedValue(undefined)
    api.createCommand.mockResolvedValue({
      command_type: 'refresh_shadow',
      created_at: '2026-08-14T02:01:00Z',
      device_id: devices[0].id,
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

    expect(wrapper.get('[aria-label="设备概览"]').text()).toContain('在线 1')
    expect(wrapper.get('table').text()).toContain('SIM-A-001')
    expect(wrapper.get('table').text()).toContain('离线')

    await wrapper.get('input[type="search"]').setValue('002')
    expect(wrapper.get('tbody').text()).not.toContain('SIM-A-001')
    expect(wrapper.get('tbody').text()).toContain('SIM-A-002')
    await wrapper.get('input[type="search"]').setValue('')

    await wrapper.get('button[aria-label="查看 SIM-A-001 详情"]').trigger('click')
    await flushPromises()

    expect(api.getDevice).toHaveBeenCalledWith(devices[0].id, undefined)
    expect(wrapper.get('[aria-labelledby="device-detail-title"]').text()).toContain('Shadow v3')
    expect(wrapper.get('[aria-labelledby="device-detail-title"]').text()).toContain('firmware_major')
  })

  it('requires a reason and confirms the only allowed command with an accessible receipt', async () => {
    api.getSession.mockResolvedValue(operatorSession)
    const wrapper = mountWorkspace()
    await flushPromises()
    await wrapper.get('button[aria-label="查看 SIM-A-001 详情"]').trigger('click')
    await flushPromises()

    const trigger = wrapper.get('button', { text: '准备刷新 Shadow' })
    await trigger.trigger('click')
    await wrapper.vm.$nextTick()
    const reason = wrapper.get('textarea[name="command-reason"]')
    expect(document.activeElement).toBe(reason.element)

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
      device_id: devices[0].id,
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
  })
})

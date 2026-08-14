import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, ref } from 'vue'

import {
  createCommandApiV1DeviceCommandsPost,
  createSimulatorSessionApiV1SimulatorSessionPost,
  deleteSessionApiV1SessionDelete,
  getDeviceApiV1DevicesDeviceIdGet,
  getSessionApiV1SessionGet,
  listDevicesApiV1DevicesGet,
  type DeviceResponse,
  type SessionResponse,
  type SimulatorSessionRequestActor,
} from '../shared/api/generated/web'

const SESSION_KEY = ['api', 'v1', 'session'] as const

function organizationLabel(organizationId: string | null | undefined): string {
  if (organizationId === '0198f001-6000-7000-8000-000000000001') return 'ORG-SIM-A'
  if (organizationId === '0198f001-6000-7000-8000-000000000002') return 'ORG-SIM-B'
  return '跨机构支持'
}

function siteLabel(siteId: string | null): string {
  if (siteId === '0198f001-6100-7000-8000-000000000001') return 'SITE-SIM-A1'
  if (siteId === '0198f001-6100-7000-8000-000000000002') return 'SITE-SIM-B1'
  return '未分配场地'
}

export function useDeviceWorkspace() {
  const queryClient = useQueryClient()
  const search = ref('')
  const presenceFilter = ref('all')
  const selectedDeviceId = ref('')
  const commandReason = ref('')
  const commandValidationError = ref('')
  const liveMessage = ref('')

  const sessionQuery = useQuery<SessionResponse | null>({
    queryKey: SESSION_KEY,
    queryFn: getSessionApiV1SessionGet,
    retry: false,
  })

  const session = computed(() => sessionQuery.data.value ?? null)
  const signedIn = computed(() => Boolean(session.value))
  const canCreateCommand = computed(() => session.value?.roles.includes('device_operator') ?? false)

  const devicesQuery = useQuery({
    queryKey: computed(() => ['workspace', 'devices', session.value?.actor_id ?? 'anonymous']),
    queryFn: () => listDevicesApiV1DevicesGet({ limit: 100 }),
    enabled: signedIn,
    retry: false,
  })

  const devices = computed(() => devicesQuery.data.value?.items ?? [])
  const visibleDevices = computed(() => {
    const needle = search.value.trim().toLocaleLowerCase()
    return devices.value.filter((device) => {
      const matchesPresence =
        presenceFilter.value === 'all' || device.presence === presenceFilter.value
      const matchesSearch =
        needle.length === 0 ||
        `${device.code} ${device.model_code} ${siteLabel(device.site_id)}`
          .toLocaleLowerCase()
          .includes(needle)
      return matchesPresence && matchesSearch
    })
  })

  const counts = computed(() => ({
    total: devices.value.length,
    online: devices.value.filter((device) => device.presence === 'online').length,
    attention: devices.value.filter(
      (device) => device.presence !== 'online' || device.lifecycle !== 'active',
    ).length,
  }))

  const deviceQuery = useQuery({
    queryKey: computed(() => ['workspace', 'device', selectedDeviceId.value]),
    queryFn: () => getDeviceApiV1DevicesDeviceIdGet(selectedDeviceId.value, undefined),
    enabled: computed(() => signedIn.value && selectedDeviceId.value.length > 0),
    retry: false,
  })

  const loginMutation = useMutation({
    mutationFn: (actor: SimulatorSessionRequestActor) =>
      createSimulatorSessionApiV1SimulatorSessionPost({ actor }),
    onSuccess: (createdSession) => {
      queryClient.setQueryData(SESSION_KEY, createdSession)
      liveMessage.value = `已使用合成身份 ${createdSession.actor_id} 进入工作台`
    },
  })

  const logoutMutation = useMutation({
    mutationFn: deleteSessionApiV1SessionDelete,
    onSuccess: () => {
      selectedDeviceId.value = ''
      queryClient.removeQueries({ queryKey: ['workspace'] })
      queryClient.setQueryData(SESSION_KEY, null)
      liveMessage.value = '模拟器会话已退出'
    },
  })

  const commandMutation = useMutation({
    mutationFn: (input: { device: DeviceResponse; reason: string }) =>
      createCommandApiV1DeviceCommandsPost(
        {
          command_type: 'refresh_shadow',
          device_id: input.device.id,
          expires_at: new Date(Date.now() + 2 * 60 * 1000).toISOString(),
          parameters: {},
          reason: input.reason,
        },
        { headers: { 'Idempotency-Key': crypto.randomUUID() } },
      ),
    onSuccess: (command) => {
      commandReason.value = ''
      commandValidationError.value = ''
      liveMessage.value = `命令已受理：${command.id}`
    },
  })

  function selectDevice(deviceId: string) {
    selectedDeviceId.value = deviceId
    commandMutation.reset()
    commandReason.value = ''
    commandValidationError.value = ''
  }

  function submitCommand(device: DeviceResponse) {
    const reason = commandReason.value.trim()
    if (reason.length < 3) {
      commandValidationError.value = '请至少输入 3 个字符，说明本次操作原因。'
      return false
    }
    commandValidationError.value = ''
    commandMutation.mutate({ device, reason })
    return true
  }

  return {
    canCreateCommand,
    commandMutation,
    commandReason,
    commandValidationError,
    counts,
    deviceQuery,
    devicesQuery,
    liveMessage,
    loginMutation,
    logoutMutation,
    organizationLabel,
    presenceFilter,
    search,
    selectDevice,
    selectedDeviceId,
    session,
    sessionQuery,
    signedIn,
    siteLabel,
    submitCommand,
    visibleDevices,
  }
}

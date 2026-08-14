<script setup lang="ts">
import {
  Activity,
  ArrowRight,
  Bot,
  Check,
  ChevronRight,
  CircleDot,
  Command,
  Cpu,
  LogOut,
  RefreshCw,
  Search,
  ShieldCheck,
  TriangleAlert,
  X,
} from '@lucide/vue'
import { computed, nextTick, ref } from 'vue'

import type { SimulatorSessionRequestActor } from '../shared/api/generated/web'
import { useDeviceWorkspace } from './useDeviceWorkspace'

const actor = ref<SimulatorSessionRequestActor>('org_a_operator')
const commandPanelOpen = ref(false)
const commandReasonInput = ref<HTMLTextAreaElement | null>(null)
const commandTrigger = ref<HTMLButtonElement | null>(null)

const actors: Array<{ value: SimulatorSessionRequestActor; label: string }> = [
  { value: 'org_a_operator', label: 'ORG-SIM-A · 设备运维' },
  { value: 'org_a_admin', label: 'ORG-SIM-A · 机构管理员' },
  { value: 'org_b_operator', label: 'ORG-SIM-B · 设备运维' },
  { value: 'org_b_admin', label: 'ORG-SIM-B · 机构管理员' },
]

const {
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
} = useDeviceWorkspace()

const selectedDevice = computed(() => deviceQuery.data.value)

function presenceLabel(presence: string): string {
  const labels: Record<string, string> = {
    online: '在线',
    offline: '离线',
    stale: '状态陈旧',
  }
  return labels[presence] ?? '状态未知'
}

function lifecycleLabel(lifecycle: string): string {
  return lifecycle === 'active' ? '已启用' : '已暂停'
}

function lastSeenLabel(value: string | null): string {
  if (!value) return '从未上报'
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'short',
    timeStyle: 'medium',
    timeZone: 'Asia/Shanghai',
  }).format(new Date(value))
}

async function openCommandPanel() {
  commandPanelOpen.value = true
  await nextTick()
  commandReasonInput.value?.focus()
}

function closeCommandPanel() {
  commandPanelOpen.value = false
  commandReason.value = ''
  commandValidationError.value = ''
  nextTick(() => commandTrigger.value?.focus())
}

function confirmCommand() {
  if (!selectedDevice.value) return
  if (submitCommand(selectedDevice.value)) commandPanelOpen.value = false
}

function closeDeviceDetail() {
  selectedDeviceId.value = ''
  commandPanelOpen.value = false
}
</script>

<template>
  <main id="main-content" class="workspace-shell" tabindex="-1">
    <p class="sr-only" aria-live="polite">{{ liveMessage }}</p>

    <section v-if="sessionQuery.isPending.value" class="entry-state" aria-label="正在检查会话">
      <RefreshCw class="spin" aria-hidden="true" />
      <p>正在检查模拟器会话…</p>
    </section>

    <section v-else-if="!signedIn" class="entry-shell" aria-labelledby="entry-title">
      <div class="entry-brand" aria-hidden="true"><Bot /></div>
      <p class="boundary-label"><ShieldCheck aria-hidden="true" /> Stage 1A · Simulator-only</p>
      <h1 id="entry-title">进入模拟器工作台</h1>
      <p class="entry-copy">
        仅限合成身份与虚拟设备。这里没有真实机构、个人数据、物理设备或生产入口。
      </p>

      <form class="entry-form" @submit.prevent="loginMutation.mutate(actor)">
        <label for="simulator-actor">选择合成身份</label>
        <select id="simulator-actor" v-model="actor" name="simulator-actor">
          <option v-for="option in actors" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <button class="primary-button" type="submit" :disabled="loginMutation.isPending.value">
          <span>{{ loginMutation.isPending.value ? '正在建立会话…' : '进入设备运维' }}</span>
          <ArrowRight aria-hidden="true" />
        </button>
      </form>

      <p v-if="loginMutation.isError.value" class="inline-error" role="alert">
        无法建立合成会话，请确认本地 FastAPI 服务已启动。
      </p>
      <p class="entry-footnote">会话使用 HttpOnly Cookie；凭证不会写入浏览器存储。</p>
    </section>

    <div v-else class="workspace-grid">
      <aside class="side-rail" aria-label="主导航">
        <div class="brand-lockup">
          <span class="brand-symbol" aria-hidden="true"><Bot /></span>
          <span><strong>Lemoo</strong><small>机器人云平台</small></span>
        </div>
        <nav aria-label="功能区">
          <a class="nav-item active" href="#device-list" aria-current="page">
            <Cpu aria-hidden="true" />设备
          </a>
          <span class="nav-item disabled" aria-disabled="true">
            <Activity aria-hidden="true" />运行事件<small>后续切片</small>
          </span>
        </nav>
        <div class="scope-guard">
          <ShieldCheck aria-hidden="true" />
          <div><strong>模拟边界已锁定</strong><span>生产与实机入口不可用</span></div>
        </div>
      </aside>

      <section class="workspace-main">
        <header class="topbar">
          <div>
            <p class="breadcrumb">设备云 / 运维工作台</p>
            <h1>设备运维</h1>
          </div>
          <div class="actor-chip">
            <span class="actor-avatar" aria-hidden="true">{{ session?.actor_id.slice(-3) }}</span>
            <span
              ><strong>{{ session?.actor_id }}</strong
              ><small>{{ organizationLabel(session?.organization_id) }}</small></span
            >
            <button
              type="button"
              aria-label="退出模拟器会话"
              :disabled="logoutMutation.isPending.value"
              @click="logoutMutation.mutate(undefined)"
            >
              <LogOut aria-hidden="true" />
            </button>
          </div>
        </header>

        <div class="simulator-ribbon" role="status">
          <CircleDot aria-hidden="true" />
          <strong>Simulator-only</strong>
          <span>{{ organizationLabel(session?.organization_id) }} · 合成租户 · 非生产</span>
        </div>

        <section class="content-column" aria-labelledby="fleet-title">
          <div class="section-heading">
            <div>
              <p class="kicker">FLEET OVERVIEW</p>
              <h2 id="fleet-title">虚拟设备舰队</h2>
              <p>{{ counts.total }} 台虚拟设备 · 当前数据来自 FastAPI 控制面</p>
            </div>
            <button class="quiet-button" type="button" @click="devicesQuery.refetch()">
              <RefreshCw
                :class="{ spin: devicesQuery.isFetching.value }"
                aria-hidden="true"
              />刷新事实
            </button>
          </div>

          <dl class="metric-strip" aria-label="设备概览">
            <div>
              <dt>全部设备</dt>
              <dd>{{ counts.total }}</dd>
            </div>
            <div>
              <dt><span class="status-dot online" />在线</dt>
              <dd>{{ counts.online }}</dd>
            </div>
            <div>
              <dt><span class="status-dot attention" />需要关注</dt>
              <dd>{{ counts.attention }}</dd>
            </div>
            <div>
              <dt>运行范围</dt>
              <dd class="text-value">{{ organizationLabel(session?.organization_id) }}</dd>
            </div>
          </dl>

          <div id="device-list" class="fleet-panel">
            <div class="filter-bar">
              <label class="search-field">
                <span class="sr-only">搜索设备</span>
                <Search aria-hidden="true" />
                <input v-model="search" type="search" placeholder="搜索设备、型号或场地" />
              </label>
              <label class="select-field">
                <span>连接状态</span>
                <select v-model="presenceFilter">
                  <option value="all">全部状态</option>
                  <option value="online">在线</option>
                  <option value="offline">离线</option>
                  <option value="stale">状态陈旧</option>
                </select>
              </label>
            </div>

            <div v-if="devicesQuery.isPending.value" class="table-state" role="status">
              <RefreshCw class="spin" aria-hidden="true" />正在读取设备事实…
            </div>
            <div
              v-else-if="devicesQuery.isError.value"
              class="table-state error-state"
              role="alert"
            >
              <TriangleAlert aria-hidden="true" />
              <div>
                <strong>设备数据暂不可用</strong>
                <p>依赖异常期间不会显示伪造的在线状态。请恢复服务后重试。</p>
              </div>
              <button type="button" @click="devicesQuery.refetch()">重试</button>
            </div>
            <div v-else-if="visibleDevices.length === 0" class="table-state">
              <Search aria-hidden="true" />没有符合当前筛选条件的虚拟设备。
            </div>
            <div v-else class="table-scroll">
              <table>
                <caption class="sr-only">
                  当前合成机构中的虚拟设备
                </caption>
                <thead>
                  <tr>
                    <th>设备</th>
                    <th>连接状态</th>
                    <th>场地</th>
                    <th>版本</th>
                    <th>最近上报</th>
                    <th><span class="sr-only">操作</span></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="device in visibleDevices" :key="device.id">
                    <td data-label="设备">
                      <div class="device-identity">
                        <span class="robot-glyph" aria-hidden="true"><Bot /></span>
                        <span
                          ><strong>{{ device.code }}</strong
                          ><small>{{ device.model_code }}</small></span
                        >
                      </div>
                    </td>
                    <td data-label="连接状态">
                      <span class="state-pill" :class="device.presence">
                        <span class="status-dot" :class="device.presence" />{{
                          presenceLabel(device.presence)
                        }}
                      </span>
                    </td>
                    <td data-label="场地">{{ siteLabel(device.site_id) }}</td>
                    <td data-label="版本">Shadow v{{ device.reported_shadow_version }}</td>
                    <td data-label="最近上报">{{ lastSeenLabel(device.last_seen_at) }}</td>
                    <td class="row-action">
                      <button
                        type="button"
                        :aria-label="`查看 ${device.code} 详情`"
                        @click="selectDevice(device.id)"
                      >
                        <ChevronRight aria-hidden="true" />
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </section>

      <aside v-if="selectedDeviceId" class="detail-drawer" aria-labelledby="device-detail-title">
        <header class="drawer-header">
          <div>
            <p>DEVICE FACTS</p>
            <h2 id="device-detail-title">设备详情</h2>
          </div>
          <button type="button" aria-label="关闭设备详情" @click="closeDeviceDetail">
            <X aria-hidden="true" />
          </button>
        </header>
        <div v-if="deviceQuery.isPending.value" class="drawer-state" role="status">
          <RefreshCw class="spin" aria-hidden="true" />正在读取设备详情…
        </div>
        <div v-else-if="deviceQuery.isError.value" class="drawer-state error-state" role="alert">
          <TriangleAlert aria-hidden="true" />设备详情不可用，未显示推测数据。
        </div>
        <div v-else-if="selectedDevice" class="drawer-body">
          <div class="device-title-row">
            <span class="robot-glyph large" aria-hidden="true"><Bot /></span>
            <div>
              <h3>{{ selectedDevice.code }}</h3>
              <p>{{ selectedDevice.model_code }} · {{ selectedDevice.hardware_revision }}</p>
            </div>
            <span class="state-pill" :class="selectedDevice.presence"
              ><span class="status-dot" :class="selectedDevice.presence" />{{
                presenceLabel(selectedDevice.presence)
              }}</span
            >
          </div>

          <dl class="fact-grid">
            <div>
              <dt>生命周期</dt>
              <dd>{{ lifecycleLabel(selectedDevice.lifecycle) }}</dd>
            </div>
            <div>
              <dt>证书状态</dt>
              <dd>{{ selectedDevice.certificate_status }}</dd>
            </div>
            <div>
              <dt>场地</dt>
              <dd>{{ siteLabel(selectedDevice.site_id) }}</dd>
            </div>
            <div>
              <dt>最近上报</dt>
              <dd>{{ lastSeenLabel(selectedDevice.last_seen_at) }}</dd>
            </div>
          </dl>

          <section class="shadow-panel" aria-labelledby="shadow-title">
            <div>
              <p>REPORTED SHADOW</p>
              <h3 id="shadow-title">Shadow v{{ selectedDevice.reported_shadow_version }}</h3>
            </div>
            <dl v-if="Object.keys(selectedDevice.reported_shadow).length">
              <div v-for="(value, key) in selectedDevice.reported_shadow" :key="key">
                <dt>{{ key }}</dt>
                <dd>{{ value }}</dd>
              </div>
            </dl>
            <p v-else class="empty-copy">设备尚未上报 Shadow。</p>
          </section>

          <section class="command-zone" aria-labelledby="command-title">
            <div class="command-heading">
              <span aria-hidden="true"><Command /></span>
              <div>
                <h3 id="command-title">受控操作</h3>
                <p>唯一允许的命令：refresh_shadow</p>
              </div>
            </div>

            <template v-if="canCreateCommand">
              <button
                v-if="!commandPanelOpen"
                ref="commandTrigger"
                class="primary-button compact"
                type="button"
                data-command-trigger
                :disabled="selectedDevice.presence !== 'online'"
                @click="openCommandPanel"
              >
                <RefreshCw aria-hidden="true" />准备刷新 Shadow
              </button>
              <p v-if="selectedDevice.presence !== 'online'" class="constraint-copy">
                离线设备不能接受命令；系统不会假装已下发。
              </p>

              <form
                v-if="commandPanelOpen"
                class="command-confirmation"
                aria-label="确认刷新 Shadow"
                @keydown.esc.prevent="closeCommandPanel"
                @submit.prevent="confirmCommand"
              >
                <label for="command-reason">操作原因</label>
                <textarea
                  id="command-reason"
                  ref="commandReasonInput"
                  v-model="commandReason"
                  name="command-reason"
                  rows="3"
                  aria-describedby="command-reason-help command-reason-error"
                />
                <p id="command-reason-help">原因将进入合成审计记录，3–240 个字符。</p>
                <p v-if="commandValidationError" id="command-reason-error" role="alert">
                  {{ commandValidationError }}
                </p>
                <div class="confirmation-actions">
                  <button type="button" class="quiet-button" @click="closeCommandPanel">
                    取消
                  </button>
                  <button
                    class="primary-button compact"
                    type="submit"
                    :disabled="commandMutation.isPending.value"
                  >
                    <Check aria-hidden="true" />{{
                      commandMutation.isPending.value ? '提交中…' : '确认单设备操作'
                    }}
                  </button>
                </div>
              </form>
            </template>
            <p v-else class="constraint-copy">当前身份仅可查看设备事实，不能创建命令。</p>

            <div v-if="commandMutation.isSuccess.value" class="command-receipt">
              <Check aria-hidden="true" />
              <div>
                <strong>命令已受理</strong
                ><span
                  >{{ commandMutation.data.value?.state }} ·
                  {{ commandMutation.data.value?.id }}</span
                >
              </div>
            </div>
            <div v-if="commandMutation.isError.value" class="inline-error" role="alert">
              命令未被受理。服务端没有返回成功事实，请核对设备状态后重试。
            </div>
          </section>

          <p class="physical-boundary">
            <ShieldCheck aria-hidden="true" />虚拟设备 · is_physical_hardware=false ·
            production_supported=false
          </p>
        </div>
      </aside>
    </div>
  </main>
</template>

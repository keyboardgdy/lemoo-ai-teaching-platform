import { createI18n } from 'vue-i18n'

export const messages = {
  'zh-CN': {
    title: 'Lemoo 教育机器人云平台',
    stage: '阶段 1A · 模拟器工程基线',
    description: '当前只允许合成租户、虚拟设备和非生产环境。',
    gate0: 'Gate 0 已通过',
    w2: 'W2 工具链建设中',
    blocked: '真实设备与生产发布保持阻断',
  },
  en: {
    title: 'Lemoo Education Robot Cloud',
    stage: 'Stage 1A · Simulator engineering baseline',
    description:
      'Only synthetic tenants, virtual devices and non-production environments are allowed.',
    gate0: 'Gate 0 passed',
    w2: 'W2 toolchain in progress',
    blocked: 'Real devices and production releases remain blocked',
  },
} as const

export const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  fallbackLocale: 'en',
  messages,
})

import { expect, test } from '@playwright/test'

test('synthetic operator completes the real device workspace request path', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: '进入模拟器工作台' })).toBeVisible()
  await expect(page.getByText('仅限合成身份与虚拟设备')).toBeVisible()

  await page.getByLabel('选择合成身份').selectOption('org_a_operator')
  await page.getByRole('button', { name: '进入设备运维' }).click()

  await expect(page.getByRole('heading', { name: '虚拟设备舰队' })).toBeVisible()
  await expect(page.locator('tbody tr')).toHaveCount(4)
  await expect(page.getByText('SIM-B-001', { exact: true })).toHaveCount(0)
  await expect(page.getByText('Simulator-only', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: '查看 SIM-A-001 详情' }).click()
  await expect(page.getByRole('heading', { name: 'Shadow v1' })).toBeVisible()
  await expect(page.getByText('is_physical_hardware=false')).toBeVisible()

  await page.getByRole('button', { name: '准备刷新 Shadow' }).click()
  await page.getByLabel('操作原因').fill('Playwright 合成设备 Shadow 验证')
  await page.getByRole('button', { name: '确认单设备操作' }).click()
  await expect(page.getByText('命令已受理', { exact: true })).toBeVisible()
  await expect(page.getByText('approved', { exact: false })).toBeVisible()
})

test('synthetic administrator remains read-only and tenant B sees only its two devices', async ({
  page,
}) => {
  await page.goto('/')
  await page.getByLabel('选择合成身份').selectOption('org_a_admin')
  await page.getByRole('button', { name: '进入设备运维' }).click()
  await expect(page.locator('tbody tr')).toHaveCount(4)
  await page.getByRole('button', { name: '查看 SIM-A-001 详情' }).click()
  await expect(page.getByText('当前身份仅可查看设备事实')).toBeVisible()
  await expect(page.getByRole('button', { name: '准备刷新 Shadow' })).toHaveCount(0)

  await page.getByRole('button', { name: '关闭设备详情' }).click()
  await page.getByRole('button', { name: '退出模拟器会话' }).click()
  await page.getByLabel('选择合成身份').selectOption('org_b_operator')
  await page.getByRole('button', { name: '进入设备运维' }).click()
  await expect(page.locator('tbody tr')).toHaveCount(2)
  await expect(page.getByText('SIM-B-001', { exact: true })).toBeVisible()
  await expect(page.getByText('SIM-A-001', { exact: true })).toHaveCount(0)
})

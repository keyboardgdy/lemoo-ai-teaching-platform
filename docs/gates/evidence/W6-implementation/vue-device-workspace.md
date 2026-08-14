# W6 实现证据：Vue 设备运维工作台

日期：2026-08-14；范围：Stage 1A Simulator-only、合成数据、非生产。

本切片将 W2 的工程状态占位页替换为首个可操作的设备运维界面：

- 通过固定合成 Actor 建立 HttpOnly Cookie 会话，不把 Token 或设备凭证写入浏览器
  存储；机构管理员与设备运维角色呈现不同的命令权限。
- 设备列表、搜索、连接状态筛选、状态统计和设备详情均通过 Orval 生成的 Fetch
  Client 读取 FastAPI 事实，不在前端复制 API 类型或手写备用数据。
- 详情展示 Lifecycle、Certificate、Site、Last Seen 与 Reported Shadow；缺失、离线、
  空结果和依赖失败均显式呈现，不推测或伪造在线、Shadow 或成功状态。
- 唯一命令入口固定为单设备 `refresh_shadow`，要求 3～240 字符的操作原因，使用
  CSRF Cookie/Header 和每次唯一 Idempotency Key；离线设备和无命令权限角色不能
  提交。
- Simulator-only、合成机构、虚拟设备、非实机和非生产边界在登录页、全局状态带、
  侧栏和设备详情中持续可见；Content、Teaching、AI、Diagnostics、Bulk Command、
  OTA 和生产入口未出现。
- 视觉方向为安静、紧凑、可扫描的日常运维工具；桌面使用稳定侧栏、事实表格和详情
  抽屉，移动端收敛为 390px 单列并保留设备详情操作入口。
- 无障碍实现使用原生表单/表格/按钮、跳转链接、可见焦点、至少 44px 的主要控件、
  文本化状态与错误、`aria-live` 命令回执、Escape 取消和焦点归还。

TDD 证据：RED Commit `d1349c8` 固定合成会话、列表/详情、筛选、权限、命令确认和
降级场景并产生 5 项预期失败；GREEN Commit `f65f459` 完成工作台、TanStack Query
状态边界、响应式样式和 Vite 本地 API 代理。

验证结果：

- `task verify`：PASS；后端 44 项、协议 27 项、前端 9 项；后端覆盖率 93.61%，
  前端覆盖率见下；Lint、Format、Pyright、Vue Typecheck、Build、Docs、Repo、
  Compose、Schema/OpenAPI 和 Orval 漂移检查全部通过。
- `task frontend:verify`：PASS；Orval 漂移、ESLint、Prettier、Vue TypeScript、
  Vitest、Coverage 和 Vite Production Build 全部通过。
- 前端测试：9 项 PASS；纳入范围的 Vue SFC 语句/行覆盖率 99.24%、分支 92.30%、
  函数 100%，均高于 90% 门禁。
- 真实本地纵切：`task infra:up` 与 `task seed` 后，通过 Vite 代理、FastAPI 和
  PostgreSQL 建立 ORG-SIM-A 运维会话；Playwright 使用本机 Chrome 观察到 4 行
  ORG-SIM-A 设备、一个全局 Simulator-only 边界、SIM-A-001 Shadow v1 详情和允许的
  单设备命令入口。
- 响应式视觉复核：1440×1000 登录、工作台和详情状态无重叠；390×844 页面
  `innerWidth=390`、`scrollWidth=390`，设备表收敛到设备/状态/详情入口。

联调同时确认：Windows 上直接以无 reload 的 Uvicorn CLI 启动时，ProactorEventLoop
与 Psycopg Async 不兼容；仓库正式 `task dev` 的 `--reload` 路径使用兼容事件循环并
通过本次联调。无 reload 的 Windows 控制台入口仍须在 W7 本地运行切片修复，不能把
首次 500 记录为通过。

本证据只证明设备列表/详情和命令请求 UI 的当前纵切，不代表 MQTT Runtime、设备
ACK/终态、遥测、事件、告警、SSE、Playwright Required Check、Simulator 故障注入或
Gate 3-Sim 已完成，也不授权真实设备、真实机构、个人数据、外部 Provider、内容、
教学、AI、诊断、批量命令、OTA 或生产。

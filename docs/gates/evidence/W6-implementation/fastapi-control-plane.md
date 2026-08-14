# W6 实现证据：FastAPI 设备控制面

日期：2026-08-14；范围：Stage 1A Simulator-only、合成数据、非生产。

本切片交付了首个可运行的 Web API 纵切：

- 固定合成 Actor 的 HttpOnly Session Cookie 与 Double-submit CSRF；Web 会话与
  Device mTLS 契约保持分离。
- `/api/v1/session`、设备列表/详情、单设备 `refresh_shadow` 命令创建/查询；
  Content、Teaching、AI、Diagnostics、Bulk Command 和 OTA 路由不存在。
- 所有错误运行时与 OpenAPI 均使用 RFC 9457 `application/problem+json`，带稳定
  `code` 和服务端 `request_id`；跨租户资源与不存在资源返回相同 404 形状。
- 数据库连接在每个事务中切换到 `NOBYPASSRLS` 应用角色并设置租户上下文；
  命令、审计和 Outbox 在同一事务提交。
- 相同 Idempotency Key 与相同请求返回既有命令；不同请求返回 409；非法角色、
  非活动设备和错误 CSRF 均在产生副作用前拒绝。
- `task seed` 只写入 PILOT-001 的 2 个合成机构、2 个合成场地和 6 台虚拟设备。
- OpenAPI 3.1 生成物执行漂移检查；Vue 客户端由 Orval 生成，使用原生 Fetch
  与唯一请求适配器，不引入 Axios。

TDD 证据：RED Commit `92db3d4` 因控制面模块不存在而在测试收集阶段失败；GREEN
Commit `71ba63a` 完成 API、PostgreSQL Adapter、合成 Seed、OpenAPI 与 Fetch 客户端。

验证结果：

- `task verify`：PASS；后端 44 项、协议 27 项、前端 4 项；后端覆盖率 93.61%，
  前端既有纳入范围覆盖率 100%；Lint、Format、Pyright、Vue Typecheck、Build、
  Docs、Repo、Compose 与 Schema/OpenAPI 漂移检查均通过。
- 真实 PostgreSQL API 集成：PASS；临时 `LOGIN NOSUPERUSER NOBYPASSRLS` 角色完成
  ORG A 列表、ORG B 隐藏、命令创建/重放/冲突、角色拒绝、停用设备拒绝，以及
  Command/Audit/Outbox 各一条的原子性断言。
- `task migrate:test`：PASS；空库升级、重复升级、RLS、审计不可篡改、降级与
  再升级继续通过。

本证据不代表 Vue 设备工作台、MQTT Runtime、Simulator、SSE、告警页面、E2E 或
Gate 3-Sim 已完成；也不授权真实设备、真实机构、个人数据、外部 Provider、内容、
教学、AI、诊断、批量命令、OTA 或生产。

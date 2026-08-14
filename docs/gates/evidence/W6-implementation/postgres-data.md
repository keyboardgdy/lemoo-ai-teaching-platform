# W6 实现证据：PostgreSQL 数据边界

日期：2026-08-14；范围：Stage 1A Simulator-only、合成数据、非生产。

本切片建立了设备云控制面的 PostgreSQL 事实层：

- Alembic 初始迁移创建 12 张 Stage 1A 业务表；主键使用 PostgreSQL 18
  `uuidv7()`，时间使用 `timestamptz`。
- 遥测表按 `received_at` 原生分区，并提供默认分区，避免未建立时间分区时丢失消息。
- 11 张租户表启用并强制 RLS；事务使用 `app.organization_id` 设置租户上下文，
  缺失上下文时查询结果为空。
- 命令表以 `(organization_id, idempotency_key)` 唯一约束作为幂等最终防线。
- 审计表通过数据库 Trigger 拒绝 `UPDATE` 和 `DELETE`；Outbox 与业务事实共用
  PostgreSQL 事务边界。
- API 和 Worker 不自动执行迁移；迁移由显式 Task/CI 步骤运行。

TDD 证据：RED Commit `97ee2a8` 在数据库 Metadata 和迁移不存在时失败；GREEN
Commit `b6db55c` 完成模型、迁移、RLS、审计保护和真实数据库验证。

验证结果：

- `task verify`：PASS；后端 35 项、协议 27 项、前端 1 项，后端覆盖率
  92.42%，前端覆盖率 100%，Lint、Format、Pyright、Build、Docs、Repo、Compose
  配置均通过。
- `task migrate:test`：PASS；覆盖空库升级、重复升级、ORG A/B 跨租户读写阻断、
  缺失租户上下文 fail-closed、审计篡改阻断、降级和再升级。
- GitHub `backend` 必检任务已接入 PostgreSQL 18 服务和相同迁移攻击套件。

本证据只证明 PostgreSQL Schema、迁移和数据库隔离边界，不代表 Web API、MQTT
运行时、Simulator、SSE、对象访问、E2E 或 Gate 3-Sim 已完成；更不授权真实设备、
真实机构、个人数据、外部 Provider、内容、教学、AI、诊断、批量命令、OTA 或生产。

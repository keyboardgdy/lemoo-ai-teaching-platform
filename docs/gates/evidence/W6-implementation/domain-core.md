# W6 实现证据：领域内核

日期：2026-08-14；范围：Stage 1A Simulator-only、合成数据、非生产。

首个正式业务代码纵切已实现，不再是空骨架：

- `identity`：本机构 RBAC、跨机构不泄漏拒绝、只读 Support + Reason、冲突上下文 Fail Closed。
- `device_fleet`：设备绑定/生命周期、证书状态、在线时效、Boot/Sequence 判定、Reported Shadow 单调版本。
- `device_operations`：唯一 `refresh_shadow`、设备状态/组织/Expiry/参数验证、命令状态机、终态不回退与 Idempotency Key 冲突。
- 架构测试保证 Domain 不导入 FastAPI、SQLAlchemy、Redis、MQTT、S3 或 Dramatiq，跨模块只依赖 `public.py`。

TDD：RED Commit `3a409dc` 因三个领域模块不存在而收集失败；GREEN Commit `87e02f7` 后领域测试 20/20 通过。仓库后端共 27 个测试通过，覆盖率 92.12%，Pyright 0 error。

这只是纯领域层证据，不代表 PostgreSQL/RLS、API、MQTT、Simulator、E2E、G1/HIL 或生产已完成；对应证据将在后续实现 PR 增量补齐。

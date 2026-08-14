# W5c 核心 Job 与命令状态契约证据

> 工作包：W5c 冻结核心 Job 与命令状态契约
>
> 执行日期：2026-08-14
>
> 执行人：OpenAI Codex
>
> 最终责任人：高端阳
>
> 范围：Stage 1A、Simulator-only、合成数据、非生产

## 结论

W5c 的 Job Envelope、Progress、Result、Error、Outbox Event、核心 Job Catalog 与 `refresh_shadow` Command 状态机已冻结并通过可执行契约测试。W5a～W5c 的 Stage 1A 机器契约至此完整；WebSocket、Content、Teaching、AI、Diagnostics 与 OTA 继续保持未开始/禁用。

## TDD 证据

| 阶段 | Commit | 命令 | 结果 |
|---|---|---|---|
| RED：定义 Job/Outbox/Command 契约 | `7f74432` | `pytest packages/protocol-schemas/tests/test_job_contracts.py -q` | 8 failed；权威契约尚不存在 |
| GREEN：冻结核心 Job 契约 | `810acc8` | 同上 | 8 passed |
| RED：补充命令幂等冲突 | `c10a225` | 同上 | 1 failed, 7 passed |
| GREEN：冻结重复与冲突语义 | `39a73d2` | `task test:protocol` | 26 passed |

## 已验证行为

| 类别 | 确定结果 |
|---|---|
| Job 白名单 | 仅 `device.command.dispatch`、`device.command.expire`、`device.presence.reconcile` |
| 未知/未来 Job | 未知类型及 AI/Content/Diagnostics/OTA/Teaching 前缀不执行，进入 Dead Letter |
| 交付/幂等 | At-least-once；重复 Job ID 返回既有 Progress/Result；Outbox 消费者按 Event/Business ID 去重 |
| 重试 | 有界指数 Full Jitter；按错误分类决定 Retry；达到 Catalog 最大尝试后 Dead Letter |
| 超时/取消 | 过期 Deadline 不执行；Queued 直接取消；Running 协作取消后进入有界超时 |
| 进度/结果 | 进度回退忽略并审计；终态 Result 不可变 |
| Command | 合法转换白名单、同状态幂等、非法转换拒绝、迟到 ACK 不回退终态、设备端二次校验 |
| 创建幂等 | Key 作用域为 Organization/Device/Command Type；相同请求返回已有命令，不同参数冲突拒绝并审计 |
| 过期创建 | 以 Server Receive Time 判断，拒绝且不创建 Outbox 副作用 |

## 权威路径

- `packages/protocol-schemas/jobs/*.schema.json`
- `packages/protocol-schemas/jobs/job-catalog.v1.json`
- `packages/protocol-schemas/jobs/execution-policy.v1.json`
- `packages/protocol-schemas/jobs/command-state-machine.v1.json`
- `packages/protocol-schemas/jobs/fixtures/`
- `packages/protocol-schemas/tests/test_job_contracts.py`

## 安全与范围说明

- Job Payload 只允许稳定 ID 和有界参数，不允许 ORM 对象、文件、Prompt、Credential 或个人数据。
- 本工作包没有实现 Worker、Dispatcher、Scheduler、Handler 或真实异步副作用。
- 本证据不是法律意见、合规认证、生产授权、真实设备兼容、G1/HIL 或真实机构试点批准。

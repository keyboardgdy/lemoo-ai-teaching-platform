# W5a MQTT/ACL 契约证据

> 工作包：W5a 冻结 MQTT/ACL 契约
>
> 执行日期：2026-08-14
>
> 执行人：OpenAI Codex
>
> 最终责任人：高端阳
>
> 范围：Stage 1A、Simulator-only、合成数据、非生产

## 结论

W5a 的 Simulator-first MQTT v1 契约已实现并由可执行测试冻结。契约覆盖 Topic、设备 ACL、QoS、Retain、Persistent Session、Will、统一 Envelope、Reported Shadow、Telemetry、Device Event、唯一允许命令 `refresh_shadow`、Command ACK 与兼容策略。

本工作包没有实现 Broker、Gateway、Device/Web API 或业务 Handler，也没有声称兼容真实硬件。真实设备 Capture、HIL 与 G2-Device 最终批准仍保持阻断。

## TDD 证据

| 阶段 | Commit | 命令 | 结果 |
|---|---|---|---|
| RED：定义权威产物与正/负向行为 | `f40c649` | `uv run --project apps/cloud pytest packages/protocol-schemas/tests/test_mqtt_contracts.py -q` | 9 failed；均因 MQTT 契约、策略或 Fixture 尚不存在 |
| GREEN：冻结 Schema、ACL 与 Fixture | `e80a06c` | 同上 | 9 passed |
| RED：定义重复、乱序、重启、过期、超限结果 | `466d190` | 同上 | 1 failed, 9 passed；缺少乱序等语义策略 |
| GREEN：冻结语义拒绝策略 | `9b8349b` | `task test:protocol` | 10 passed |

## 可重复验证

```text
task schemas:check
task test:protocol
```

## 已验证行为

| 类别 | 确定结果 |
|---|---|
| 独立身份 | 设备只能发布/订阅自身 Device ID Topic；跨设备、通配符及错误方向默认拒绝 |
| Schema | Draft 2020-12；未知 Major、缺字段、未知字段、伪造身份和物理设备声明拒绝 |
| 消息策略 | QoS、Retain、Session Expiry、Will、最大包与 inflight 上限已冻结 |
| 幂等 | 重复消息只 ACK，不重复应用业务效果 |
| 顺序 | 同一 Boot 的低 Sequence 不得回退当前状态；新 Boot 建立新顺序流 |
| 命令 | 只允许 `refresh_shadow`；过期命令拒绝并返回 expired ACK |
| 超限 | 超过 65,536 bytes 的 Packet 在 Schema 解析前拒绝并审计 |
| 范围标志 | 所有消息必须显式为 `is_physical_hardware=false`、`production_supported=false` |

## 权威路径

- `packages/protocol-schemas/mqtt/*.schema.json`
- `packages/protocol-schemas/mqtt/topic-policy.v1.json`
- `packages/protocol-schemas/mqtt/acl.v1.json`
- `packages/protocol-schemas/mqtt/compatibility.v1.json`
- `packages/protocol-schemas/mqtt/fixtures/`
- `packages/protocol-schemas/tests/test_mqtt_contracts.py`

## 安全与范围说明

- 证书身份、Client ID、Topic Device ID 与 Payload Device ID 的四方一致性是后续 Broker/Gateway 实现必须遵守的契约；W5a 只冻结规则。
- Content、Teaching、AI、Diagnostic、Bulk Command 和 OTA 均没有 Topic、命令或处理路径。
- 本证据不是法律意见、合规认证、生产授权、真实设备兼容证明或真实机构试点批准。

## 契约勘误

2026-08-14 在数据库 Seed 设计前发现 Device ID Pattern 与 PILOT-001 六设备清单不一致；回归测试先复现后，将 MQTT/Device API 统一为仅允许 `SIM-A-001`～`004` 与 `SIM-B-001`～`002`，并拒绝 A-005、B-003 等范围外 ID。

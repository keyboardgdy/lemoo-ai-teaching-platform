# W5b Device API/mTLS 契约证据

> 工作包：W5b 冻结 Provision 与 Device API
>
> 执行日期：2026-08-14
>
> 执行人：OpenAI Codex
>
> 最终责任人：高端阳
>
> 范围：Stage 1A、Simulator-only、合成数据、非生产

## 结论

W5b 的 OpenAPI 3.1 Device API v1 与身份策略已由可执行测试冻结。契约覆盖 Simulator Provision、一次性 Binding、CSR 轮换、证书状态/吊销判定、服务端时间及受限传输 URL 形状。

传输 URL 与所有 Content、Diagnostics、Firmware/OTA、student audio Purpose 在 Stage 1A 均明确返回 `403 capability_not_enabled`。不存在 Web Cookie/Bearer Token 与设备 mTLS 的凭据复用。

## TDD 证据

| 阶段 | Commit | 命令 | 结果 |
|---|---|---|---|
| RED：定义 OpenAPI、身份与负向矩阵 | `c20fbe7` | `pytest packages/protocol-schemas/tests/test_device_api_contract.py -q` | 7 failed, 1 passed；权威契约尚不存在 |
| GREEN：冻结 Device API v1 | `1a07c80` | 同上 | 8 passed |
| 合并协议回归 | `1a07c80` | `task test:protocol` | 18 passed |

## 已验证行为

| 类别 | 确定结果 |
|---|---|
| Trust Domain | Provisioning mTLS 与 Device mTLS 分离；Cookie、Bearer 与 Web Session 不可调用设备边界 |
| 身份来源 | 只信任已验证 X.509 SAN URI；客户端身份 Header 不作为授权事实 |
| 路径隔离 | 证书 Device ID、SAN URI 与路径 Device ID 不一致时拒绝 |
| 证书时间 | Not Before 未到或 Expiry 已到时拒绝 |
| 状态 | Revoked、Suspended 或未知状态 Fail Closed 并要求审计 |
| Binding | 300 秒、一次性、最多 5 次，并绑定 Serial/Organization/Site |
| Rotation | 要求当前证书、CSR SAN 相同、私钥留在设备、旧新证书最多重叠 300 秒 |
| 传输 | 契约形状预留但 Stage 1A 全部禁用 |

## 权威路径

- `packages/protocol-schemas/device-api/openapi.v1.json`
- `packages/protocol-schemas/device-api/identity-policy.v1.json`
- `packages/protocol-schemas/device-api/capability-catalog.v1.json`
- `packages/protocol-schemas/device-api/fixtures/auth/`
- `packages/protocol-schemas/tests/test_device_api_contract.py`

## 安全与范围说明

- Auth Fixture 是合成证书观察值，不包含私钥；W8 才会在运行时生成临时测试 CA/证书并执行真实 TLS 握手。
- 本工作包没有实现 Device API Handler、真实 CA、硬件私钥存储、对象上传下载、真实设备或生产 Trust Store。
- 本证据不是 G1/HIL、真实设备兼容、合规认证、生产授权或真实机构试点批准。

2026-08-14 的 Device ID 契约勘误由跨 MQTT/Device API 的同一回归测试覆盖：仅 PILOT-001 的六个 Device Code 合法。

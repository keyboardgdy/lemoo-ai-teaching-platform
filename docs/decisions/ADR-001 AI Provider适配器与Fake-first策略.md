# ADR-001：AI Provider Adapter 与 Fake-first 策略

**Date**: 2026-08-13

**Status**: proposed

**Deciders**: 高端阳（Product/Security/Privacy Owner，待批准）；OpenAI Codex（提案编制，非批准人）

**GitHub Work Item**: [#5](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5)

## Context

目标平台未来可能需要 ASR、语义匹配、提示/讲解、TTS、内容草稿和脱敏运维摘要，但当前没有真实用户/法域、Provider DPA/区域、音频设备事实、Eval 阈值或生产预算。直接选择 SDK 会让业务依赖供应商格式，并可能在未批准时发送未成年人数据。W1 明确 AI 不属于阶段 1A。

## Decision

采用内部版本化 Capability Port + Provider Adapter。阶段 1A 只提供确定性 Fake/Fixture；真实网络 Provider、凭据和数据发送入口默认不存在并 Fail Closed。具体 Provider、区域、模型、预算与生产 Eval 延后到 G2-AI，以新 ADR/本 ADR accepted revision 批准。

内部能力白名单仅允许：

- `asr.transcribe`
- `answer.semantic_match`
- `tutor.hint`
- `tutor.explain`
- `tutor.follow_up`
- `tts.synthesize`
- `author.question_draft`
- `ops.log_summary`

白名单定义目标产品边界，不表示当前启用。输出只允许类型化文本、音频引用或 `action_id`；AI 无任意工具、MQTT、设备命令、OTA、数据库、文件系统或网络访问。模型不能改变正确答案、评分规则、试卷或 TeachingSession 状态。

## Data and execution boundary

```text
Feature Gate (disabled by default)
-> Processing Authority + tenant/session checks
-> approved capability + schema + budget
-> field allowlist / PII + Secret scan
-> regional Provider Adapter or deterministic Fake
-> output schema / content safety / confidence
-> Action Allowlist (data only)
-> deterministic Orchestrator / human review
-> bounded metadata audit + fallback
```

- 原始学生音频默认不持久化；当前也不采集或发送。
- Provider 请求使用假名 Request/Run ID，不含真实学生身份、设备 Secret 或完整诊断包。
- Provider Adapter 不得绕过 Orchestrator；业务层不得直接导入 Provider SDK。
- 超时、限流、拒绝、成本上限或校验失败进入预置文本/本地能力/纯离线 Fallback。
- 每次调用记录 Provider/区域/模型/Prompt/参数版本、延迟、成本、安全与 Fallback，不默认记录全文。

## Provider approval checklist

真实 Provider 启用前必须同时批准：服务实体与区域、模型/版本固定策略、DPA、角色、子处理者、跨区域机制、输入/输出/滥用监测保留、是否用于训练、删除/权利协作、加密与访问、安全事件通知、内容安全、未成年人条款、可用性/限流、预算/配额、数据退出/迁移、Eval 集与阈值。

## Alternatives Considered

### Alternative 1: 现在直接绑定单一云 Provider SDK

- **Pros**：早期集成快，能力丰富。
- **Cons**：供应商格式侵入业务；区域、保留和模型漂移未决定；可能误发数据。
- **Why not**：与 D-009/D-010、阶段 1A 禁用边界和 Schema-first 冲突。

### Alternative 2: 现在自建全部 ASR/LLM/TTS

- **Pros**：数据面和版本控制潜力更强。
- **Cons**：模型、算力、安全、许可、运维和质量事实均缺失，成本不可证。
- **Why not**：在没有用例/Eval/容量事实前不可逆且过度设计。

### Alternative 3: 业务代码直接调用多个 Provider

- **Pros**：团队可按功能自由选择。
- **Cons**：审计、数据边界、Fallback、成本和安全策略分散，难以统一阻断。
- **Why not**：破坏 Port/Adapter、最小数据和单一策略执行点。

### Alternative 4: 永久不使用 AI

- **Pros**：消除 Provider 和生成风险。
- **Cons**：无法验证已批准的未来 AI 产品假设。
- **Why not**：可以作为长期 Go/No-Go 结果，但当前证据不足以永久取消目标能力。

## Consequences

### Positive

- 阶段 1A 无 Provider 凭据、网络费用或个人数据外发路径。
- 契约、Eval、故障和隐私检查可用 Fake 确定性准备。
- 后续 Provider 可替换，业务状态与评分规则保持供应商无关。

### Negative

- 不能用 Fake 证明真实模型质量、时延、适龄性、区域或成本。
- Adapter 和统一 Schema 增加初始设计与契约测试工作。
- 流式 ASR/TTS 的能力差异可能需要受控扩展，而非完全同构。

### Risks

- **抽象泄漏**：用 capability-specific contract 和 conformance suite 控制。
- **模型漂移**：固定模型/Prompt 版本与 Eval 门禁；未知版本拒绝或重审。
- **误启用**：配置、启动测试和网络出口共同 Fail Closed。
- **Prompt Injection/越权动作**：无工具权限、类型校验、Action Allowlist、设备互锁。
- **隐私/跨区域**：Processing Authority、DPA、区域和字段扫描未通过则不调用。

## Approval boundary

批准本 ADR 只接受 Adapter + Fake-first 的准备策略，不批准任何真实 Provider、模型、区域、预算、个人数据处理、AI 评分或生产 AI 能力。

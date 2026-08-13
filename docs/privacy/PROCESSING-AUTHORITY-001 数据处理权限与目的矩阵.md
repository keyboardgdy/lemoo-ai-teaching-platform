# PROCESSING-AUTHORITY-001：数据处理权限与目的矩阵

> 版本：0.1.0
>
> 状态：Proposed — Awaiting Security/Privacy Owner Approval
>
> 日期：2026 年 8 月 13 日
>
> 安全/隐私 Owner：高端阳（待批准）
>
> GitHub Work Item：[#5](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5)
>
> 适用性输入：[PRIVACY-APPLICABILITY-001](PRIVACY-APPLICABILITY-001%20隐私与AI法规适用性.md)

“处理权限”指用途、角色和授权证据完整后，系统才允许某类数据流；不是单纯 RBAC。当前只有合成数据流具备内部工程授权，所有真实个人数据流的法律/合同处理依据均为 `UNSET_BLOCKED`。

## 一、角色模型

| Scenario | 可能角色 | 当前状态 | 启用前证据 |
|---|---|---|---|
| 机构决定教学目的，平台按指示处理 | 机构 Controller/个人信息处理者；平台 Processor/受托人 | Unconfirmed | 合同/DPA、指令、职责、删除/事件协作 |
| 平台独立决定账号、安全、计费或产品改进目的 | 平台可能独立 Controller/个人信息处理者 | Unconfirmed | 逐目的依据、告知、必要性、权利和保留 |
| 双方共同决定目的与手段 | 可能共同控制 | Unconfirmed | 透明分工、权利入口和责任安排 |
| Provider 处理 ASR/LLM/TTS 输入 | Provider 可能处理者、子处理者或独立角色 | Not selected | Provider 条款、DPA、训练/保留、区域和子处理者 |

不得使用一份笼统 DPA 覆盖平台自己决定的所有目的；每个目的单独判定。

## 二、处理目的登记

| Purpose ID | 目的与数据 | 数据主体/来源 | 接收方 | 处理依据/授权状态 | 保留与删除 | Owner | 当前动作 |
|---|---|---|---|---|---|---|---|
| PUR-001 | 合成租户、Actor、场地与设备 Fixture | 无自然人；代码生成 | 本地/临时 CI | W1 内部工程授权；非个人数据 | DP-001；Reset/环境销毁 | 技术/QA | Allowed Stage 1A |
| PUR-002 | 合成遥测、事件、Shadow、命令与审计 | 模拟设备 | 本地依赖/CI 报告 | W1 内部工程授权；非个人数据 | DP-002/003；TTL/分区/Reset | 技术/QA | Allowed Stage 1A |
| PUR-003 | 真实机构成员账号与权限 | 教师/运维/机构 | 平台、身份服务待定 | `UNSET_BLOCKED`；需合同角色、依据与告知 | `UNSET`；账户/备份/审计删除规则 | 产品/隐私 | No collection |
| PUR-004 | 真实设备标识、位置、归属和运维记录 | 机构/设备/运维 | 平台、支持人员 | `UNSET_BLOCKED`；设备事实不等于个人数据豁免 | `UNSET`；设备转移/删除/审计例外 | 设备/隐私 | No collection |
| PUR-005 | 绑定学生身份、班级或学号 | 学生/机构 | 教师/平台 | `UNSET_BLOCKED`；优先匿名/共享模式 | `UNSET`；主体删除与历史解关联 | 产品/隐私 | Disabled |
| PUR-006 | 答题、提示、学习结果和分析 | 学生/教学会话 | 教师；去标识后教研 | `UNSET_BLOCKED`；不得默认依赖机构授权 | `UNSET`；明细与聚合分别删除 | 教学/隐私 | Disabled |
| PUR-007 | 原始语音/环境音频 | 学生/教室麦克风 | Interaction/ASR Provider | `UNSET_BLOCKED`；默认不持久化/不持续采集 | DP-004；内存有界后丢弃；异常样本另批 | AI/隐私 | Disabled |
| PUR-008 | 转写、语义匹配和 TTS 文本 | 学生/内容/AI | Orchestrator/Provider | `UNSET_BLOCKED`；需最小字段和 Provider 批准 | `UNSET`；按 Turn/Session/AI Run 级联 | AI/隐私 | Disabled |
| PUR-009 | AI Prompt、输入输出、模型参数、安全/成本结果 | 教学/教研/运维 | 内部 Eval；Provider 待定 | 合成 Eval 可内部授权；真实数据 `UNSET_BLOCKED` | DP-005；全文与元数据分离 | AI/产品 | Fake synthetic only |
| PUR-010 | 题目、图片、音频、解析与 AI 草稿 | 作者/供应方/教研 | 内容审核/目标机构 | 权利与合同记录未建立；`UNSET_BLOCKED` | 权利到期/撤回联动；不可变审计保留 | 内容 Owner | Draft tooling only |
| PUR-011 | 诊断包、日志、网络和设备环境信息 | 运维/设备/可能旁观者 | 授权支持人员 | `UNSET_BLOCKED`；字段/时间窗/必要性逐次批准 | 最多 7 天仅是设计上限，未批准不采集 | 安全/设备 | Disabled |
| PUR-012 | 安全、访问和高风险操作审计 | 用户/设备/服务账号 | 安全/审计有权人 | 真实环境依据和通知 `UNSET_BLOCKED` | 环境/法域批准期限；删除有审计例外 | 安全/隐私 | Synthetic only |
| PUR-013 | 支持、事件通报和数据主体请求记录 | 请求人/机构 | 隐私、安全、法务 | `UNSET_BLOCKED`；需要身份核验和案件依据 | 案件关闭后期限待法务决定 | 隐私/法务 | Process design only |

## 三、Provider 数据流最小化

```text
Untrusted input
-> purpose + Feature Gate
-> tenant/session/age/authority checks
-> field allowlist + pseudonymous request id
-> secret/PII/content-rights scanner
-> regional approved Provider Adapter
-> bounded request (time/size/token/budget)
-> schema + safety + action validation
-> deterministic orchestrator / human review
-> separately retained AI Run metadata
```

永不发送：设备证书/私钥、Session Cookie、Wi-Fi/网络密码、真实学生直接标识、完整诊断包、任意数据库记录、未获权利内容、OTA/Content 签名材料。Provider 不得获得 MQTT、数据库、对象存储或任意网络工具。

## 四、机构/监护人授权要求

- 先确认机构是否有权代表数据主体决定该用途；学校合同不能自动覆盖家庭场景或所有 AI 用途。
- 需要同意时，告知必须按法域说明目的、字段、接收方、保留、跨区域、撤回和不利影响。
- 需要监护人同意时，记录监护关系/验证方式、Policy 版本、时间、范围和撤回；不得收集超出验证所需的数据。
- 拒绝或撤回不能破坏非 AI 基础教学；进入预置/离线 Fallback。
- 新目的、Provider、模型区域或保留延长需要重新评估，不能沿用旧同意。

## 五、数据主体请求流程

`受理 → 身份/授权核验 → 定位全部事实/备份/Provider → 冲突和法定例外评估 → 导出/更正/删除/限制 → Provider/子处理者传递 → 验证 → 通知 → 审计`。

请求系统必须区分学生、监护人、机构代理和账号持有人；不能向请求者泄漏其他学生或机构数据。目标响应期限在法域确认前为 `UNSET`，因此真实数据处理继续阻塞。

## 六、事件与通报

发现疑似个人数据或 Secret 泄漏时：停止相关流量和 Provider 调用、保全最小证据、吊销凭据、确定数据/主体/法域/接收方、通知 Security/Privacy Owner 和有权法务，再按确认的法定/合同期限通报。当前不得预填统一“72 小时”等结论冒充所有法域要求。

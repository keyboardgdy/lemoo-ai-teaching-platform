# DATA-POLICY-001：数据分类、保留与删除政策

> 版本：0.1.0
>
> 状态：Proposed — Awaiting Security/Privacy Owner Approval
>
> 日期：2026 年 8 月 13 日
>
> 安全/隐私 Owner：高端阳（待批准）
>
> GitHub Work Item：[#5](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5)

本政策为 W4 工程基线。只有阶段 1A 合成数据期限可执行；真实个人数据、生产日志、诊断、教学和 AI 的期限必须在适用法域、角色和处理依据确定后批准，不能直接采用 03 的初始设计值。

## 一、数据等级

| Class | 定义 | 示例 | 默认控制 |
|---|---|---|---|
| D0 Public | 明确批准公开 | 开源文档、公开 Schema | 完整性、许可证、发布审核 |
| D1 Internal Synthetic | 纯合成、不可映射自然人或真实机构 | ORG-SIM-A、模拟遥测 | 非生产隔离、TTL、禁止对外冒充 |
| D2 Confidential Operational | 可关联账号、设备、机构或安全运营 | 用户 ID、设备归属、IP、审计 | 加密、最小权限、机构隔离、脱敏 |
| D3 Sensitive/Child | 儿童、语音、转写、学习记录、生物/位置或高影响画像 | 原始音频、学生回答、学习分析 | 默认不采集；单独评估、强授权、最短保留 |
| D4 Secret/Signing | 可认证、解密、签名或提升权限 | 私钥、Token、密码、签名 Share | 不进业务库/日志；专用 Secret/KMS/HSM 域 |

去标识数据仍按原等级管理，直至有书面重识别风险评估证明其不再能合理关联个人。聚合数据必须定义最小群组、稀疏单元抑制和重算/删除策略。

## 二、阶段 1A 可执行保留计划

| Policy ID | 合成数据 | Class | 最长期限/触发 | 删除方式 | Owner |
|---|---|---|---|---|---|
| DP-001 | 合成租户、Actor、场地、Registry | D1 | 临时环境生命周期；共享开发环境 30 天无活动 | 可重复 Reset；删除 DB/S3/缓存引用 | 技术/QA |
| DP-002 | 合成遥测、事件、Shadow、命令 | D1 | 原始 30 天；无需建立长期聚合 | Drop 分区/记录并清理对象与缓存 | 技术/QA |
| DP-003 | 合成审计与测试证据 | D1 | 测试环境 90 天；Git 中已批准去敏证据按项目历史 | 环境 TTL；Git 证据用更正/撤回提交 | QA/安全 |
| DP-004 | Simulator 音频 Fixture | D1 | 默认不生成；若协议测试必须使用人工合成音频，Job 结束即删，最长 24 小时 | 临时目录删除 + Artifact 排除检查 | AI/QA |
| DP-005 | Fake AI Input/Output/Eval | D1 | 合成全文 30 天；必要的去敏失败报告 90 天 | Run ID 级联；缓存/对象同步清理 | AI/QA |
| DP-006 | CI Log/Artifact | D1 | GitHub 配置上限 30 天；失败证据按需去敏入库 | CI 生命周期；入库前 Secret/路径扫描 | 技术/安全 |
| DP-007 | 临时测试证书/Token | D4 test-only | 单次运行；最长 24 小时 | 吊销/删除，随后清理临时目录 | 设备/安全 |

期限是上限，不是最低保留承诺；测试结束且无证据需求时应立即删除。

## 三、未来数据默认策略

| 数据 | 默认 | 生产期限状态 | 启用条件 |
|---|---|---|---|
| 真实学生/教师/机构身份 | 不采集 | `UNSET_BLOCKED` | 法域、角色、依据、告知/授权、权利流程批准 |
| 原始学生/教室音频 | 不持久化、不持续采集 | `ZERO_PERSISTENCE_DEFAULT` | 特定诊断样本须单独目的、同意、时间窗与删除批准 |
| 转写与自由文本回答 | 不采集 | `UNSET_BLOCKED` | 教学目的、可见角色、Provider、保留和删除批准 |
| 教学会话/答题明细 | 不采集 | `UNSET_BLOCKED` | 身份模式与 G2-Teaching 通过 |
| 去标识学习聚合 | 不生成 | `UNSET_BLOCKED` | 聚合/重识别阈值、用途和历史删除策略批准 |
| AI Input/Output 全文 | 不发送/不保存 | `UNSET_BLOCKED` | G2-AI、Provider DPA/区域/训练/保留与 Eval 批准 |
| AI Run 技术元数据 | 仅 Fake 合成 | `UNSET_BLOCKED` | 字段白名单和法域期限批准 |
| 真实设备遥测/事件/命令 | 不采集 | `UNSET_BLOCKED` | G1/G2-Device、机构合同和数据分类批准 |
| 诊断包 | 功能关闭 | `UNSET_BLOCKED` | APR-006、字段/时间窗、脱敏和最长 7 天上限批准 |
| 生产审计/安全日志 | 无生产 | `UNSET_BLOCKED` | 环境、合同、监管和事件需求确定 |

## 四、删除语义

1. 每类数据必须有稳定 Subject/Tenant/Device/Run/Content Key，不能只靠全文搜索删除。
2. 删除覆盖 PostgreSQL、分区、S3 版本、缓存、搜索/分析副本、Provider、导出、诊断、备份恢复后的再删除。
3. 在线删除和备份到期分开记录；恢复旧备份后必须重放 Tombstone/Deletion Ledger。
4. 法定/争议保留必须限定数据、Reason、Owner、期限和访问范围，不能无限期冻结全部账户。
5. 不可变审计采用最小标识/假名、密钥销毁或解关联策略；不能悄悄删改审计事实。
6. 派生聚合能重识别或包含单一主体贡献时必须重算或删除。
7. 删除完成输出系统级证明和未完成清单，不把“API 返回 202”当作完成。

## 五、日志与可观测性字段规则

允许：随机内部 ID、合成组织/设备 ID、事件类型、策略/Schema 版本、延迟、大小、状态码、错误分类、Request/Trace ID。

禁止：密码、Token、Cookie、Binding Code、私钥、完整证书、Wi-Fi 信息、原始音频、学生姓名/学号/联系方式、完整回答/转写、未脱敏 Prompt、完整诊断包、签名材料。IP/User-Agent 在真实环境是否允许及保留多久须单独决定。

## 六、导出、备份和非生产复制

- 禁止把生产数据复制到开发/测试；测试使用合成 Fixture。
- 导出必须是登记用途、最小字段、加密、短期链接、单次授权和到期删除。
- 备份加密密钥与数据库凭据分离；Restore Drill 复核 RLS、Tombstone 和到期任务。
- Provider 缓存/日志/滥用监测副本必须纳入删除承诺与验证，不能只删平台数据库。

## 七、变更规则

任何新数据字段必须先登记 Class、Purpose ID、Owner、来源、接收方、保留、删除、日志/AI 许可与适用性。缺任一项时 Schema/实现评审失败。延长期限、改变用途或新增 Provider/区域按新处理活动重新批准。

# CONTENT-GOVERNANCE-001：内容权利、审核、发布与撤回治理

> 版本：0.1.0
>
> 状态：Proposed — Awaiting Security/Privacy Owner Approval
>
> 日期：2026 年 8 月 13 日
>
> 内容最终 Owner：高端阳（阶段 1A 临时；待批准）
>
> 执行编制：OpenAI Codex（非批准人）
>
> GitHub Work Item：[#5](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5)

本文定义未来题目、解析、图片、音频、互动脚本和 AI 草稿的治理门槛。阶段 1A 不实现内容 CRUD、导入、签名或发布；所有相关入口继续 `disabled/not_started`。

## 一、强制原则

1. 无权利记录、无人工审核、无适用区域或已到期/撤回的内容不得发布。
2. AI 生成内容只能进入 `ai_draft`，不得自动成为 Published Version。
3. 已发布版本不可原地修改；修订生成新版本并保留来源/审核/发布链。
4. 内容签名与 OTA 签名使用不同信任域、Key、角色和审计。
5. 教学内容不能包含真实学生数据、运维 Secret 或从诊断日志复制的个人信息。
6. 发布前检查目标 Device Capability；不兼容不得通过“尽量运行”降级。
7. 下架阻止新使用；撤回还必须覆盖缓存、已下发包和后续会话引用。

## 二、Content Rights Record

每个可发布 Asset/Version 必须有机器可验证记录：

| Field | 含义 | 规则 |
|---|---|---|
| `rights_record_id` | 稳定权利记录 ID | 不复用 |
| `content_version_id` / `asset_digest` | 不可变内容/资源 | Hash 必须与审核对象一致 |
| `source_type` | original/licensed/open/imported/ai_generated | 不能用 `unknown` 发布 |
| `source_reference` | 合同、URL、作者声明或导入批次 | 不得写入敏感合同正文 |
| `rightsholder` | 作者/供应方/机构 | 必须可追溯 |
| `license_type` / `license_version` | 许可及版本 | 自定义许可需法务记录 |
| `permissions` | 复制、改编、分发、语音合成、AI 使用等 | 白名单；未列出的权利视为没有 |
| `territories` / `audience` | 适用区域和人群 | 与目标机构/年龄匹配 |
| `effective_at` / `expires_at` | 生效/到期 | 到期自动阻止新发布 |
| `attribution` | 署名要求 | 构建时可验证 |
| `ai_disclosure` | AI 参与类型、模型/Prompt 引用 | AI 草稿必须填写 |
| `reviewer_ids` / `reviewed_at` | 权利、教学、安全人工审核 | 必须是不同于提交人的有权自然人 |
| `withdrawal_status` | active/suspended/withdrawn/expired | 非 active 不能发布 |

合同、授权书等原始敏感附件放在经批准的受限存储中；公开仓库仅保存非敏感引用与摘要。

## 三、状态机与职责

```text
draft / ai_draft
-> rights_pending
-> rights_verified
-> pedagogical_review
-> safety_review
-> approved
-> packaged + signed
-> published
-> suspended -> reinstated | withdrawn
-> expired
```

| Role | 可执行 | 不可执行 |
|---|---|---|
| Author/Importer | 创建 Draft、修订、提交 | 批准自己的版本、发布 |
| AI Service | 生成 `ai_draft` 和出处/模型元数据 | 审核、批准、签名、发布 |
| Rights Reviewer | 核对来源、许可、区域、到期 | 修改教学内容、代替安全审核 |
| Pedagogy Reviewer | 准确性、适龄性、答案/解析 | 改写权利记录或签名 |
| Safety Reviewer | 有害内容、Prompt Injection、动作/隐私 | 单独完成全链 |
| Publisher | 对已批准 Digest 构建/发布 | 修改审核对象、使用未批准 Key |

阶段 1A 只有一名自然人 A，无法满足真实内容的独立审核，因此发布始终禁用。

## 四、导入与 AI 草稿

- 文件先进入隔离区，执行类型、扩展名、大小、恶意内容和公式/外链检查。
- 解析、校验、预览、人工确认分阶段；导入失败不产生 Published Version。
- 外部 URL、公式、图片、音频和附件均是不可信输入，不允许构建器任意网络访问。
- AI Prompt 输入只含获授权内容；输出记录模型/Prompt/参数、引用、生成标记和安全结果。
- AI 不得伪造来源、许可证或人工审核；来源不确定时状态保持 `rights_pending`。
- 客观题正确答案和评分规则必须由确定性校验与人工审核确认。

## 五、发布门禁

发布请求必须绑定 Content Version/Asset Digest、Rights Record、目标机构/设备能力、审核记录、构建器版本、Manifest Digest、签名角色和回退版本。以下任一情况 Fail Closed：

- Rights Record 缺失、许可不含目标用途/区域/人群、已到期或撤回。
- `ai_draft`、审核人等于提交人、审核对象 Digest 已变化。
- 含个人数据、Secret、未批准外链/脚本/动作或不适龄内容。
- 目标 Capability 不满足、资源缺失、Hash/签名错误、空间/原子切换能力未知。
- Content signing Key 与 OTA/普通服务域重叠。

## 六、下架与已下发撤回

1. Intake 记录举报/权利通知、内容版本、区域、严重度和证据。
2. `suspended` 立即阻止新发布、新下载和新会话选择，不删除证据。
3. 定位全部 Paper/Script/Package/Device Cache 引用和当前教学会话。
4. 安全风险可立即停止；普通权利争议按批准策略处理进行中的会话。
5. 构建撤回/替代清单；设备在线时获取并验证，离线设备保持阻塞标记。
6. 记录每台设备/机构结果、无法撤回项和人工升级；不能只更新云端状态。
7. 结论为 reinstated、replaced、withdrawn 或 expired；修订发布新版本。

## 七、证据与验证

后续 G2-Content 必须提供：完整/缺失/过期/区域不符 Rights Fixture，AI Draft 禁止发布，审核人冲突，Digest 替换，恶意导入，签名篡改，Capability 不兼容，离线撤回和已缓存内容验证。Simulator 只能证明云端流程；真实安装、原子激活和撤回需要 G1/HIL。

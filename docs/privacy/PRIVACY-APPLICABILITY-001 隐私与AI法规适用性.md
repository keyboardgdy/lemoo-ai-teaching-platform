# PRIVACY-APPLICABILITY-001：隐私、未成年人和 AI 法规适用性

> 版本：1.0.0
>
> 状态：Approved — Stage 1A Engineering Boundary
>
> 日期：2026 年 8 月 13 日
>
> 安全/隐私 Owner：高端阳（2026 年 8 月 13 日批准）
>
> 批准记录：https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5#issuecomment-5278502909
>
> 执行编制：OpenAI Codex（工程分析，不构成法律意见）
>
> GitHub Work Item：[#5](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5)

本文只建立适用性问题、触发器和证据清单。项目尚未确定运营实体、部署/服务法域、真实机构、数据主体位置、年龄范围、控制者/处理者关系或 Provider 区域，因此不能得出“合规”结论，不能授权处理真实个人数据或面向公众提供 AI 服务。

## 一、当前事实与默认判定

| Fact ID | 问题 | 当前事实 | 安全默认 |
|---|---|---|---|
| JUR-001 | 运营/签约实体注册地 | Unknown | 阻塞生产与合同 |
| JUR-002 | 服务器、备份、日志和 Provider 区域 | Unknown；阶段 1A 仅本地/临时 CI | 阻塞真实数据 |
| JUR-003 | 目标机构和数据主体所在地 | 无真实机构；Unknown | 不选择或联系真实主体 |
| JUR-004 | 学生年龄、是否不满 14/13/16 岁 | Unknown | 按可能涉及儿童的最高保护设计，不采集 |
| JUR-005 | 平台与机构的控制者/处理者角色 | Unknown | 不签署/宣称角色，不处理真实数据 |
| JUR-006 | 机构/监护人授权和告知渠道 | 不存在 | 教学/AI/个人数据保持禁用 |
| JUR-007 | 是否向公众提供生成式 AI | 否；AI 当前禁用 | Fake-only，不调用真实 Provider |
| JUR-008 | 是否用 AI 决定入学、分班、学习评价或考试行为 | 否；明确非目标 | 模型不得决定成绩/资格/会话状态 |

当前阶段 1A 的合成标识不应对应或可映射到自然人。若 Fixture、日志或录屏意外包含真实标识，应立即停止处理并按事件流程处置，不能因“测试环境”降低标准。

## 二、官方参考与条件触发

以下是 2026-08-13 的工程适用性快照；应由有权法务按真实事实复核最新文本、实施规则和地方要求。

| Regime ID | 官方来源 | 条件触发问题 | 工程上必须准备 | 当前判定 |
|---|---|---|---|---|
| REG-CN-PIPL | [《个人信息保护法》](https://www.npc.gov.cn/npc/c2/c30834/202108/t20210820_313088.html) | 是否在中国境内处理个人信息，或存在该法规定的域外触发；是否处理敏感/不满 14 周岁信息、自动化决策或跨境 | 处理依据、单独同意/监护人同意适用性、专门规则、影响评估、委托/跨境机制、权利响应 | Applicability unknown；真实数据 blocked |
| REG-CN-CHILD | [《儿童个人信息网络保护规定》](https://www.cac.gov.cn/2019-08/23/c_1124913903.htm) | 是否在中国境内通过网络处理不满 14 周岁儿童个人信息 | 专门保护规则、监护人同意路径、最小必要、专人/权限、事件处置 | Applicability unknown；儿童数据 blocked |
| REG-CN-MINOR | [《未成年人网络保护条例》](https://www.moe.gov.cn/jyb_xxgk/moe_1777/moe_1778/202310/t20231025_1087333.html) | 是否向中国境内未成年人提供网络产品/服务或处理其信息 | 最有利于未成年人、内容/沉迷/隐私保护、投诉举报、供应链职责 | Applicability unknown；真实服务 blocked |
| REG-CN-GENAI | [《生成式人工智能服务管理暂行办法》](https://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm) | 是否向中国境内公众提供生成内容服务；内部研发/教育应用是否落入例外或其他规则 | 适用人群/用途、个人信息与输入记录保护、内容安全、投诉、标识/备案评估适用性 | 当前不向公众提供；Provider disabled |
| REG-EU-GDPR | [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679) | 是否处理欧盟数据主体数据或存在域外适用；儿童同意、敏感数据、画像/自动决策、跨境是否触发 | 角色/依据、透明度、儿童同意年龄国别确认、DPIA、权利、处理者合同、传输机制 | Applicability unknown；EU personal data blocked |
| REG-EU-AIA | [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) | 是否在欧盟投放/部署 AI；是否用于教育准入、分配、学习结果评价、教育水平或考试监控 | 用途分类记录；若高风险则质量/风险/数据/日志/人类监督/注册等适用要求；即使非高风险仍需透明与安全评估 | No EU use facts；AI disabled |
| REG-US-COPPA | [FTC COPPA Rule 与 2025 修订](https://www.ftc.gov/legal-library/browse/federal-register-notices/16-cfr-part-312-coppa-final-rule-amendments) | 是否为面向美国 13 岁以下儿童的商业在线服务，或实际知情收集其个人信息 | 隐私通知、可验证家长同意、最小化、访问/删除、安全、保留和第三方披露控制 | Applicability unknown；US child data blocked |

不得把“学校/机构签约”自动等同监护人授权，也不得把匿名 Participant ID 自动等同匿名数据；只要仍可合理关联或重识别自然人，就按个人数据处理。

## 三、适用性决策流程

```text
真实部署/试点请求
-> 确认运营与签约实体
-> 确认机构、用户、年龄与数据主体所在地
-> 绘制数据存储/备份/Provider/支持访问区域
-> 确认产品用途（教学辅助、评分、准入、监控、诊断）
-> 确认控制者/处理者/共同控制者和子处理者
-> 法务形成逐法域适用性与处理依据
-> 完成必要 DPIA/PIPIA、合同、告知/同意与权利流程
-> Security/Privacy Owner + 法务批准
-> 才能为明确数据类型启用独立 Feature Gate
```

任一步为 Unknown 时，默认结果是 `NO_COLLECTION / NO_PROVIDER_TRANSFER / NO_PRODUCTION`。

## 四、必须完成的影响评估触发器

| Trigger ID | 变化 | 所需评估 |
|---|---|---|
| PIA-001 | 首次处理任何真实学生、教师、机构联系人或设备归属数据 | Privacy Applicability + Processing Authority + 数据流评审 |
| PIA-002 | 处理儿童/未成年人信息、语音、转写、学习记录或画像 | 专门未成年人规则 + DPIA/PIPIA/当地等价评估 |
| PIA-003 | 引入 AI Provider、子处理者或新的数据区域 | Provider 尽调、DPA、传输机制、保留/训练政策和删除验证 |
| PIA-004 | 用 AI 评价学习结果、推荐教育水平、准入/分班或考试监控 | AI 用途分类、人类监督、偏差/申诉和高风险适用评估 |
| PIA-005 | 远程诊断、摄像头/麦克风、批量导出或跨机构支持 | 必要性/比例性、字段/时间窗、告知、审批和审计评估 |
| PIA-006 | 改变目的、保留期、接收方、身份模式或去标识方法 | 兼容性、重识别、再次告知/同意与历史数据处置评估 |

## 五、法务/Owner 决策所需事实包

- 运营、签约、托管、支持和 Provider 实体及地址。
- 机构类型、公私立属性、学生年龄与国家/地区。
- 数据字典、目的、必要性、来源、接收方、保留/删除、备份和日志路径。
- 机构协议、DPA、子处理者清单、跨境/跨区域机制。
- 监护人/机构告知、同意、撤回、权利请求和投诉流程。
- AI intended purpose、模型/Prompt、评分影响、自动化程度、人类复核和申诉。
- 安全控制、事件响应、恢复、删除验证和独立测试证据。

W4 批准不能替代上述事实包或专业法律复核。

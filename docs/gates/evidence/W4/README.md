# W4 安全、隐私、内容与 AI 工程边界批准证据

> 工作包：W4 冻结安全、隐私与 AI 边界
>
> 状态：`approved`
>
> 执行日期：2026-08-13
>
> 执行编制：OpenAI Codex（非批准人）
>
> 安全/隐私 Owner：高端阳（2026-08-13 批准）
>
> GitHub Issue：[#5](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5)
>
> 批准记录：[#5 approval](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5#issuecomment-5278502909)
>
> 批准内容提交：`b3723fb9b4c573cd3b5d2579805c82c766402ddb`
>
> 机器可验证基线：[baseline.yaml](baseline.yaml)

## 批准产物

- [THREAT-MODEL-001](../../../security/THREAT-MODEL-001%20平台威胁模型.md)
- [PRIVACY-APPLICABILITY-001](../../../privacy/PRIVACY-APPLICABILITY-001%20隐私与AI法规适用性.md)
- [PROCESSING-AUTHORITY-001](../../../privacy/PROCESSING-AUTHORITY-001%20数据处理权限与目的矩阵.md)
- [DATA-POLICY-001](../../../privacy/DATA-POLICY-001%20数据分类保留与删除政策.md)
- [CONTENT-GOVERNANCE-001](../../../content/CONTENT-GOVERNANCE-001%20内容权利审核与撤回.md)
- [ADR-001](../../../decisions/ADR-001%20AI%20Provider适配器与Fake-first策略.md)
- [APPROVAL-MATRIX-001](../../../security/APPROVAL-MATRIX-001%20高风险操作审批矩阵.md)
- [SECRET-INVENTORY-001](../../../security/SECRET-INVENTORY-001%20Secret与密钥清单.md)

## 当前批准判定

- 已识别 26 个 Web/Device/Data/AI/Content/OTA/Supply-chain 威胁与 12 条安全不变量。
- 适用法域、运营/签约实体、数据主体和控制者/处理者角色仍未知；真实个人数据继续 `UNSET_BLOCKED`。
- 阶段 1A 只允许合成数据目的；每个目的都有 Owner、保留和删除路径。
- AI 采用 Provider Adapter + deterministic Fake；真实 Provider、Credential、网络调用和个人数据外发均不可达。
- 原始学生音频默认不持久化；当前不采集、不发送。
- 14 类 R2/R3 动作按重新认证、Reason、双人审批和审计控制；没有第二名自然人时保持禁用。
- Content/OTA 签名域完全分离；普通服务、开发机和 CI 不持有 OTA Root/发布私钥。
- G1-Device 保持 `blocked_no_physical_device`；W4 不产生或替代任何实机/HIL 证据。
- Content、Teaching、AI、Diagnostic、Bulk Command、OTA、真实设备/机构/数据和生产不因 W4 获批而启用。

## 需求与决策追踪

| W4 产物 | 主要输入 | 后续证据/Gate |
|---|---|---|
| Threat Model | PRD-GOV-001、PRD-GOV-002、PRD-GOV-003、PRD-DEV-001、PRD-OPS-002、PRD-OPS-004、PRD-AI-003、PRD-OTA-002、PRD-OTA-005 | W5/W6/W7b/W8；G1/G2/HIL |
| Privacy Applicability | D-008/D-009/D-012；PRD-TCH-001/005、PRD-AI-005 | 法务/隐私复核；任何真实数据前 |
| Processing Authority | D-008～010；PRD-TCH-001、PRD-TCH-004、PRD-TCH-005、PRD-AI-001、PRD-AI-002、PRD-AI-003、PRD-AI-004、PRD-AI-005 | W6a/W5f；G2-Teaching/G2-AI |
| Data Policy | D-009/D-014；PRD-OPS-004、PRD-TCH-005、PRD-AI-005 | W6a/W7c/Privacy test |
| Content Governance | D-011/D-013；PRD-CNT-002、PRD-CNT-003、PRD-CNT-005 | W5d；G1/G2-Content |
| AI Provider ADR | D-010；PRD-AI-001、PRD-AI-002、PRD-AI-003、PRD-AI-004、PRD-AI-005 | W5f；G1/G2-AI/Eval |
| Approval Matrix | PRD-GOV-003、PRD-OPS-002/004、PRD-CNT-003、PRD-AI-003、PRD-OTA-005 | W6b/W7b2；各能力 Gate |
| Secret Inventory | D-004/D-005/D-010/D-012；PRD-DEV-001、PRD-OTA-002/005 | W5/W7a/W7b3；G1/HIL |

## 官方适用性参考

- [中国《个人信息保护法》](https://www.npc.gov.cn/npc/c2/c30834/202108/t20210820_313088.html)
- [中国《儿童个人信息网络保护规定》](https://www.cac.gov.cn/2019-08/23/c_1124913903.htm)
- [中国《未成年人网络保护条例》](https://www.moe.gov.cn/jyb_xxgk/moe_1777/moe_1778/202310/t20231025_1087333.html)
- [中国《生成式人工智能服务管理暂行办法》](https://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm)
- [EU GDPR](https://eur-lex.europa.eu/eli/reg/2016/679)
- [EU AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)
- [US FTC COPPA Rule Amendments](https://www.ftc.gov/legal-library/browse/federal-register-notices/16-cfr-part-312-coppa-final-rule-amendments)

这些链接是工程问题识别依据，不构成法务批准或适用性结论。

## 可重复检查

```text
uv run --project apps/cloud python docs/gates/evidence/W4/verify_w4.py
task docs:check
```

## 批准基线验证

| 检查 | 2026-08-13 结果 |
|---|---|
| `verify_w4.py` | `PASS`；29/29，`APPROVAL=APPROVED`；八份产物摘要与批准内容提交已锁定 |
| `task docs:check` | `PASS`；50 个 Markdown 文档 |
| `task verify` | `PASS`；后端 7 项测试、95.71% 覆盖率，前端 1 项测试、100% 覆盖率，其余构建/类型/格式/Schema/Compose 检查通过 |
| `pre-commit run --all-files` | `PASS`；包含私钥、格式和基础文件检查 |
| Gitleaks | `PASS`；暂存 W4 约 70 KB 和完整 16 个提交均未发现泄漏 |
| Trivy clean-checkout equivalent | `PASS`；项目锁文件和版本控制配置无 High/Critical 发现 |
| [PR #6 首轮 Required Checks](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/actions/runs/31686134622) | `PASS`；governance、backend、frontend、compose、security 全绿 |
| [PR #6 批准更新 Required Checks](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/actions/runs/31687188881) | `PASS`；governance、backend、frontend、compose、security 全绿 |

## 完成情况

- [x] W4 自动一致性检查全绿
- [x] 全仓文档、格式、测试与 Secret 检查全绿
- [x] W4 PR Required Checks 全绿
- [x] 高端阳以安全/隐私 Owner 身份批准八份产物
- [x] 产物升级为 `1.0.0 Approved`（ADR-001 为 `accepted`），记录 Commit/Digest
- [x] 批准更新后的 PR Required Checks 全绿
- [ ] PR 合并并关闭 Issue #5

批准原文：

> 高端阳批准 THREAT-MODEL-001、PRIVACY-APPLICABILITY-001、PROCESSING-AUTHORITY-001、DATA-POLICY-001、CONTENT-GOVERNANCE-001、ADR-001、APPROVAL-MATRIX-001 和 SECRET-INVENTORY-001 组成 W4 安全/隐私工程基线；确认该批准不是法律意见、合规认证或生产授权，不批准处理真实个人数据，也不启用真实设备、机构、Provider、内容、教学、AI、诊断、批量命令或 OTA。

用户消息中的 `CONTENT- GOVERNANCE-001` 已按其明确批准语义规范化为正式文档 ID `CONTENT-GOVERNANCE-001`。本次批准只接受工程边界，不解决适用法域等未决事实，也不改变任何禁用能力状态。

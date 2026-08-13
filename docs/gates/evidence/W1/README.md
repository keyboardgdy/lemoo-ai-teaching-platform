# W1 已批准范围与验收证据

> 工作包：W1 批准 PILOT-001 模拟器 MVP 与验收矩阵
>
> 状态：`approved`
>
> 执行日期：2026-08-13
>
> 执行编制：OpenAI Codex
>
> Product Owner / QA Owner：高端阳
>
> GitHub Issue：[#3](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/3)
>
> 批准记录：[高端阳 Product/QA Approval](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/3#issuecomment-5278164835)
>
> 机器可读基线：[baseline.yaml](baseline.yaml)

## 已批准产物

- [MVP-001](../../../product/MVP-001%20阶段1A模拟器MVP范围.md)
- [STORY-MAP-001](../../../product/STORY-MAP-001%20阶段1A用户故事地图.md)
- [ACCEPTANCE-001](../../../product/ACCEPTANCE-001%20阶段1A验收矩阵.md)
- [DEMO-001](../../../product/DEMO-001%20阶段1A合成数据演示脚本.md)
- [PILOT-001](../../../product/PILOT-001%20模拟器工程验证范围.md)

## 当前判定

- 已批准范围固定为 7 个 P0 Story、1 个 P1 Story、11 个 Out Story。
- P0 覆盖 GOV/DEV/OPS 12 项 Requirement。
- 7 个 P0 Story 均定义 Normal、Permission、Exception、Degraded，共 28 个场景。
- Demo 使用两个合成机构、六台模拟设备、一个虚拟组合和 16 个固定步骤。
- G1-Device 保持 `blocked_no_physical_device`；真实设备、真实机构、个人数据和生产继续阻塞。
- Content、Teaching、AI、Diagnostic、Bulk Command 和 OTA 保持 `disabled/not_started`。
- 产品价值假设和 PM-001～007 仍缺少客户证据；W1 只允许内部工程 Go。

## 可重复检查

```text
uv run --project apps/cloud python docs/gates/evidence/W1/verify_w1.py
task docs:check
```

W1 自动检查证明批准文档、公开批准记录、版本、Digest 和范围内部一致。高端阳的 Product/QA 批准以公开批准记录为准；该批准不构成任何实现、Simulator 或 HIL 证据。

## 本地批准基线验证

| 检查 | 2026-08-13 结果 |
|---|---|
| `verify_w1.py` | `PASS`；25/25，`APPROVAL=APPROVED` |
| `task docs:check` | `PASS`；39 个文档文件 |
| `task verify` | `PASS`；后端 7 项测试、95.71% 覆盖率，前端 1 项测试、100% 覆盖率，其余构建/类型/格式/Schema/Compose 检查通过 |
| `pre-commit run --all-files` | `PASS`；包含私钥检测、格式与基础文件检查 |
| Gitleaks | `PASS`；10 个提交未发现泄漏 |
| Trivy clean-checkout equivalent | `PASS`；排除未跟踪的本地 `.venv`/`node_modules` 后，项目锁文件和版本控制配置无 High/Critical 发现；最终判定以 PR Security Check 为准 |
| [PR #4 首轮 Required Checks](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/actions/runs/31682990854) | `PASS`；governance、backend、frontend、compose、security 全绿 |
| [PR #4 批准升级检查](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/actions/runs/31684384490) | `PASS`；批准文档、Digest 与证据提交后的五项 Required Checks 全绿 |

## 待完成

- [x] W1 自动检查全绿
- [x] 全仓文档、格式和 Secret 检查全绿
- [x] W1 PR Required Checks 全绿
- [x] 高端阳以 Product Owner 身份批准范围/优先级
- [x] 高端阳以 QA/验收 Owner 身份批准 28 场景、指标和 Demo Script
- [x] 四份 W1 产物升级为 `1.0.0 Approved`，PILOT-001 批准引用已记录
- [x] 基线 Commit、Artifact Digest 和公开批准记录已写入 `baseline.yaml`
- [x] 批准升级后的 PR Required Checks 全绿；PR #4 可合并

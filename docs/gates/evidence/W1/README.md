# W1 候选范围与验收证据

> 工作包：W1 批准 PILOT-001 模拟器 MVP 与验收矩阵
>
> 状态：`awaiting_owner_approval`
>
> 执行日期：2026-08-13
>
> 执行编制：OpenAI Codex
>
> Product Owner / QA Owner：高端阳
>
> GitHub Issue：[#3](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/3)

## 候选产物

- [MVP-001](../../../product/MVP-001%20阶段1A模拟器MVP范围.md)
- [STORY-MAP-001](../../../product/STORY-MAP-001%20阶段1A用户故事地图.md)
- [ACCEPTANCE-001](../../../product/ACCEPTANCE-001%20阶段1A验收矩阵.md)
- [DEMO-001](../../../product/DEMO-001%20阶段1A合成数据演示脚本.md)
- [PILOT-001](../../../product/PILOT-001%20模拟器工程验证范围.md)

## 当前判定

- 候选范围固定为 7 个 P0 Story、1 个 P1 Story、11 个 Out Story。
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

W1 自动检查只证明候选文档内部一致，不构成高端阳的产品/验收批准，也不构成任何实现、Gate、Simulator 或 HIL 证据。

## 本地候选验证

| 检查 | 2026-08-13 结果 |
|---|---|
| `verify_w1.py` | `PASS`；22/22，`APPROVAL=PENDING` |
| `task docs:check` | `PASS`；39 个文档文件 |
| `task verify` | `PASS`；后端 7 项测试、95.71% 覆盖率，前端 1 项测试、100% 覆盖率，其余构建/类型/格式/Schema/Compose 检查通过 |
| `pre-commit run --all-files` | `PASS`；包含私钥检测、格式与基础文件检查 |
| Gitleaks | `PASS`；10 个提交未发现泄漏 |
| Trivy clean-checkout equivalent | `PASS`；排除未跟踪的本地 `.venv`/`node_modules` 后，项目锁文件和版本控制配置无 High/Critical 发现；最终判定以 PR Security Check 为准 |
| [PR #4 首轮 Required Checks](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/actions/runs/31682990854) | `PASS`；governance、backend、frontend、compose、security 全绿 |

## 待完成

- [x] W1 自动检查全绿
- [x] 全仓文档、格式和 Secret 检查全绿
- [x] W1 PR Required Checks 全绿
- [ ] 高端阳以 Product Owner 身份批准范围/优先级
- [ ] 高端阳以 QA/验收 Owner 身份批准 28 场景、指标和 Demo Script
- [ ] 批准后将四份产物升级为 `1.0.0 Approved`，记录 Commit/Digest 并关闭 Issue #3

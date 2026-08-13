# Risk Register

> 状态：Active  
> 更新时间：2026 年 8 月 13 日  
> 最终责任人：高端阳  
> 维护执行：OpenAI Codex  
> 完整工程风险来源：[04 第十七章](../04%20开发前准备与启动门禁.md#十七风险登记)

本表登记阶段 1A 当前必须持续可见的风险。`Accepted` 只表示在明确范围内接受，不表示风险消失或可以扩展适用范围。

| Risk ID | 风险 | 概率 | 影响 | 缓解/门禁 | Owner | 状态 |
|---|---|---:|---:|---|---|---|
| RISK-001 | 高端阳一人承接五类 A，缺少职责独立性 | 高 | 高 | 仅限合成数据/非生产；Codex 提供可重复证据；真实数据、实机、生产前补独立复核 | 高端阳 | Accepted for Stage 1A |
| RISK-002 | 当前没有物理设备，无法证明硬件、私钥、弱网、命令和 OTA 事实 | 高 | 极高 | G1-Device=`blocked_no_physical_device`；Simulator/HIL 证据分离 | 高端阳 | Blocked outside Stage 1A |
| RISK-003 | Simulator 与未来真实设备行为漂移 | 中 | 高 | 固定 `device-v1`、确定性种子和同一 Conformance Suite；阶段 1B 必须 HIL | 高端阳 | Open |
| RISK-004 | 跨租户数据或设备控制泄露 | 中 | 极高 | ORG-SIM-A/B 负向套件；RLS、API、MQTT ACL、SSE、S3 全链路验证 | 高端阳 | Open / G2-Device blocker |
| RISK-005 | AI、内容、教学或 OTA 被工程骨架隐式启用 | 中 | 极高 | 默认 `disabled/not_started`；配置与启动测试 Fail Closed | 高端阳 | Open |
| RISK-006 | 招聘材料和未经验证假设被误当作客户事实 | 中 | 高 | JD 保持低权重；价值指标和真实试点决策保持 Open | 高端阳 | Controlled |
| RISK-007 | 需求范围扩大导致首个闭环延迟 | 高 | 高 | 阶段 1A 只允许 GOV/DEV/OPS P0；变更必须更新 PRD/RTM | 高端阳 | Open |
| RISK-008 | Secret、测试证书或生产权限误用 | 中 | 极高 | 只生成本地测试凭据；禁止生产 Key；Secret 扫描与环境隔离 | 高端阳 | Open / Gate 3-Sim blocker |
| RISK-009 | Windows 与 Linux/容器行为不一致 | 中 | 中 | 跨平台脚本、Linux CI、Windows Smoke；路径和换行检查 | 高端阳 | Open |
| RISK-010 | 尚无客户问题和价值指标基线 | 高 | 高 | 不阻塞内部阶段 1A；阻塞真实试点承诺和 Go/No-Go | 高端阳 | Deferred to real pilot preparation |

## 复核规则

- 每次 Gate Review 和任何范围扩展时复核。
- 极高影响风险如果没有可执行缓解或门禁，相关 Gate 必须失败。
- 状态、概率、影响或缓解变化时，同步对应 Decision、PRD/RTM 和测试证据。
- RISK-001 的接受记录只来自高端阳 2026-08-13 对阶段 1A 一人多角色风险的明确接受。

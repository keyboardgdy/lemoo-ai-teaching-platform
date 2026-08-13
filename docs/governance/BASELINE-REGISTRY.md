# 项目基线登记表

> 状态：Active  
> 生效日期：2026 年 8 月 13 日  
> 阶段 1A 临时项目责任人：高端阳  
> AI 执行代理：OpenAI Codex

> Gate 0 状态：[Passed 2026-08-13](../gates/gate-0.yaml)

本表明确 01～04、正式产品文档和治理文档的职责、状态、Owner 与变更方式，作为 Gate 0 的基线输入。

| 基线 | 职责 | 当前状态 | 最终责任人（A） | 执行人（R） | 变更规则 |
|---|---|---|---|---|---|
| [01 技术栈](../01%20fastapi-vue-modern-tech-stack.md) | 唯一语言、框架和基础设施选型 | Active implementation constraint | 高端阳 | OpenAI Codex | 技术替换必须 ADR；同步 01/02/04 与受影响契约 |
| [02 生产架构](../02%20fastapi-vue-modern-architecture.md) | 进程、模块、依赖、数据和部署边界 | Active architecture baseline | 高端阳 | OpenAI Codex | 跨边界变更必须 ADR、迁移/兼容方案和验证证据 |
| [03 产品与系统设计](../03%20ai-teaching-platform-design.md) | 产品与领域设计输入 | Active design input；从属于 PRD | 高端阳 | OpenAI Codex | 用户承诺以 PRD 变更为先，不得由 03 单独扩大范围 |
| [04 开发前准备与启动门禁](../04%20开发前准备与启动门禁.md) | 工作包、Gate、证据和启动条件 | Active mandatory gate baseline | 高端阳 | OpenAI Codex | 门禁弱化必须书面风险接受；不得通过实现绕过 |
| [PRD-001](../product/PRD-001%20教育机器人云平台.md) | 用户承诺、范围、规则和验收 | 1.0.0 Approved for Stage 1A | 高端阳 | OpenAI Codex | 按 PRD 变更协议升级版本并重审受影响范围 |
| [RTM-001](../product/RTM-001%20教育机器人云平台需求追踪矩阵.md) | 来源到证据的双向追踪 | 1.0.0 Approved for Stage 1A | 高端阳 | OpenAI Codex | 与 PRD/Story/Test/Evidence 同步变更；ID 不复用 |
| [PILOT-001](../product/PILOT-001%20模拟器工程验证范围.md) | 合成租户、虚拟组合和 Simulator 范围 | 1.0.0 Confirmed | 高端阳 | OpenAI Codex | 扩展到真实机构/设备必须新决策并通过 Real/HIL Gate |
| [OWNER-001](OWNER-001%20责任人与AI执行授权.md) | R/A、执行权限和不可代理边界 | 1.1.0 Stage 1A confirmed | 高端阳 | OpenAI Codex | 人员或授权范围变化时立即更新 |

## 变更优先级

1. 适用法律、合同和正式安全/隐私政策。
2. 已批准的 PRD、RTM 与产品 Decision。
3. 04 Gate 约束与已批准 ADR。
4. 03 产品设计输入。
5. 01 技术栈和 02 架构实现约束。

出现冲突时停止受影响实现，由高端阳决定产品范围，Codex 提交影响分析、候选方案和验证计划。任何变更都不得隐式启用真实数据、真实设备、AI、内容、教学或 OTA 能力。

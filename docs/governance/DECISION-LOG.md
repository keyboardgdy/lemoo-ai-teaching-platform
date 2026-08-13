# Decision Log

> 状态：Active  
> 更新时间：2026 年 8 月 13 日  
> 最终责任人：高端阳  
> 维护执行：OpenAI Codex  
> 产品决策正文：[PRD-001 第十四章](../product/PRD-001%20教育机器人云平台.md#十四open-questions-与阻塞决策)

本表集中追踪已确认和未关闭决策。推荐默认只用于 Fail Closed 或设计准备；到达“最晚决定时间”前没有高端阳或后续有权 Owner 的批准，不得把默认值升级为生产事实。

| Decision ID | 状态 | 当前决定/默认 | 最终责任人 | 最晚决定时间 | 当前影响 |
|---|---|---|---|---|---|
| D-002 | Confirmed | 使用 PILOT-001：两个合成租户、一个虚拟组合、六个模拟设备 | 高端阳 | 已确认 2026-08-13 | 阶段 1A |
| D-003 | Blocked | 真实设备 OS/Runtime 以 W3 实机事实为准 | 高端阳（临时设备 A） | 阶段 1B G1-Device 前 | 不阻塞阶段 1A |
| D-004 | Blocked | 每设备独立身份，禁止共享 Key；实现方式等待实机 | 高端阳（临时设备/安全 A） | 阶段 1B G1-Device 前 | 不阻塞阶段 1A |
| D-006 | Open | 云端冻结统一 `device-v1`；旧协议未来经 Adapter 转换 | 高端阳（临时技术/设备 A） | G2-Device 前 | 阻塞 G2-Device |
| D-007 | Open | 无事实前不承诺规模化数值 | 高端阳 | 容量预算前 | 阻塞规模/SLO 承诺 |
| D-008 | Deferred | 匿名/共享课堂优先，身份最小化 | 高端阳 | G2-Teaching 前 | 教学能力保持禁用 |
| D-009 | Deferred | 原始音频不保存；未批准数据不采集 | 高端阳；启用前需隐私/法务复核 | 任何真实人员数据前 | 教学/AI 保持禁用 |
| D-010 | Deferred | Provider Adapter + Fake；未批准生产 Provider 时禁用 | 高端阳 | G2-AI 前 | AI 保持禁用 |
| D-011 | Deferred | 自建 + XLSX/CSV 导入 | 高端阳 | G2-Content 前 | 内容能力保持禁用 |
| D-012 | Open | 单区域；部署形态待环境/客户事实 | 高端阳 | Staging 前 | 阻塞真实部署 |
| D-013 | Deferred | 无权利记录不得发布 | 高端阳；启用前需内容权利复核 | G2-Content 前 | 内容发布保持禁用 |
| D-014 | Open | RPO/RTO 按实际环境批准 | 高端阳 | 对应环境启用前 | 阻塞环境恢复承诺 |
| D-015 | Open | 先完成访谈与基线，不用功能数量替代价值 | 高端阳 | 首个真实试点承诺前 | 阻塞 Go/No-Go |
| D-016 | Confirmed | 允许 Simulator-only 工程开发，不通过 G1-Device | 高端阳 | 已确认 2026-08-13 | 阶段 1A |
| D-017 | Confirmed | OpenAI Codex 统一承担五类执行职责，人类批准责任不转移 | 高端阳 | 已确认 2026-08-13 | 全项目执行治理 |
| D-018 | Approved | 高端阳统一承接阶段 1A 五类 A，批准 PRD/RTM 并接受一人多角色风险 | 高端阳 | 已批准 2026-08-13 | 阶段 1A |
| D-019 | Confirmed | 新项目远端使用 `keyboardgdy/lemoo-ai-teaching-platform`；不覆盖既有公开 C# `keyboardgdy/Lemoo` | 高端阳授权范围内由 OpenAI Codex 执行 | 已执行 2026-08-13 | W2 仓库与工具链 |
| D-020 | Confirmed | 高端阳明确决定公开新仓库；Public 后立即启用 `main` 强制保护，不再需要 GitHub Pro 例外 | 高端阳 | 已确认并执行 2026-08-13 | W2 完成，解除后续工作包阻塞 |
| D-021 | Confirmed | 采用 Apache License 2.0，保留贡献者版权并提供明确版权、再分发和专利许可 | 高端阳授权范围内由 OpenAI Codex 执行 | 已执行 2026-08-13 | 开源仓库及贡献治理 |
| GATE-0 | Passed | W0 自动校验 28/28 通过；需求、责任、范围、决策和追踪满足工程准备入口 | 高端阳批准输入；OpenAI Codex 执行校验 | 2026-08-13 | 允许进入工程骨架与 G2-Device 准备 |

## 状态规则

- `Confirmed/Approved`：已有明确决定，可在其限定范围内作为输入。
- `Open`：需要事实或选择；允许准备，不允许隐式生产承诺。
- `Deferred`：未进入当前阶段，能力必须保持禁用。
- `Blocked`：缺少外部事实，相关范围不得启动。

新增或改变产品行为时，先更新 PRD Decision，再同步本表、RTM、Risk Register 和受影响 Gate。

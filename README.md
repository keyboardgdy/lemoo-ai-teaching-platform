# Lemoo 教育机器人云平台

Lemoo 是“题库管理 + AI 机器人互动 + 设备运维”一体化教育机器人云平台。当前仓库处于 **阶段 1A Simulator-only**：只允许合成租户、虚拟设备和非生产环境，不代表真实硬件兼容、真实机构试点或生产准入。

## 当前状态

- PRD/RTM：`1.0.0 Approved for Stage 1A Simulator-only`
- Gate 0：`passed`
- W2、W5a～W5c：`complete`，仓库、协议和必检基线已建立
- W6 实现：领域内核、PostgreSQL/RLS 与首个 FastAPI 控制面纵切已完成；Vue
  设备工作台、Simulator 与 Gate 3-Sim 仍在推进
- G1-Device：`blocked_no_physical_device`
- 内容、教学、AI、OTA：`disabled/not_started`

权威入口：

- [技术栈](docs/01%20fastapi-vue-modern-tech-stack.md)
- [生产架构](docs/02%20fastapi-vue-modern-architecture.md)
- [正式 PRD](docs/product/PRD-001%20教育机器人云平台.md)
- [需求追踪矩阵](docs/product/RTM-001%20教育机器人云平台需求追踪矩阵.md)
- [开发启动门禁](docs/04%20开发前准备与启动门禁.md)

## 本地准备

前置工具：Git、uv、Node.js 24、pnpm 11、Docker Compose、Task。

```text
task bootstrap
task infra:up
task seed
task verify
task dev
task infra:down
```

`task seed` 会执行迁移、建立 `NOBYPASSRLS` 本地应用角色，并只写入
PILOT-001 固定的 2 个合成机构和 6 台虚拟设备。随后 `task dev` 启动 FastAPI
与 Vue 开发服务。

`.env.example` 只有公开的本地示例值。`task bootstrap` 会在不存在时创建未跟踪的 `.env`；不得提交真实凭据、私钥、数据库 Dump、日志包或真实人员数据。

## 工程边界

- `apps/cloud`：FastAPI 模块化单体及独立进程入口，共享唯一 `uv.lock`。
- `apps/web`：Vue 3 + TypeScript strict + Vite SPA。
- `packages`：OpenAPI 和跨边界 Schema 的版本化源。
- `tools/robot-simulator`：后续 W8b 的确定性设备模拟器，目前只有边界占位。
- `infra`：Compose、网关、EMQX、可观测性和镜像配置。

当前已实现的业务面只包含合成会话、租户隔离设备列表/详情和单设备
`refresh_shadow` 命令创建/查询；真实身份、真实设备与未来能力仍不可用。

## 开源许可

本项目以 [Apache License 2.0](LICENSE) 开源。提交贡献即表示贡献内容按该许可证提供；安全问题请按 [Security Policy](SECURITY.md) 私下报告，不要在公开 Issue 中披露漏洞或敏感信息。

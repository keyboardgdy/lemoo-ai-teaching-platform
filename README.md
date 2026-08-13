# Lemoo 教育机器人云平台

Lemoo 是“题库管理 + AI 机器人互动 + 设备运维”一体化教育机器人云平台。当前仓库处于 **阶段 1A Simulator-only**：只允许合成租户、虚拟设备和非生产环境，不代表真实硬件兼容、真实机构试点或生产准入。

## 当前状态

- PRD/RTM：`1.0.0 Approved for Stage 1A Simulator-only`
- Gate 0：`passed`
- W2：`complete`，Windows/Linux CI 与受保护 `main` 已验证
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
task verify
```

启动本地核心依赖：

```text
task infra:up
task infra:down
```

启动 FastAPI 与 Vue 开发服务：

```text
task dev
```

`.env.example` 只有公开的本地示例值。`task bootstrap` 会在不存在时创建未跟踪的 `.env`；不得提交真实凭据、私钥、数据库 Dump、日志包或真实人员数据。

## 工程边界

- `apps/cloud`：FastAPI 模块化单体及独立进程入口，共享唯一 `uv.lock`。
- `apps/web`：Vue 3 + TypeScript strict + Vite SPA。
- `packages`：OpenAPI 和跨边界 Schema 的版本化源。
- `tools/robot-simulator`：后续 W8b 的确定性设备模拟器，目前只有边界占位。
- `infra`：Compose、网关、EMQX、可观测性和镜像配置。

业务功能只能在相应 Requirement、契约和 Gate 就绪后实现。当前健康检查页面和进程占位不是业务能力。

## 开源许可

本项目以 [Apache License 2.0](LICENSE) 开源。提交贡献即表示贡献内容按该许可证提供；安全问题请按 [Security Policy](SECURITY.md) 私下报告，不要在公开 Issue 中披露漏洞或敏感信息。

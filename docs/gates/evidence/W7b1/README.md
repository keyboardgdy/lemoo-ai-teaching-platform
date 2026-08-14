# W7b1 证据：基础质量与浏览器门禁

日期：2026-08-14；范围：Stage 1A Simulator-only、合成数据、非生产。

## 交付

- `task verify` 统一执行锁定依赖下的 Backend 格式/Lint、Pyright、单元/集成/API
  测试、覆盖率、Build，以及 Frontend OpenAPI/Orval 漂移、格式/Lint、Vue 类型、
  Vitest、覆盖率和 Build；协议、文档、仓库结构、Schema 与 Compose 配置检查保持开启。
- `task test:e2e` 先迁移数据库、配置 `NOBYPASSRLS` 应用角色并幂等写入 PILOT-001
  的 6 台固定合成设备，再运行独立 Playwright 测试。
- Playwright 通过真实 FastAPI、PostgreSQL 与 Vue 开发服务器验证：ORG-A 操作员只能看到
  本租户 4 台设备并可创建唯一允许的 `refresh_shadow` 命令；管理员保持只读；ORG-B
  只能看到本租户 2 台设备。
- Windows `lem-api` 入口显式使用 Psycopg 支持的 Selector 事件循环；非 Windows 平台仍由
  Uvicorn 选择原生事件循环。两条平台分支均有单元测试。
- Control Plane 启动时加载完整 SQLAlchemy 模型注册表并 fail closed；独立 Python 进程
  回归测试防止测试收集顺序掩盖缺失外键目标。
- CI 新增独立、失败即关闭的 `e2e` 结果；Linux 使用 runner 预装 Chrome 运行同一
  `task test:e2e`。`compose` 结果从静态配置检查升级为真实四容器启动、健康等待和 EMQX
  mTLS 正反 smoke，并在成功或失败后清理容器。短生命周期、无网络的 PKI init 容器
  将 Compose secret 复制到仅 EMQX 用户可读的命名卷，避免 Linux bind-mounted secret
  保留宿主 `0600` 所有权后令非 root EMQX 无法读取私钥。

## TDD 与失败证据

- RED Commit `07a5369`：新增真实 Playwright 场景；Windows 上两条设备列表断言均因
  `ProactorEventLoop` 不受异步 Psycopg 支持而失败。
- GREEN Commit `43c7394`：修复跨平台 API runner、模型注册与统一 E2E Task；随后浏览器
  深入到命令提交并暴露此前被测试顺序掩盖的 `organizations` 外键元数据缺失，修复后
  2 条场景全部通过。
- Fix Commit `3975185`：全仓验证证明 Vitest 会误收集 `e2e/*.spec.ts`；将 Vitest 与
  Playwright 的测试目录显式隔离后，两个门禁各自独立通过。

## 本地验证

- `task verify`：PASS。
  - Backend：49 项通过，覆盖率 93.60%，Ruff、Pyright、Build 通过。
  - Protocol：27 项通过。
  - Frontend：9 项通过；SFC 语句/行 99.24%、分支 92.30%、函数 100%；ESLint、
    Prettier、Vue 类型、Build 通过。
  - Docs、Repo、Compose config、Schema/OpenAPI 与 Orval drift：PASS。
- `task test:e2e`：PASS，2 项真实浏览器场景通过。
- `task migrate:test`：PASS；空库升级、重复升级、降级后升级、RLS 与不可变审计均通过。

## 尚待 PR CI 固化的证据

本地 Windows 结果已经完成。Linux `e2e`、真实 Compose 启动与 mTLS smoke 必须在本分支
PR 的独立检查中通过后，W7b1 才满足跨平台退出条件；不得用本地结果替代该检查。W7b4
将依据 01 的完整权威集合统一分支保护，本切片不提前改变 Required Check 集合。

本证据不授权生产部署、真实设备/机构/个人数据或生产 Secret，也不启用 Content、
Teaching、AI、Diagnostics、Bulk Command 或 OTA。

# 教育机器人云平台唯一生产级技术栈基线

> 更新时间：2026 年 8 月  
> 产品与领域基线：[教育机器人云平台产品与系统设计](03%20ai-teaching-platform-design.md)  
> 实施架构基线：[教育机器人云平台生产架构设计](02%20fastapi-vue-modern-architecture.md)

本文回答“项目统一使用什么技术”。业务定位、用户场景和领域规则以 03 为准；进程边界、依赖方向、数据流和部署方式以 02 为准。本文所有标记为“启用”的组件均进入开发、测试、部署和运维范围，不再通过 Profile 或覆盖说明改变状态。

项目唯一技术路线是：

> Vue 3 + TypeScript + Vite 管理后台  
> FastAPI 模块化单体 + 独立 Gateway/Worker 进程  
> PostgreSQL + Redis + S3 统一数据基础设施  
> EMQX + MQTT 5 over TLS 连接机器人  
> WebSocket 承载流式 AI 互动，SSE 承载 Web 运维事件  
> Dramatiq + Redis + PostgreSQL Outbox 承载可靠异步任务  
> OpenTelemetry + Prometheus/Grafana/Loki/Tempo + Sentry 完成可观测性

## 一、决策状态与约束

技术项只有两种状态：

| 状态 | 含义 |
|---|---|
| 启用 | 必须纳入本地环境、CI、生产部署、监控、备份和故障演练 |
| 预留 | 已明确接入边界，但当前不得安装、部署或成为运行依赖 |

以下原则不可由单个功能开发自行改变：

1. 云端保持模块化单体代码库，但 API、设备接入、AI 互动和后台任务按进程隔离。
2. PostgreSQL 是业务事实源；Redis、EMQX 和可观测系统都不是业务主数据库。
3. 浏览器只访问 Caddy/FastAPI，不直连 EMQX，也不持有设备凭证。
4. MQTT 只传小型状态、遥测、事件、通知与 ACK；文件和连续音频走 HTTPS/WebSocket。
5. AI 只能输出结构化教学建议和白名单动作 ID，不能获得设备运维权限。
6. OTA 使用签名、兼容性、过期和发布计数校验，不能退化为普通文件下载。
7. 任何新增框架、中间件或数据库都必须通过 ADR，同时更新 01、02、03 中受影响的约束。

## 二、唯一技术栈总表

### 1. 语言、运行时与工程工具

| 领域                 | 唯一选择              | 状态  | 用途                          |
| ------------------ | ----------------- | --- | --------------------------- |
| 后端语言               | Python 3.14       | 启用  | API、Gateway、Worker、模拟器和运维工具 |
| Python 包管理         | uv                | 启用  | Python、虚拟环境、依赖解析和 `uv.lock` |
| 前端语言               | TypeScript strict | 启用  | Vue 管理后台和生成客户端              |
| JavaScript Runtime | Node.js 24 LTS    | 启用  | 前端构建、测试和代码生成                |
| 前端包管理              | pnpm Workspace    | 启用  | 前端依赖与 `pnpm-lock.yaml`      |
| 任务入口               | Taskfile          | 启用  | 本地与 CI 使用同一命令               |
| 版本管理               | Git + GitHub      | 启用  | 源码、评审和发布追踪                  |

运行时版本通过 `.python-version`、`.node-version`、`package.json#engines` 和 CI 固定。第三方包精确版本不写死在文档中，以锁文件为唯一解析结果；升级由 Renovate 提交并通过完整门禁。

### 2. 云端后端

| 领域                | 唯一选择               | 状态  | 用途                                          |
| ----------------- | ------------------ | --- | ------------------------------------------- |
| Web/API 框架        | FastAPI            | 启用  | Web REST、Device HTTPS API、SSE 和受限 WebSocket |
| ASGI Server       | Uvicorn            | 启用  | 所有 ASGI 进程                                  |
| Schema/DTO        | Pydantic           | 启用  | REST、MQTT、WebSocket、命令和任务消息验证               |
| 配置                | pydantic-settings  | 启用  | 类型化环境配置与 Secret 文件                          |
| ORM               | SQLAlchemy 2 Async | 启用  | Typed ORM 和异步事务                             |
| PostgreSQL Driver | psycopg 3          | 启用  | 异步连接池                                       |
| 数据迁移              | Alembic            | 启用  | Schema、RLS、索引和分区迁移                          |
| 异步 HTTP           | httpx              | 启用  | AI Provider、对象存储辅助接口和内部 HTTP                |
| 密码哈希              | pwdlib + Argon2id  | 启用  | Web 用户密码                                    |
| 结构化日志             | structlog          | 启用  | JSON Log 和关联字段                              |
| 重试                | tenacity           | 启用  | 仅用于有界、可重试的外部调用                              |

后端使用一套代码库和多个进程入口：

```text
api
device-gateway
interaction-gateway
outbox-dispatcher
worker-content
worker-operations
worker-analytics
scheduler
```

这不是微服务拆分。进程共享领域模型、数据库迁移、协议 Schema 和发布版本，但具有独立的连接池、并发、伸缩、健康检查和故障边界。

### 3. 数据与异步基础设施

| 领域      | 唯一选择                        | 状态  | 用途                                 |
| ------- | --------------------------- | --- | ---------------------------------- |
| 关系数据库   | PostgreSQL                  | 启用  | 业务事实、Session、租户数据、设备与教学记录          |
| 时序/事件存储 | PostgreSQL 原生分区             | 启用  | 遥测、设备事件、命令事件、教学事件和审计               |
| 租户隔离    | PostgreSQL RLS + Service 授权 | 启用  | 机构数据双重隔离                           |
| 基础搜索    | PostgreSQL FTS + `pg_trgm`  | 启用  | 题库、设备、事件和日志索引查询                    |
| 内存数据层   | Redis                       | 启用  | Dramatiq Broker、限流、短期状态、实时扇出和分布式协调 |
| 后台任务    | Dramatiq                    | 启用  | 导入、内容包、日志、告警、OTA、AI 评测和清理          |
| 可靠事件    | PostgreSQL Outbox           | 启用  | 数据提交与任务/MQTT 发布的一致性                |
| 对象存储    | S3 API                      | 启用  | 固件、内容包、媒体、导入文件和诊断包                 |
| 本地对象存储  | MinIO                       | 启用  | 本地、测试和私有环境的 S3 兼容实现                |

Redis 的使用边界固定为：

- 不保存设备、命令、OTA、教学或 AI Run 的唯一事实。
- Key 必须包含命名空间、版本、租户或业务范围，并设置 TTL。
- Redis 故障时允许新任务和实时推送暂缓，但已发布内容的机器人教学仍可继续。
- Worker 必须从 PostgreSQL Job/Outbox 恢复，不依赖 Redis 中的消息永久存在。
- 分布式锁只保护调度和竞争窗口，数据库约束仍是最终一致性防线。

### 4. 机器人连接与设备协议

| 领域                 | 唯一选择                                | 状态  | 用途                                     |
| ------------------ | ----------------------------------- | --- | -------------------------------------- |
| MQTT Broker        | EMQX                                | 启用  | MQTT 5、TLS、认证、ACL、Will、持久会话和共享订阅       |
| 设备消息协议             | MQTT 5 over TCP/TLS                 | 启用  | 状态、遥测、事件、命令、ACK、OTA/内容通知               |
| Python MQTT Client | paho-mqtt                           | 启用  | Device Gateway、Robot Simulator、测试和运维工具 |
| 设备身份               | 每设备 X.509 mTLS                      | 启用  | MQTT 和 Device HTTPS API 身份             |
| 私有 PKI             | 离线 Root CA + Device Intermediate CA | 启用  | 设备证书签发、轮换和吊销                           |
| 设备协议描述             | JSON Schema + Pydantic              | 启用  | MQTT Envelope、版本兼容和 CI 契约测试            |
| 大文件通道              | HTTPS + S3 Presigned URL            | 启用  | 固件、内容包、诊断包和媒体                          |

设备优先使用 MQTT TCP/TLS，不使用 MQTT over WebSocket。每台机器人具有独立证书，Broker 将证书身份绑定到唯一 `device_id`，设备不得使用 `+`、`#` 订阅，也不能越过自己的 Topic 空间。

MQTT Payload 使用版本化 JSON。若真实机器人证明 JSON 的带宽或 CPU 开销无法满足 SLO，才通过 ADR 评估 Protobuf/CBOR；当前不同时维护两套编码。

### 5. AI 互动与治理

| 领域 | 唯一选择 | 状态 | 用途 |
|---|---|---|---|
| 互动通道 | WebSocket over TLS | 启用 | 双向文本、音频片段、状态和流式结果 |
| AI 接入 | 内部类型化 AI Gateway | 启用 | ASR、LLM、TTS Provider Adapter |
| Provider 调用 | httpx + 官方 SDK（仅确有必要时） | 启用 | 超时、取消、限流和流式响应 |
| 教学编排 | 确定性 Orchestrator 状态机 | 启用 | 评分、提示、追问、解释和动作约束 |
| Prompt/Model 治理 | PostgreSQL 版本记录 | 启用 | Prompt、模型、参数、成本、评测和发布 |
| AI 异步评测 | Dramatiq Worker | 启用 | 数据集评测、抽检和回归 |

AI Gateway 对上层暴露内部稳定能力，而不是 Provider API：

```text
transcribe_audio
judge_semantic_answer
generate_hint
generate_explanation
generate_follow_up
synthesize_speech
```

统一输出 Pydantic Schema，保存 `ai_run_id`、能力、模型、Prompt 版本、输入输出引用、延迟、Token/音频用量、成本、安全结果和 Fallback。客观题由确定性逻辑评分；AI 不直接获得 MQTT、OTA、数据库、凭证或任意网络工具。

LangChain、LlamaIndex、通用 Agent 框架、向量数据库和 RAG 不进入当前基线。平台首先解决受控机器人互动；只有出现经批准的知识检索场景时，再新增独立 ADR。

### 6. Web 管理后台

| 领域 | 唯一选择 | 状态 | 用途 |
|---|---|---|---|
| 框架 | Vue 3 | 启用 | Composition API + `<script setup>` |
| 构建 | Vite | 启用 | 单页管理后台 |
| 路由 | Vue Router | 启用 | 页面路由、权限元数据和懒加载 |
| 服务端状态 | TanStack Vue Query | 启用 | REST 数据缓存、失效、轮询和 Mutation |
| 客户端状态 | Pinia | 启用 | 当前用户、全局 UI 和跨页工作流 |
| API Client | Orval + Fetch | 启用 | 由 OpenAPI 生成类型、请求和 Query Hooks |
| 表单 | vee-validate + Zod | 启用 | 复杂表单状态和即时验证 |
| CSS | Tailwind CSS | 启用 | Design Token 与原子样式 |
| 组件系统 | shadcn-vue + Reka UI | 启用 | 可访问的可组合组件 |
| 图标 | Lucide Vue | 启用 | 统一图标 |
| 国际化 | vue-i18n | 启用 | 管理后台多语言 |
| 数据表格 | TanStack Vue Table | 启用 | 设备、题库、会话、命令和 OTA 表格 |
| 图表 | Apache ECharts + vue-echarts | 启用 | 遥测趋势、告警、OTA 漏斗和教学分析 |
| Markdown/公式 | markdown-it + KaTeX | 启用 | 题干、解析和数学公式安全预览 |
| 状态图编辑 | Vue Flow | 启用 | 互动脚本状态机可视化编辑 |
| Web 实时事件 | Native EventSource | 启用 | 在线状态、告警、命令、任务和 OTA 进度 |
| 受限实时诊断 | Native WebSocket | 启用 | 明确开始/结束的单设备诊断流 |

前端固定为 Vite SPA，由 Caddy 托管，不使用 Nuxt、SSR、Node BFF 或微前端。公开营销网站如有需要，应作为独立站点，不改变管理后台架构。

状态所有权固定为：

| 状态 | 归属 |
|---|---|
| API 数据、加载、缓存、重试 | TanStack Query |
| 当前用户、界面偏好、跨页草稿流程 | Pinia |
| 筛选、分页、Tab、选中时间窗 | URL Query |
| 表单值与字段错误 | vee-validate |
| 单组件短期状态 | `ref` / `reactive` |
| 在线/告警/命令实时增量 | SSE 收到后更新 Query Cache |

不得把 API 返回值整份复制进 Pinia。浏览器的权限判断只控制展示，后端仍必须执行 RBAC、机构和资源归属检查。

### 7. Web 身份与安全

| 领域 | 唯一选择 | 状态 | 用途 |
|---|---|---|---|
| Web 登录 | 邮箱/用户名 + 密码 | 启用 | 首期人员登录 |
| 密码哈希 | Argon2id | 启用 | 密码安全存储 |
| Web Session | PostgreSQL Server-side Session | 启用 | 可撤销、可审计的浏览器会话 |
| 浏览器凭证 | HttpOnly + Secure + SameSite Cookie | 启用 | 不向 JavaScript 暴露 Token |
| CSRF | 同源 Token 校验 | 启用 | 所有状态修改请求 |
| 授权 | RBAC + 机构/资源归属 + PostgreSQL RLS | 启用 | 多租户和角色隔离 |
| 高风险操作 | Re-auth + Reason + Audit + 可选双人审批 | 启用 | 命令、诊断、证书、内容和 OTA |

Web Session 保存在 PostgreSQL，Redis 只用于限流和短期协调。前端不得把 Access Token、Refresh Token 或设备凭证放进 `localStorage`。

### 8. 可观测性

| 领域 | 唯一选择 | 状态 | 用途 |
|---|---|---|---|
| Instrumentation | OpenTelemetry | 启用 | HTTP、任务、Gateway、数据库和 AI Trace/Metric |
| Telemetry Gateway | OpenTelemetry Collector | 启用 | OTLP 接收、处理和导出 |
| Metric | Prometheus | 启用 | 指标抓取与规则 |
| Dashboard/Alert | Grafana | 启用 | 仪表盘和统一告警视图 |
| Log | structlog + Loki | 启用 | JSON Log 聚合检索 |
| Trace | Tempo | 启用 | 分布式链路 |
| Error Tracking | Sentry | 启用 | Web 和 Python 异常聚合 |

统一关联字段：

```text
request_id
trace_id
organization_id
device_id
boot_id
teaching_session_id
interaction_turn_id
command_id
ota_release_id
deployment_id
ai_run_id
job_id
```

业务 ID 只进入 Log/Trace，不得作为 Prometheus 高基数 Label。

### 9. 测试与质量

| 领域 | 唯一选择 | 状态 |
|---|---|---|
| Python Lint/Format | Ruff | 启用 |
| Python Type Check | Pyright strict | 启用 |
| Python Test | pytest + pytest-asyncio | 启用 |
| 属性测试 | Hypothesis | 启用 |
| 集成环境 | Testcontainers | 启用 |
| HTTP Mock | respx | 启用 |
| Test Data | Polyfactory | 启用 |
| 前端 Lint/Format | ESLint + Prettier | 启用 |
| Vue Type Check | vue-tsc | 启用 |
| 前端单元测试 | Vitest | 启用 |
| 组件测试 | Vue Test Utils | 启用 |
| API Mock | MSW | 启用 |
| E2E | Playwright | 启用 |
| API 兼容 | oasdiff | 启用 |
| 设备仿真 | 自研 Robot Simulator（Python + paho-mqtt） | 启用 |
| HTTP/WSS 压测 | Locust | 启用 |
| 安全扫描 | Trivy | 启用 |
| SBOM | Syft/CycloneDX | 启用 |

集成测试使用真实 PostgreSQL、Redis、EMQX 和 S3 API，禁止用 SQLite 替代 PostgreSQL。Robot Simulator 是产品基础设施，不是临时脚本，必须支持：

- 独立设备证书和 ACL 测试。
- 上下线、Will、心跳、Shadow 和遥测。
- 乱序、重复、断网、离线缓冲和重连风暴。
- 命令 ACK、超时、拒绝和重复投递。
- 内容同步、OTA 成功/失败/回滚。
- 教学事件补传和 AI WebSocket 会话。

### 10. 基础设施与交付

| 领域 | 唯一选择 | 状态 | 用途 |
|---|---|---|---|
| 容器 | Docker | 启用 | 可重复构建和运行 |
| 首期编排 | Docker Compose | 启用 | 本地、测试和首期生产 |
| Web 网关 | Caddy | 启用 | TLS、SPA、REST、SSE 和 WebSocket 反代 |
| CI/CD | GitHub Actions | 启用 | 检查、测试、构建、签名和部署 |
| 依赖更新 | Renovate | 启用 | 自动升级和回归 |
| 镜像扫描 | Trivy | 启用 | OS 和依赖漏洞 |
| 镜像/制品签名 | Cosign | 启用 | 云端镜像和发布制品验证 |
| 密钥注入 | Docker Secret / 部署环境 Secret | 启用 | 普通服务运行时 Secret |

云端容器镜像必须多阶段构建、锁定依赖、使用非 root 用户、固定基础镜像版本或 Digest、生成 SBOM 并通过漏洞扫描。数据库迁移由独立 Job 执行，API/Gateway/Worker 不得在并发启动时自动迁移。

## 三、协议与数据格式

| 边界 | 格式 | 版本策略 |
|---|---|---|
| Web REST | JSON + OpenAPI 3.1 | `/api/v1` + Schema 兼容检查 |
| Device HTTPS | JSON + OpenAPI 3.1 | `/device-api/v1`，独立认证与限流 |
| MQTT | 版本化 JSON Envelope | `schema` + Major Topic/Schema |
| Interaction WebSocket | 版本化 JSON Control Frame + Binary Audio Frame | 握手协商协议版本 |
| SSE | 标准 SSE Event | `event` 类型 + 单调事件 ID |
| Worker | Pydantic Job Payload | `job_type` + `schema_version` |
| Outbox | PostgreSQL Record | Event Type + Payload Version |
| 内容包 | Signed Manifest + immutable files | Package Version + Compatibility |
| OTA | TUF/Uptane 思路的签名元数据 | Role、Version、Expiry、Release Counter |

禁止跨边界直接序列化 ORM Model。OpenAPI、JSON Schema、MQTT Schema 和 WebSocket Frame Schema 都必须提交仓库并在 CI 做向后兼容检查。

## 四、后端依赖清单

基础依赖：

```text
fastapi[standard]
pydantic
pydantic-settings
sqlalchemy[asyncio]
psycopg[binary,pool]
alembic
httpx
structlog
pwdlib[argon2]
python-multipart
redis
dramatiq[redis]
paho-mqtt
tenacity
boto3
orjson
```

可观测依赖：

```text
opentelemetry-api
opentelemetry-sdk
opentelemetry-exporter-otlp
opentelemetry-instrumentation-fastapi
opentelemetry-instrumentation-sqlalchemy
opentelemetry-instrumentation-httpx
sentry-sdk[fastapi]
prometheus-client
```

开发依赖：

```text
ruff
pyright
pytest
pytest-asyncio
pytest-cov
testcontainers
hypothesis
polyfactory
respx
locust
pre-commit
```

若 Provider 官方 SDK 只是对 HTTP 的薄封装，优先使用 `httpx` Adapter，避免把 Provider 类型扩散到领域层。任何新增 SDK 必须包在 `infrastructure/ai/providers/` 内。

## 五、前端依赖清单

运行依赖：

```text
vue
vue-router
pinia
@tanstack/vue-query
@tanstack/vue-table
vee-validate
zod
vue-i18n
reka-ui
lucide-vue-next
echarts
vue-echarts
markdown-it
katex
@vue-flow/core
```

构建与测试依赖：

```text
vite
typescript
vue-tsc
tailwindcss
orval
eslint
eslint-plugin-vue
prettier
vitest
@vue/test-utils
msw
playwright
```

只生成 Fetch Client，不安装 Axios。生成文件放在 `apps/web/src/shared/api/generated/`，禁止手工修改；鉴权、CSRF、Problem Details、Request ID 和错误归一化放在唯一 Fetch Mutator 中。

## 六、固定 Monorepo 布局

```text
lemoo/
├── apps/
│   ├── cloud/                         # Python 模块化单体代码
│   │   ├── app/
│   │   │   ├── entrypoints/           # api/gateway/dispatcher/worker/scheduler
│   │   │   ├── modules/               # 领域模块
│   │   │   ├── infrastructure/        # pg/redis/mqtt/s3/ai/telemetry
│   │   │   └── shared/
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── uv.lock
│   └── web/
│       ├── src/
│       ├── e2e/
│       └── package.json
├── packages/
│   ├── protocol-schemas/              # MQTT/WS/Job JSON Schema
│   ├── openapi/                       # 固化的 OpenAPI 输出
│   └── content-package-schema/
├── tools/
│   ├── robot-simulator/
│   ├── ota-metadata/
│   └── data-maintenance/
├── infra/
│   ├── compose/
│   ├── caddy/
│   ├── emqx/
│   ├── observability/
│   └── docker/
├── docs/
│   └── decisions/
├── scripts/
├── .github/workflows/
├── compose.yaml
├── pnpm-workspace.yaml
├── Taskfile.yml
└── README.md
```

Python 进程全部来自 `apps/cloud`，避免复制领域模型或建立多个互相漂移的锁文件。`packages/protocol-schemas` 是机器人端和云端共享协议的发布源，但不包含任何 Secret。

## 七、环境与部署组件

### 1. 本地开发

```text
caddy
web
api
device-gateway
interaction-gateway
outbox-dispatcher
worker-content
worker-operations
worker-analytics
scheduler
emqx
redis
postgresql
minio
otel-collector
prometheus
grafana
loki
tempo
```

可通过 Compose Profile 只启动当前开发所需的 Worker 或观测 UI，但 PostgreSQL、Redis、EMQX 和协议测试不得从 CI 集成环境中省略。

### 2. 首期生产

- Caddy、Web、API 与各 Python 进程使用不可变镜像。
- PostgreSQL、S3、Redis 和 EMQX 可以使用受管服务或独立持久节点，但接口和语义不变。
- Gateway 与 Worker 按职责独立扩容，不通过增加 API Worker 间接扩容 MQTT/AI。
- EMQX、PostgreSQL、S3、设备 CA 与 OTA 签名材料必须有加密备份和恢复演练。
- Redis 可重建，仍需持久化/高可用配置以减少任务停顿，但不把它升级为事实源。

### 3. OTA 加密基线

推荐且唯一默认算法为 SHA-256 + ECDSA P-256；设备必须在安装前验证 Metadata Role、签名阈值、Hash、Length、型号/硬件兼容、版本、Expiry 和单调 Release Counter。离线 Root Key 与在线发布角色 Key 分离，普通 Web/API/Worker 不能读取签名私钥。

如果阶段 0 确认现有硬件安全模块不支持该算法，必须先形成替代算法 ADR 和迁移策略，不能在业务代码中静默降级验签。

## 八、CI/CD 固定门禁

每个 Pull Request 至少执行：

```text
Backend
uv lock --check
ruff check
ruff format --check
pyright
pytest unit/integration/api/worker
alembic migration test

Frontend
pnpm install --frozen-lockfile
eslint
prettier --check
vue-tsc --noEmit
vitest run
vite build
playwright test

Contracts
export OpenAPI
Orval generate
git diff --exit-code generated files
oasdiff breaking check
MQTT JSON Schema compatibility
WebSocket/Job Schema compatibility

Robot and security
Robot Simulator integration
EMQX ACL isolation tests
Device API mTLS tests
Command allowlist/idempotency tests
OTA metadata/signature/rollback tests
AI action allowlist tests
PostgreSQL RLS/partition tests

Supply chain
Trivy scan
SBOM generation
immutable image build
artifact/image signature
```

云端应用发布与机器人 OTA 是两套独立流水线。云端镜像发布不得自动创建 OTA Release，固件构建也不得自动部署云端应用。

## 九、明确预留但暂不引入

| 预留能力 | 固定候选 | 启用条件 |
|---|---|---|
| 容器编排 | Kubernetes | Compose 已无法满足容量、隔离或可用性目标 |
| 海量时序分析 | TimescaleDB 或 ClickHouse，届时 ADR 二选一 | PostgreSQL 分区经压测和调优后仍无法满足 SLO |
| 独立搜索集群 | OpenSearch | PostgreSQL FTS/Trigram 无法满足已量化搜索需求 |
| OTA/内容全球分发 | CDN | S3 出口、地域延迟或并发下载达到明确阈值 |
| 企业身份 | OIDC Authorization Code + PKCE | 出现学校/企业 SSO 需求 |
| 强身份 | WebAuthn/Passkey + TOTP 恢复策略 | 账号风险评估要求正式启用 MFA |
| 独立策略引擎 | OPA | RBAC/RLS/资源授权规则复杂到无法安全维护 |
| 消息流平台 | Kafka | Outbox + Worker + PostgreSQL 无法承载已量化事件吞吐/回放需求 |
| 媒体传输 | WebRTC | WebSocket 音频在真实网络中无法满足互动质量目标 |
| AI 知识检索 | pgvector 起步 | 出现经评审的 RAG 知识库需求与评测集 |

预留不代表可以提前加入依赖。微服务、RabbitMQ/Celery、GraphQL、Socket.IO、通用 AI Agent、Service Mesh、CQRS/Event Sourcing 和多主数据库不属于当前路线。

## 十、最终唯一组合

```text
Cloud
Python 3.14 + uv
FastAPI + Uvicorn
Pydantic + pydantic-settings
SQLAlchemy 2 Async + psycopg 3 + Alembic
PostgreSQL + RLS + Native Partitioning + FTS/pg_trgm
Redis + Dramatiq + PostgreSQL Outbox
S3 API / MinIO

Robot connectivity
EMQX
MQTT 5 over TCP/TLS
Per-device X.509 mTLS
paho-mqtt
JSON Schema + Pydantic protocol validation
HTTPS Presigned URL for files

AI interaction
WebSocket over TLS
Typed AI Gateway
Deterministic Teaching Orchestrator
ASR/LLM/TTS Provider Adapters
Versioned Prompt/Model/AIRun governance

Web
Vue 3 + TypeScript strict + Vite
Vue Router + TanStack Vue Query + Pinia
Orval + Fetch
vee-validate + Zod
Tailwind CSS + shadcn-vue + Reka UI
TanStack Vue Table + ECharts + Vue Flow
markdown-it + KaTeX
Native SSE + WebSocket

Quality and operations
Ruff + Pyright + pytest + Testcontainers
Vitest + Vue Test Utils + MSW + Playwright
Robot Simulator + Locust
Docker Compose + Caddy
OpenTelemetry + Prometheus + Grafana + Loki + Tempo + Sentry
GitHub Actions + Renovate + Trivy + SBOM + Cosign
```

该组合是教育机器人云平台当前唯一实施基线。Redis、Dramatiq、SSE、WebSocket、EMQX、设备 Gateway、AI Gateway 与安全 OTA 均为正式启用能力，不再列为“未来 Profile”。

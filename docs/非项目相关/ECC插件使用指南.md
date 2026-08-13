# ECC 插件使用指南（Codex）

> 适用环境：Codex App / Codex CLI  
> ECC 版本：2.2.0  
> 核对日期：2026-08-12  
> 官方仓库：[affaan-m/ECC](https://github.com/affaan-m/ECC)  
> 官方网站：[ecc.tools](https://ecc.tools)

本文介绍如何在 Codex 中正确使用 Everything Claude Code（ECC）插件，包括技能、兼容命令、Agent、Hook、MCP、安装升级、工作流组合和常见故障处理。

本文依据当前已安装的 ECC 2.2.0 文件和 Codex 实际注册状态生成。ECC 更新较快，组件数量或名称变化时，应以实时插件清单为准。

## 一、ECC 是什么

ECC 是一套面向 AI 编程代理的工程工作流集合。它不替代 Codex，也不是一个新的编程语言或 Web 框架；它主要给 Codex 增加经过整理的工作方法和专业知识，例如：

- 测试驱动开发。
- FastAPI、Vue、PostgreSQL、Redis 等技术模式。
- API、架构、数据库和部署设计。
- 代码审查、安全审查和生产就绪审计。
- E2E、性能、回归和验证流程。
- 文档治理、代码库入门和上下文管理。
- 多种业务、研究、运营和 Agent 工程工作流。

可以把二者的关系理解为：

```text
Codex
├── 模型推理与对话
├── 文件、终端、网络和其他工具
├── 权限、安全与协作机制
└── ECC 插件
    ├── Skills：可复用工作流与专业知识
    ├── Hooks：受信任后运行的生命周期自动化
    ├── MCP：可选外部工具连接
    ├── Commands：兼容不同 Harness 的命令入口
    ├── Agents：可供不同 Harness 使用的角色定义
    └── Rules/Scripts：规则包、安装和维护工具
```

ECC 最有价值的地方不是“拥有很多技能”，而是让任务采用清晰、可重复、可验证的工程流程。

## 二、当前安装状态

当前机器检测结果：

| 项目 | 当前状态 |
|---|---|
| 插件 ID | `ecc@ecc` |
| 插件短名 | `ecc` |
| 版本 | `2.2.0` |
| 安装状态 | 已安装 |
| 启用状态 | 已启用 |
| Marketplace | `affaan-m/ECC` |
| Codex 安装模式 | 原生 Marketplace 插件 |
| 默认 MCP | `chrome-devtools` |
| 原生 Codex Hook | 一个 `SessionStart` Hook，需显式信任 |

Codex 官方当前将插件定位为 Skills、Connector/MCP、Hook 等能力的可安装组合。插件可在 Codex CLI 和 ChatGPT 桌面应用的 Codex 界面使用；Codex IDE Extension 当前不支持插件。参见 [Codex 官方 Plugins 指南](https://learn.chatgpt.com/docs/plugins)。

实时仓库目录统计为：

| 组件 | 数量 | 在 Codex 中的意义 |
|---|---:|---|
| Skills | 287 | 主要使用界面，按需加载 |
| Commands | 94 | 主要用于 Slash Command 兼容，不是 Codex 首选入口 |
| Agent 定义 | 68 | 跨 Harness 角色资源，不代表 Codex 自动注册 68 个子代理 |

ECC 2.2.0 的插件展示描述中仍可能出现“281 Skills”，但实时 Catalog 脚本统计为 287。出现类似不一致时，以以下命令和当前会话的可用技能列表为准：

```powershell
codex plugin list --json
```

在 ECC 源码检出目录中还可以运行：

```powershell
node scripts/ci/catalog.js --json
```

不要直接编辑 Codex 插件缓存目录；升级插件时缓存内容可能被整体替换。

## 三、最重要的使用原则

### 1. Skills First：优先使用技能

ECC 的主界面是 Skill。用户应该直接告诉 Codex 使用哪个技能和完成什么任务，而不是先寻找旧式 Slash Command。

推荐写法：

```text
请使用 ecc:tdd-workflow，为登录限流功能先写失败测试，再实现并验证。
```

```text
请使用 ecc:fastapi-patterns 和 ecc:api-design，审查用户接口设计；只审查，不修改代码。
```

```text
请使用 ecc:verification-loop，验证当前改动；运行相关测试、类型检查和构建，并给出证据。
```

在支持 `$` 技能补全的 Codex 客户端中，可以输入 `$` 后从列表选择 ECC 技能。不同版本可能显示为 `$configure-ecc` 或带插件前缀的名称，选择自动补全结果比手工猜别名更可靠。

### 2. 每一轮明确指定需要的技能

技能通常只对当前任务轮次生效。下一轮如果仍希望使用某个技能，应再次点名：

```text
继续使用 ecc:tdd-workflow 修复第二个失败用例。
```

不要假设上一轮提到过的技能会永久附着在整个会话上。

### 3. 一次使用最小技能集合

通常一个主技能加一到两个领域技能就足够：

```text
主流程：ecc:tdd-workflow
领域约束：ecc:fastapi-patterns
完成验证：ecc:verification-loop
```

一次点名十几个技能会增加上下文、产生规则冲突，并降低执行重点。先选择主流程，需要时再追加专业技能。

### 4. 明确操作权限

Skill 决定“怎么做”，不自动扩大 Codex 的授权范围。提示词应说明任务是只读审查还是允许修改：

```text
请使用 ecc:security-review 审查 authentication 模块，只输出问题和建议，不修改文件。
```

```text
请使用 ecc:tdd-workflow 修复该缺陷，允许修改相关代码和测试，但不要改动数据库 Schema。
```

### 5. 明确完成标准

高质量请求至少包含范围和验证方式：

```text
请使用 ecc:vue-patterns 重构设备详情页。
范围仅限 apps/web/src/features/device-detail。
保持现有 API 不变，运行 vue-tsc、Vitest 和对应 Playwright 用例。
```

通用请求公式：

```text
动作 + 精确技能名 + 目标 + 范围 + 允许的改动 + 验证方式 + 输出位置
```

## 四、ECC 的组件如何协作

### 1. Skills

Skill 是包含完整工作流程和领域知识的 `SKILL.md`。它可能要求 Codex：

- 先读取项目证据。
- 遵循固定步骤。
- 使用指定工具或检查项。
- 在修改前建立测试。
- 在完成前运行验证。
- 生成特定格式的报告或文件。

Skill 可以由用户显式点名，也可能在任务与其描述高度匹配时由 Codex 自动选择。显式点名最可靠。Codex 官方约定使用 `$` 显式选择 Skill，详见 [Skills & Plugins](https://learn.chatgpt.com/docs/skills-and-plugins)。

### 2. Commands

ECC 仍保留 94 个 `commands/*.md`，主要服务于 Claude Code Slash Command 和旧工作流兼容，例如 `/plan`、`/build-fix`、`/security-scan`。

在 Codex 中：

- 优先寻找对应的 `ecc:<skill-name>`。
- 不要假设 README 中的 `/ecc:plan`、`/code-review` 一定是 Codex 原生 Slash Command。
- 部分命令会以 `ecc:source-command-*` 的迁移技能形式出现。
- `source-command-*` 是兼容入口；如果存在更直接的领域 Skill，优先使用领域 Skill。

示例：

| 目标 | Codex 首选 |
|---|---|
| FastAPI 开发规范 | `ecc:fastapi-patterns` |
| FastAPI 命令式审查流程 | `ecc:source-command-fastapi-review`，仅需兼容命令流程时使用 |
| 测试驱动开发 | `ecc:tdd-workflow` |
| 安全代码审查 | `ecc:security-review` |
| Agent 配置扫描 | `ecc:security-scan` |
| 完成前验证 | `ecc:verification-loop` |

### 3. Agents

ECC 仓库包含 68 个 Agent 角色定义，例如 Planner、Reviewer、Security Reviewer、TDD Guide 和各语言 Reviewer。

需要注意：

- Agent 是可委派角色，Skill 是可复用工作流，两者不是同一个概念。
- 原生 Codex 插件 Manifest 当前主要注册 Skills、MCP 和 Hook，并不会自动把全部 68 个角色写入用户的 Codex Agent 配置。
- Codex 实际可用的子代理和并发能力由当前客户端、配置和会话权限决定。
- 不要仅因为 ECC 仓库存在某个 Agent 文件，就声称当前会话一定能调用它。

只有任务能够安全拆成相互独立的子任务时，才值得使用多 Agent。简单修复或单文件修改通常没有委派收益。

### 4. Hooks

Hook 是在特定生命周期事件触发的自动化命令。Hook 可以执行代码，因此应当视为可执行配置，而不是普通文档。

当前 ECC 2.2.0 原生 Codex 插件包含一个经过适配的同步 Hook：

```text
SessionStart
└── session:start
    └── 加载上一会话上下文并检测包管理器
```

安装插件不会静默授权 Hook。首次使用或 Hook 内容 Hash 变化后：

1. 在 Codex 中打开 `/hooks`。
2. 阅读 Hook 定义和执行命令。
3. 明确信任后再启用。

`/plugins` 控制插件启用状态，`/hooks` 控制 Hook 信任状态，两者互相独立。

Claude Code 中的 `off/minimal/standard/strict` 四种 Hook Profile 不适用于 Codex，不要把它们映射到 Codex 配置。

### 5. MCP

当前原生插件默认只声明：

```text
chrome-devtools
```

它通过 Chrome DevTools Protocol 支持浏览器调试、Console/Network 检查和性能分析。其他旧默认 Connector 已在 ECC 的连接器审计中退出默认集合，需要时再单独配置。

使用 MCP 时要注意：

- MCP Server 可以启动本地进程、访问网络或继承环境变量。
- 只启用任务真正需要的 Server。
- 不把 API Key 写进仓库或提示词。
- 外部写操作仍需要明确授权。
- MCP 不工作时先检查 Node.js、`npx`、网络和 Codex MCP 状态。

### 6. Rules

ECC 的 `rules/` 是始终遵循的通用或语言规则包，主要服务于选择性/手动安装。

原生 Codex 插件不会自动把全部 Rules 写入当前项目。Codex 项目的原生长期指令入口是 `AGENTS.md`。不要在安装原生插件后再执行完整同步，仅仅为了复制 Rules；应根据实际需要选择少量规则，或把稳定项目约束写进仓库自己的 `AGENTS.md`。

## 五、安装、升级和重新配置

### 1. 原生安装

当前 Codex 推荐使用 Marketplace 原生插件：

```powershell
codex plugin marketplace add affaan-m/ECC
codex plugin add ecc@ecc
codex plugin list --json
```

安装后重启 Codex，使新 Skills、MCP 和 Hook 定义进入新会话。

以上两个 Add 命令是幂等的；重复执行不会创建第二个安装 Scope。

### 2. 升级

```powershell
codex plugin marketplace upgrade ecc --json
codex plugin add ecc@ecc --json
codex plugin list --json
```

升级后：

1. 重启 Codex。
2. 检查插件版本和 Enabled 状态。
3. 打开 `/hooks`，重新检查 Hash 发生变化的 Hook。
4. 确认常用 Skill 可以被自动补全。

### 3. 在 Codex 内重新配置

推荐提示词：

```text
请使用 ecc:configure-ecc，检查并重新配置当前 Codex 的 ECC 原生插件。
先只读盘点和预览，任何安装或升级操作都先向我确认。
```

`ecc:configure-ecc` 在 Codex 中会使用原生插件生命周期，不会询问 Claude Code 的 `user/project/local` Scope 或四档 Hook Profile。

### 4. 只选择一种安装方式

同一个 Codex Home 只能选择一种 ECC 分发方式：

```text
推荐：Codex 原生 Marketplace 插件
兼容：sync-ecc-to-codex.sh 管理同步
禁止叠加：原生插件 + Managed Sync
```

叠加两种安装方式可能导致：

- Skill 重复。
- 旧文件覆盖新文件。
- MCP 配置漂移。
- Hook 或指令重复。
- 升级与卸载无法确定所有权。

当前 Codex 原生插件没有 Claude Code 的 `user/project/local` 三种 Scope。启用状态保存在当前活动的 `CODEX_HOME` 中。

### 5. 不要修改插件缓存

以下目录属于安装缓存，不应作为自定义入口：

```text
%CODEX_HOME%\plugins\cache\...
```

如果需要自定义长期规则：

- 项目规则放进项目 `AGENTS.md`。
- 自定义 Skill 使用正式 Skill/Plugin 创建流程。
- MCP 配置放进受支持的 Codex 配置位置。
- 不要直接 Patch 缓存中的 `SKILL.md` 或 Manifest。

## 六、如何选择合适的 Skill

### 1. 按工作阶段选择

| 阶段 | 推荐 Skill | 用途 |
|---|---|---|
| 接手代码库 | `ecc:codebase-onboarding` | 识别架构、入口、约定和入门路径 |
| 全仓资产审计 | `ecc:repo-scan` | 文件级分类和第三方资产识别 |
| 产品需求澄清 | `ecc:product-lens` | 从产品价值、角色和范围审视需求 |
| 架构决策 | `ecc:architecture-decision-records` | 记录背景、方案、取舍和后果 |
| 新功能/缺陷 | `ecc:tdd-workflow` | RED-GREEN-REFACTOR 与覆盖验证 |
| API 设计 | `ecc:api-design` | REST 资源、状态码、分页、错误和版本 |
| 安全敏感开发 | `ecc:security-review` | 鉴权、输入、Secret、注入和敏感操作 |
| E2E | `ecc:e2e-testing` | Playwright、Page Object 和 Flaky 治理 |
| 部署 | `ecc:deployment-patterns` | CI/CD、健康检查、回滚和生产准备 |
| Docker | `ecc:docker-patterns` | 镜像、Compose、网络、卷和安全 |
| 完成前验证 | `ecc:verification-loop` | 测试、Lint、类型、构建和证据 |
| 上线审计 | `ecc:production-audit` | 基于本地证据检查生产风险 |
| 文档治理 | `ecc:living-docs-governance` | 防漂移、文档角色和长期维护 |
| 上下文过重 | `ecc:context-budget` | 找出 Skills、Rules、MCP 的上下文开销 |
| 查找新 Skill | `ecc:skill-scout` | 先搜索现有能力，再决定是否新建 |

### 2. 按技术栈选择

| 技术                            | 推荐 Skill                                   |
| ----------------------------- | ------------------------------------------ |
| FastAPI                       | `ecc:fastapi-patterns`                     |
| Vue 3 / Pinia / Vue Router    | `ecc:vue-patterns`                         |
| PostgreSQL / RLS / Index      | `ecc:postgres-patterns`                    |
| Redis / Cache / Lock / PubSub | `ecc:redis-patterns`                       |
| Python                        | `ecc:python-patterns`、`ecc:python-testing` |
| Docker Compose                | `ecc:docker-patterns`                      |
| REST API                      | `ecc:api-design`                           |
| 错误、重试、熔断                      | `ecc:error-handling`                       |
| 可访问性                          | `ecc:accessibility` 或 `ecc:frontend-a11y`  |
| Playwright                    | `ecc:e2e-testing`                          |
| Kubernetes                    | `ecc:kubernetes-patterns`                  |

### 3. 安全相关 Skill 的区别

| Skill | 审查对象 |
|---|---|
| `ecc:security-review` | 应用代码、API、鉴权、输入和敏感业务 |
| `ecc:security-scan` | Agent/Harness 配置，例如指令、MCP、Hook、权限和 Secret 暴露 |
| `ecc:security-bounty-hunter` | 更偏进攻性安全研究与漏洞发现流程 |
| `ecc:safety-guard` | Agent 执行时的安全边界与危险操作防护 |

不要把 `security-scan` 当成普通 Python 依赖扫描器；它主要检查 AI 编程 Harness 配置。

### 4. 查不到 Skill 时

先询问 ECC：

```text
请使用 ecc:skill-scout，在当前可用 Skills 中查找最适合“数据库在线迁移”的工作流。
只列出最匹配的三个，并说明选择理由，不要安装任何东西。
```

也可以直接在 ECC 源码目录搜索：

```powershell
rg -n "migration" skills commands agents docs
```

不要为了一个简单任务先创建新 Skill；只有现有能力确实不适合、流程会重复使用时才值得创建。

## 七、推荐工作流

### 1. 新功能开发

```text
需求澄清
-> 架构/API 决策
-> TDD 失败测试
-> 最小实现
-> 领域模式审查
-> 安全审查
-> Verification Loop
```

示例提示词：

```text
请使用 ecc:tdd-workflow 和 ecc:fastapi-patterns，实现设备列表游标分页。

要求：
1. 先写失败的 API 和数据库集成测试。
2. API 遵循现有 OpenAPI 和 Problem Details 约定。
3. 只修改 devices 模块和相关测试。
4. 完成后运行 Ruff、Pyright 和相关 pytest。
```

功能完成后另开一轮验证：

```text
请使用 ecc:verification-loop 验证刚才的设备列表改动。
检查实现、测试、类型、迁移和生成契约，不修改无关文件。
```

### 2. 缺陷修复

```text
复现
-> 写失败测试
-> 找根因
-> 最小修复
-> 回归测试
-> 检查相邻风险
```

```text
请使用 ecc:tdd-workflow 修复重复 MQTT 消息导致命令状态回退的问题。
必须先补充能够稳定复现问题的失败测试，再修改实现。
不要通过降低断言或删除幂等检查来让测试通过。
```

### 3. 只读代码审查

```text
请使用 ecc:fastapi-patterns、ecc:postgres-patterns 和 ecc:security-review，
只读审查本次设备命令模块改动。

按严重程度输出发现，每条包含文件、行号、影响、证据和建议；
如果没有问题，明确说明检查了哪些风险。不要修改文件。
```

### 4. 上线前检查

```text
请使用 ecc:production-audit 和 ecc:verification-loop，
对当前版本做上线前审计。

覆盖配置、数据库迁移、健康检查、备份、回滚、Secret、观测、测试和容量风险。
先只读审计，不部署、不推送、不修改外部资源。
```

### 5. FastAPI + Vue 项目组合

推荐按任务拆开使用：

```text
后端接口：ecc:fastapi-patterns + ecc:api-design
数据库：ecc:postgres-patterns
Redis：ecc:redis-patterns
前端：ecc:vue-patterns + ecc:accessibility
测试：ecc:tdd-workflow + ecc:e2e-testing
安全：ecc:security-review
交付：ecc:docker-patterns + ecc:deployment-patterns
最终验证：ecc:verification-loop
```

不要一次全部加载。当前任务是 PostgreSQL 索引优化时，只使用 `postgres-patterns` 和验证 Skill；当前任务是 Vue 表单时，只使用 `vue-patterns`、可访问性和相关测试 Skill。

### 6. 文档更新

```text
请使用 ecc:living-docs-governance，审查 docs 的职责划分和交叉引用。
优先复用现有文件，不新建无必要的根级文档；输出建议后再实施获批修改。
```

## 八、如何写出有效的 ECC 请求

### 1. 最小模板

```text
请使用 ecc:<skill-name> 完成 <目标>。
范围：<目录/模块/文件>。
权限：<只读 / 允许修改 / 禁止外部写操作>。
约束：<必须保持不变的接口或行为>。
验证：<测试、Lint、类型检查、构建>。
交付：<回复格式或输出文件>。
```

### 2. 审查模板

```text
请使用 ecc:security-review，只读审查 <范围>。
不要实现修复。
按 Critical/High/Medium/Low 排序；每项给出证据、影响和建议。
重点检查 <鉴权/越权/注入/Secret/审计>。
```

### 3. 实现模板

```text
请使用 ecc:tdd-workflow 和 ecc:<domain-skill> 实现 <功能>。
先建立失败测试，保持 <契约> 向后兼容。
只修改 <范围>；不要修改 <禁止范围>。
完成后运行 <验证命令>，失败则继续修复直到通过或报告真实阻塞。
```

### 4. 研究模板

```text
请使用 ecc:documentation-lookup 查阅 <框架> 当前官方文档，
回答 <问题>，只引用官方/主来源并标注版本。
如果所需 MCP 未配置，说明缺失并使用可用的官方检索能力。
```

### 5. 避免模糊请求

不推荐：

```text
用 ECC 优化项目。
```

推荐：

```text
请使用 ecc:postgres-patterns，只读分析最近 24 小时设备遥测查询的 Schema、索引和 SQL；
不要迁移数据库。输出前三个瓶颈、证据和可回滚优化方案。
```

## 九、安全与权限

### 1. Skill 不等于授权

即使 Skill 建议部署、删除文件、推送代码或调用外部服务，Codex 仍需遵循用户授权、Sandbox 和审批策略。

以下操作应该在提示词中明确授权：

- 删除或覆盖重要数据。
- 推送、合并或创建 Pull Request。
- 修改线上资源。
- 写入第三方服务。
- 使用付费 API。
- 修改凭证、权限或安全策略。
- 执行生产数据库迁移。

只说“使用 ECC”不代表授权以上操作。

### 2. 把 Hook、MCP 和项目指令视为代码

这三类配置可能影响 Agent 行为或执行命令：

```text
Hooks       可在生命周期事件执行程序
MCP Servers 可访问网络、文件或持有凭证
AGENTS.md    会进入 Agent 的长期指令上下文
```

安装或升级后应阅读变更，不要因来源是插件就自动无限信任。

### 3. Secret

- Secret 使用环境变量或正式 Secret 管理器。
- 不写进 `AGENTS.md`、Skill、Prompt、日志或仓库配置。
- MCP 启动进程可能继承环境变量，应限制其可见凭证。
- 分享诊断输出前删除 Token、Cookie、私钥和个人数据。

### 4. 外部行为

默认把网络工具用于读取、搜索和验证。发布内容、发送消息、提交 PR、修改云资源等外部写操作，应由用户明确授权。

## 十、上下文和成本管理

ECC 能力很多，但不意味着所有能力都应同时加载。

降低上下文开销的方法：

1. 每轮只点名当前任务所需技能。
2. 不安装原生插件和 Managed Sync 两套表面。
3. 禁用不使用的 MCP。
4. 稳定项目规则写入简洁的 `AGENTS.md`，不要复制整个 ECC README。
5. 长任务分阶段，每阶段有明确产物与验证。
6. 使用 `ecc:context-budget` 检查 Skills、Rules 和 MCP 的上下文占用。

示例：

```text
请使用 ecc:context-budget，只读审计当前 Codex/ECC 配置的上下文开销。
找出重复 Skills、无用 MCP 和过长指令；先给建议，不修改配置。
```

`ecc:cost-tracking` 依赖 ECC 本地成本日志是否存在。在 Codex 中没有对应数据时，它不能凭空生成准确费用。

## 十一、故障排查

### 1. 插件不可见

检查：

```powershell
codex plugin list --json
```

确认：

- `pluginId` 为 `ecc@ecc`。
- `installed` 为 `true`。
- `enabled` 为 `true`。
- 版本符合预期。

然后重启 Codex。插件是在会话启动时发现的，旧会话不一定刷新全部技能。

### 2. Skill 找不到

依次检查：

1. 使用当前 Codex 的 `$` 自动补全搜索关键字。
2. 使用准确注册名，例如 `ecc:fastapi-patterns`。
3. 确认插件 Enabled。
4. 重启 Codex。
5. 升级 Marketplace Snapshot 并重新 Add 插件。
6. 不要根据旧博客猜 `/tdd`、`/eval` 等退役短命令。

仓库 Catalog 与当前会话可见列表可能因 Harness 过滤、迁移兼容层或版本缓存略有不同；以当前会话可调用列表为最终依据。

### 3. Hook 没运行

1. 打开 `/plugins`，确认 ECC 已启用。
2. 打开 `/hooks`，确认 `session:start` 已审查并信任。
3. Hook 更新后 Hash 会变化，需要重新信任。
4. 重启会话触发 `SessionStart`。
5. 检查 Node.js 是否可用。

不要套用 Claude Code 的 Hook Profile 排障步骤；Codex 使用独立信任机制。

### 4. 技能或配置出现两份

最常见原因是同时使用：

```text
Codex Native Plugin
+ sync-ecc-to-codex.sh
```

处理原则：

1. 用 `codex plugin list --json` 确认原生安装。
2. 检查 `~/.codex` 是否还有 Managed Sync 产生的 Skills/MCP/指令。
3. 先确认文件所有权和安装状态，不要直接递归删除。
4. 选择保留一种方式；当前版本优先保留原生插件。
5. 使用 `/plugins` 执行插件级启用、禁用或移除。

### 5. MCP 启动失败

当前默认 `chrome-devtools` 通过 `npx` 启动。检查：

```powershell
node --version
npx --version
```

还应检查：

- 能否访问 npm Registry。
- Chrome/Chromium 与调试环境是否满足工具要求。
- 代理、防火墙和证书是否阻断下载或连接。
- Codex 是否启用了对应 MCP。

没有浏览器调试需求时，可以不启用该 MCP。

### 6. 安装脚本缺少 Node 依赖

不要在 Codex 不可变插件缓存中随意执行需要完整 `node_modules` 的开发脚本。如果确实需要 ECC 的 Installer、Catalog 维护或源码级诊断：

```powershell
git clone https://github.com/affaan-m/ECC.git
Set-Location ECC
npm install
```

然后在独立源码检出目录运行相关脚本。原生插件的日常安装和升级不需要在缓存中执行 `npm install`。

### 7. Windows 限制

ECC 核心 Node.js 与原生 Codex 插件可以在 Windows 使用，但部分 Shell、持续学习、媒体或编排能力可能仍依赖 Bash、Python、Git Bash 或 WSL。

遇到可移植性问题时：

- 先读取该 Skill 的环境要求。
- 优先使用 PowerShell/Node 原生路径。
- 只有 Skill 明确要求时才进入 WSL/Git Bash。
- 不要把 Linux 删除、路径或权限命令直接复制到 Windows。

## 十二、维护建议

### 每次升级后

- 检查 `codex plugin list --json`。
- 重新阅读发生变化的 Hook。
- 确认默认 MCP 是否变化。
- 搜索常用 Skill 是否仍存在或更名。
- 对关键工作流做一个小型试运行。
- 不把插件内部说明全文复制进项目上下文。

### 每月或出现异常时

- 使用 `ecc:context-budget` 检查上下文开销。
- 使用 `ecc:security-scan` 检查 Agent/Harness 配置安全。
- 检查是否存在重复安装或废弃 MCP。
- 检查 `AGENTS.md` 是否仍准确、精简且不含 Secret。

### 项目开始时

- 使用 `ecc:codebase-onboarding` 获取代码库地图。
- 选择与当前技术栈相关的少量 Skills。
- 把稳定约束写入项目自己的 `AGENTS.md`。
- 确定测试、验证和安全审查流程。
- 不把 ECC 的所有 Rules 和 Skills 一次性复制进项目。

## 十三、快速参考

### 插件命令

```powershell
# 查看状态
codex plugin list --json

# 安装 Marketplace 与插件
codex plugin marketplace add affaan-m/ECC
codex plugin add ecc@ecc

# 升级
codex plugin marketplace upgrade ecc --json
codex plugin add ecc@ecc --json
```

### Codex 内置界面

```text
/plugins  查看、启用、禁用或移除插件
/hooks    审查和信任插件 Hook
```

### 高频技能

```text
ecc:configure-ecc
ecc:codebase-onboarding
ecc:tdd-workflow
ecc:fastapi-patterns
ecc:vue-patterns
ecc:api-design
ecc:postgres-patterns
ecc:redis-patterns
ecc:security-review
ecc:e2e-testing
ecc:docker-patterns
ecc:deployment-patterns
ecc:verification-loop
ecc:production-audit
ecc:living-docs-governance
ecc:context-budget
ecc:skill-scout
```

### 推荐的完整交付链

```text
理解需求
-> 选择 1 个主流程 Skill
-> 选择 1~2 个领域 Skill
-> 明确权限和修改范围
-> 测试/实现
-> 安全或专业审查
-> Verification Loop
-> 以证据交付
```

## 十四、官方参考

- [ECC GitHub 仓库](https://github.com/affaan-m/ECC)
- [ECC 官方网站](https://ecc.tools)
- [ECC Security Policy](https://github.com/affaan-m/ECC/blob/main/SECURITY.md)
- [ECC Codex Navigation Guide](https://github.com/affaan-m/ECC/blob/main/docs/CODEX-NAVIGATION-GUIDE.md)
- [Codex Plugins 文档](https://learn.chatgpt.com/docs/plugins)
- [Codex Skills & Plugins 文档](https://learn.chatgpt.com/docs/skills-and-plugins)
- [Codex Hooks 文档](https://learn.chatgpt.com/docs/hooks)
- [Codex 配置参考](https://developers.openai.com/codex/config-reference)

使用 ECC 时，最稳妥的习惯是：**精确点名技能、限定任务范围、明确是否允许修改，并在完成前要求可复现的验证证据。**

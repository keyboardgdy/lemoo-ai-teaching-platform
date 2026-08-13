# W2 仓库与工具链证据

> 工作包：W2 建立仓库与工具链
>
> 执行日期：2026-08-13
>
> 执行人：OpenAI Codex
>
> 最终责任人：高端阳
>
> 范围：Stage 1A、Simulator-only、合成数据、非生产

## 结论

Windows 本地 W2 骨架与验证，以及 PR #1 的 Linux 五项 CI 均已通过。仓库只包含空业务 FastAPI/Vue 骨架、契约与 Simulator 目录占位、本地开发依赖和最小 CI；Content、Teaching、AI、OTA、真实设备、真实机构数据和生产路径均保持禁用或未实现。

远端采用私有仓库 `keyboardgdy/lemoo-ai-teaching-platform`。账户中已存在的 `keyboardgdy/Lemoo` 是公开 C# `Lemoo.UI` 项目，具有不相容历史，因此未覆盖、未强推、未修改。

W2 当前状态为 `blocked_branch_protection`：GitHub REST API 对私有 `main` 返回 HTTP 403，要求升级 GitHub Pro 或公开仓库。项目保持私有，不用扩大可见性绕过门禁；在套餐升级并启用保护，或高端阳书面批准有期限的例外前，不把 W2 标为完成，也不进入依赖 W2 的后续工作包。

## 基线与版本

| 项目 | 结果 |
|---|---|
| 治理基线 Commit | `6340df2 docs: establish Stage 1A governance baseline` |
| 工作分支 | `prep/w2-repo-toolchain` |
| Git | 2.51.0.windows.1 |
| uv / 项目 Python | 0.12.2 / 3.14.7 |
| Node.js / pnpm | 24.11.1 / 11.2.2 |
| Task | 3.46.4 |
| Docker / Compose | 29.1.3 / 5.0.1 |
| Gitleaks / Trivy | 8.30.1 / 0.73.0 |

主机默认 `python` 仍是 3.12.10；项目所有 Python 命令均经 uv 使用 3.14.7，不依赖主机默认解释器。

## 可重复验证

在 Windows 工作区执行：

```text
task bootstrap
task verify
uv run --project apps/cloud pre-commit run --all-files
uv run --project apps/cloud pip-audit --progress-spinner off
pnpm audit --audit-level moderate
gitleaks git . --redact --no-banner --log-level warn
git diff --cached --binary | gitleaks stdin --redact --no-banner --log-level warn
trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 --skip-dirs apps/cloud/.venv --skip-dirs node_modules --skip-dirs apps/web/dist --skip-dirs apps/web/coverage --skip-dirs docs/.obsidian .
task infra:up
docker compose ps
```

## 验证结果

| 检查 | 结果 |
|---|---|
| `task bootstrap` | PASS；锁定依赖安装成功，`.env` 仅由 `.env.example` 生成且保持未跟踪 |
| Ruff / ESLint / Prettier | PASS |
| Pyright strict / Vue TypeScript | PASS；Python 0 error、0 warning |
| Pytest | PASS；7/7，覆盖率 95.71%，门槛 90% |
| Vitest | PASS；1/1，目标组件覆盖率 100% |
| Python wheel/sdist / Vite build | PASS |
| 文档 / 仓库边界 / Schema 占位 / Compose config | PASS；文档 33 份、仓库跟踪文件 97 份 |
| pre-commit | PASS；JSON/TOML/YAML、冲突、私钥、换行、空白、Ruff、Prettier 全部通过 |
| pip-audit | PASS；已知漏洞 0；本地包 `lemoo-cloud` 因非 PyPI 包按预期跳过 |
| pnpm audit | PASS；已知漏洞 0 |
| Gitleaks | PASS；治理历史和 W2 暂存差异均未发现 Secret |
| Trivy fs | PASS；`uv.lock` 与 `pnpm-lock.yaml` 高危/严重漏洞 0，Secret/Misconfiguration 无命中 |
| Core Compose | PASS；PostgreSQL 18.3、Redis 8.2.1、MinIO、EMQX 5.8.8 均为 `healthy` |
| PR #1 Linux CI | PASS；Commit `454c7ae`、run `31679934413` 的 `governance/backend/frontend/compose/security` 5/5 通过 |

## 安全与范围说明

- `.env`、虚拟环境、依赖目录、构建物、覆盖率结果和 Obsidian 本机配置均不进入版本控制。
- Compose 端口只绑定 `127.0.0.1`；MQTT 1883 不发布到宿主机，EMQX 匿名访问关闭。
- 示例凭据只用于本机非生产环境，不是随机生产 Secret，也不可复用到任何共享或生产环境。
- OpenAPI 只暴露健康/状态接口；未来业务进程由 Fail Closed 配置和测试保持关闭。
- 本证据不是 G2-Device、Gate 3-Sim、HIL、真实机构试点或生产批准。

## 远端结果

- 仓库：`keyboardgdy/lemoo-ai-teaching-platform`（Private）
- W2 PR：`https://github.com/keyboardgdy/lemoo-ai-teaching-platform/pull/1`
- Linux CI：PASS，Commit `454c7ae`、run `31679934413`，五项检查全绿且无 Node 20 弃用警告
- `main` 分支保护：BLOCKED；2026-08-13 API 返回 HTTP 403：`Upgrade to GitHub Pro or make this repository public to enable this feature.`
- 推荐处置：保持 Private，升级 GitHub Pro 后启用 `governance/backend/frontend/compose/security` Required Checks、PR、线性历史、禁止强推/删除和对话解决

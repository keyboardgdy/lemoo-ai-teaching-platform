# W7b3 证据：供应链、镜像与签名门禁

日期：2026-08-14；范围：Stage 1A Simulator-only、合成数据、非生产。

## 交付

- API 与 Web 使用多阶段 Dockerfile；所有 `FROM` 均固定到 SHA-256 摘要，运行时均为
  `10001:10001` 非 root 用户并声明健康检查。
- API 运行时不保留无需使用的 `pip`，避免其 vendored `msgpack` 与 `setuptools` 扩大攻击面；
  Python 生产依赖只从锁文件安装。
- Web 使用固定摘要的 Node 构建前端；Caddy 由固定摘要的 Go 1.26.6 构建器和锁定的 Go module
  图编译，再复制到最小 Alpine 运行时。该构建消除了官方 Caddy 镜像和 Go 1.26.5 中已存在修复的
  HIGH 漏洞。
- `task supply-chain:audit` 独立审计 Python 锁文件和 pnpm 生产依赖；
  `task image:verify` 生成并验证完整证据。
- 每张镜像生成 Docker archive、CycloneDX JSON SBOM、Trivy JSON 扫描结果和 SLSA v1/in-toto
  provenance。不可变镜像摘要来自 BuildKit `containerimage.digest`，并与 descriptor、Docker
  元数据、OCI revision label 和归档 SHA-256 交叉验证。
- 所有镜像归档、SBOM、扫描报告、provenance、哈希清单及总报告均由当次运行生成的 Cosign
  测试密钥离线签名。门禁结束前删除两个私钥，仅保留公钥和 bundle 作为可复核证据。
- 负向验证明确证明篡改 artifact、错误公钥和可变标签均被拒绝。
- CI 把生成与验证拆为稳定独立结果：`dependency-audit`、`supply-chain-artifacts`、
  `immutable-image`、`sbom`、`image-scan`、`provenance` 和 `artifact-signature`。后五项从上传的
  同一份证据重新验证，避免生成脚本单方面自证。

## TDD 与失败证据

- RED Commit `a0610d8`：先冻结 8 项不可变引用、SLSA subject、哈希篡改及 Dockerfile pin/non-root
  策略测试，因实现模块不存在而在收集阶段失败。
- GREEN Commit `2cad3ec`：加入镜像、SBOM、Trivy、SLSA 和 Cosign 端到端实现；依赖审计先发现
  `cryptography 46.0.7` 的已修复漏洞，升级至 50.0.0 后为 0。
- CI Commit `45cd606`：增加五个独立证据验证器和七项 CI 结果；11 项供应链单元测试通过。
- [失败运行 31771924850](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/actions/runs/31771924850)
  证明 Linux `docker-container` Buildx 不允许把带证明附件的 manifest list 通过 `--load` 导入。
  Commit `473be0f` 改为单平台 manifest，并由独立 SLSA 文件承载签名溯源；BuildKit digest 仍被
  fail closed 校验。
- [失败运行 31772259177](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/actions/runs/31772259177)
  使用最新 Trivy 数据库发现 Go 1.26.5 标准库的 `CVE-2026-39821` 与 `CVE-2026-46600`；
  Commit `19439fe` 升级到发布于当日、固定摘要的 Go 1.26.6。使用同一最新数据库重新扫描后
  Alpine 与 Caddy Go binary 均为 0。

## 本地验证

- Ruff format/check：PASS。
- Pyright：PASS，0 error / 0 warning。
- 供应链策略与独立证据测试：11 passed。
- `task supply-chain:audit`：Python 与 pnpm 均无已知漏洞。
- `task image:verify`：2 张镜像、2 份 CycloneDX、2 份 Trivy 报告、2 份 SLSA v1 provenance、
  10 个签名对象和 3 个负向用例全部通过；输出目录不存在私钥。
- API `/health/live` 与 Web `/healthz` 实际容器 smoke：PASS；二者运行用户均为 `10001:10001`。
- 使用最新独立 Trivy 缓存扫描：API Debian/Python 0；Web Alpine/Caddy Go binary 0。

## PR CI 证据

[W7b3 GitHub Actions run 31772780566](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/actions/runs/31772780566)
在 PR #20 的 Linux runner 上通过全部 7 项 W7b3 检查；证据生成 job 无本地缓存完成两张镜像构建、
扫描、SBOM、SLSA 和签名，五个下游 job 成功下载并独立复核证据。

[W2 GitHub Actions run 31772780556](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/actions/runs/31772780556)
同时通过 `backend`、`frontend`、`governance`、`security`、`compose` 与 `e2e`，证明供应链变更未破坏
现有质量、真实 Compose/mTLS 或浏览器验收基线。

## 边界

Cosign 身份是每次运行临时生成、运行后销毁私钥且未接入透明日志的测试身份，只用于 Stage 1A
门禁演练；它不是生产发布签名、生产身份或生产授权。W7b3 不启用真实设备、真实机构、个人数据、
外部 Provider、内容、教学、AI、诊断、批量命令、OTA 或生产部署。

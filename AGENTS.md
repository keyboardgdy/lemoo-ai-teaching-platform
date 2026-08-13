# AGENTS.md

## Authority

Read these before changing behavior:

1. `docs/product/PRD-001 教育机器人云平台.md`
2. `docs/product/RTM-001 教育机器人云平台需求追踪矩阵.md`
3. `docs/04 开发前准备与启动门禁.md`
4. `docs/01 fastapi-vue-modern-tech-stack.md`
5. `docs/02 fastapi-vue-modern-architecture.md`

## Current scope

- Stage 1A is simulator-only, synthetic-only, non-production.
- Real devices, real institutions, personal data and production remain blocked.
- Content, teaching, AI, diagnostics and OTA remain disabled until their gates pass.
- OpenAI Codex is the execution agent; 高端阳 is the temporary accountable owner for Stage 1A.

## Implementation rules

- Keep entrypoints thin; domain code cannot import FastAPI, SQLAlchemy, Redis, MQTT or provider SDKs.
- Cross-module synchronous calls go through `public.py`; cross-boundary payloads use versioned schemas.
- Do not add a second Python or pnpm lockfile.
- Do not use SQLite as a PostgreSQL test substitute.
- No ORM objects cross API, MQTT, WebSocket or job boundaries.
- No secrets, private keys, firmware, media, logs or database dumps in Git.
- Never weaken or skip checks to make CI pass.
- Update PRD/RTM/contracts/tests/evidence together when behavior changes.

## Verification

Run `task verify` for W2 changes. Gate-specific tasks intentionally fail until the named prerequisite work package is complete.

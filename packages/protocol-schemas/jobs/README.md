# Stage 1A core Job contracts

Status: `frozen` for `stage-1a-simulator-first`.

This directory is the authoritative boundary for recoverable Stage 1A Jobs, Outbox events, progress/results/errors, and the `refresh_shadow` command state machine. Delivery is at least once; all business effects are idempotent by stable Job, Event, or Command ID.

Only the three Job types in `job-catalog.v1.json` may execute. Unknown types and all Content, Teaching, AI, Diagnostics and OTA prefixes go to Dead Letter without execution. Payloads contain stable IDs and bounded parameters, never ORM objects, files, prompts, credentials or personal data.

Run `task test:protocol` to validate schemas, accepted/rejected/backward fixtures, retry classification, cancellation, timeout and state transitions.

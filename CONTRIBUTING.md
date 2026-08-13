# Contributing

## Workflow

1. Start from protected `main` after the remote repository is configured.
2. Use `prep/w<id>-<slug>` for preparation work and `feature/<requirement-id>-<slug>` for product behavior.
3. Link every behavior change to a PRD Requirement, Acceptance and planned evidence.
4. Run `task bootstrap` once and `task verify` before opening a pull request.
5. Keep documentation, contracts, implementation and tests in the same pull request.

Direct pushes, force pushes and history rewriting on `main` are prohibited after remote protection is active. Do not approve your own high-risk production change.

## Commits

Use concise conventional subjects such as `chore: establish W2 toolchain` or `feat(PRD-DEV-001): add device identity contract`. Do not include secrets, customer names, student data or generated local credentials in commit messages.

## Pull requests

The pull request must state scope, non-goals, risks, rollback, Requirement/Acceptance IDs and exact verification commands. Red CI is a blocker, not an optional signal.

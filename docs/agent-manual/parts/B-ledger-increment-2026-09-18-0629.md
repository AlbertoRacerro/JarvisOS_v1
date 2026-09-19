# Area B explicit file-coverage increment — 2026-09-18 06:29 CEST

MAPPING_STATUS: IN_PROGRESS

This increment is B-only evidence for later consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union coverage or `UNACCOUNTED_FILES: 0`.

Fresh-start evidence: remote `master` was inspected at commit `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; PR #660/branch state was inspected before this increment. No backend-A rows are added here.

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/main.tsx` | READ | Directly inspected. React bootstrap: applies stored visual preferences before render, imports the ordered global/operator CSS stack, then mounts `App` under `React.StrictMode`. Import order is behaviorally significant because later override sheets can supersede earlier tokens/foundation/shell rules. |
| `frontend/src/operatorSemantics.ts` | READ | Directly inspected. Pure operator-facing semantic adapters for runtime delta/alignment, PR check/review summaries, provider execution location, paid-AI budget wording, and credential-state wording. Unknown runtime alignment deliberately suppresses delta/file details instead of presenting potentially stale/ambiguous evidence as canonical. |
| `frontend/src/vite-env.d.ts` | READ | Directly inspected tiny file. Single Vite client type-reference directive; compile-time ambient typing only, no runtime/operator behavior. |

Remaining work: continue literal recursive B-owned tree inspection and consolidate all durable increments into the canonical ledger. `MAPPING_STATUS` must remain `IN_PROGRESS` until a fresh tracked-tree reconciliation proves every B-owned file has exactly one explicit row.

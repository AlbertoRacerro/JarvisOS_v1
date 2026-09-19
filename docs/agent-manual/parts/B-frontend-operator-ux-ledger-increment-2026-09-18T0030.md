# Area B explicit file coverage increment — 2026-09-18 00:30 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This is durable Area-B-only evidence to be consolidated into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not make the stale canonical `MAPPING_STATUS: COMPLETE` authoritative and does not assert `UNACCOUNTED_FILES: 0`.

Fresh run baseline: PR #660 head before this commit was `3f1160c02e18d7ed9f2068aa37e20efcbaca9eea`. The recursive tracked tree and `frontend/src/api/` directory were re-read before inspection. No backend-A rows are added here.

## EXPLICIT FILE COVERAGE LEDGER — increment

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/api/memory.ts` | READ | Directly inspected. Typed Memory proposal/lifecycle client for assumptions, parameters and decisions: lists proposals with optional status filter; POSTs promote/reject and parameter replacement promotion. It bounds server error detail to 400 characters. Mutation calls carry record identity but no expected revision/timestamp, AbortSignal, or workspace in the mutation body; concurrency/authorization remains backend authority and stale-response rejection must be handled by consumers. |
| `frontend/src/api/parameterLifecycle.ts` | READ | Directly inspected. Canonical parameter read/edit/lifecycle client. PATCH edits send `workspace_id` plus `expected_updated_at`; lifecycle POST additionally sends `expected_lifecycle_state`, providing explicit optimistic-concurrency preconditions. Supports activate/deactivate/archive/delete and structured API error code/message projection. No AbortSignal support; consumer still owns superseded-request handling. |
| `frontend/src/api/knowledgeActions.ts` | READ | Directly inspected. Bounded Jarvis Memory context/proposal client: previews stable refs into backend-issued exact refs/context digest, then proposes against `expected_context_digest`. Explicit refused states are converted to errors rather than treated as current/proposed. It exposes proposal/context authority only—no commit mutation—and has no AbortSignal support. |

## Failure-mode notes

- `memory.ts` lifecycle mutations do not expose an optimistic revision parameter, so the frontend wrapper itself cannot prevent acting on a stale record snapshot; do not infer conflict safety from this client.
- `parameterLifecycle.ts` does carry timestamp/state preconditions, so consumers should preserve those canonical values rather than reconstructing lifecycle requests.
- `knowledgeActions.ts` correctly binds proposal generation to the preview digest, but late async responses can still be visually stale unless the consuming component identity/generation-guards them.

## Completion guard

`MAPPING_STATUS: IN_PROGRESS` remains mandatory. A fresh recursive reconciliation of the entire tracked `frontend/` tree plus canonical operator design-reference files/assets has not yet proved that every owned file has exactly one canonical ledger row. Literal `UNACCOUNTED_FILES: 0` is therefore not asserted.

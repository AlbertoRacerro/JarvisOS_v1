# A+B explicit file coverage ledger — durable progress

MAPPING_STATUS: IN_PROGRESS

This sidecar is durable literal-read progress for issue #656 while the canonical ledger is being consolidated into `B-frontend-operator-ux.md`. A row marked `READ` means the file contents were directly opened/inspected; no status is inferred from path or capability-level knowledge.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | one-line role/reason |
|---|---|---|
| `backend/app/modules/ai/sensitivity.py` | READ | Provider-free sensitivity policy: labels source snapshots, prevents in-place S2-S4 downgrades, manages provenance-bound sanitized derivatives, and builds bounded external-eligible context; deterministic secret/IP/confidential floors are lower bounds, never egress permission. |
| `backend/app/modules/ai/sensitivity_models.py` | READ | Strict Pydantic contracts for S0-S4 labels, S0-S2 derivatives, normalized source refs, bounded transformations/content, and automatic/manual context-preview requests/responses. |
| `backend/app/modules/ai/sensitivity_routes.py` | READ | `/ai/sensitivity` HTTP boundary for labels, derivative create/read/revalidate/approve/revoke, and context previews with explicit 404/409/422 failure mapping. |
| `backend/app/modules/ai/thread_models.py` | READ | AI-thread API contracts: bounded IDs/prompts/routes/tokens, paired context+digest and Jarvis-context+digest invariants, persistence states, and bounded interaction/proposal projections. |
| `backend/app/modules/ai/thread_routes.py` | READ | `/threads` HTTP boundary for create/list/read/submit with bounded query limits and explicit not-found/conflict/validation status mapping. |
| `backend/app/modules/ai/thread_service.py` | READ | Durable AI-thread orchestration: request-digest idempotency, server rebuild/digest checks for context, local-only exact Jarvis refs, transactional reservation before dispatch, flow reuse, bounded assistant capture, and capture-failure persistence. |

## Capability facts absorbed from former Area A in this increment

- Sensitivity classification is fail-closed: deterministic pattern matches can raise the effective floor to S2/S3/S4, but cannot themselves authorize external egress. S2-S4 source labels cannot be downgraded in place; external use requires a reviewed derivative/current source binding.
- Sanitized derivatives are source-digest-bound records with explicit draft/approved/revoked/stale lifecycle. Approval rechecks source freshness and deterministic floors; stale source state blocks approval rather than silently reusing old clearance.
- AI-thread submit idempotency binds `request_id` to a canonical request digest. Reusing the same ID with different semantics is a conflict; a duplicate with identical semantics returns the existing durable interaction instead of spending twice.
- Thread context is rebuilt server-side immediately before reservation and compared to the expected digest. Exact-ref Jarvis context is rejected for non-local routes, and dispatchable Jarvis previews must still match the inspected digest.
- A thread interaction is transactionally reserved with an `ai_flow` before provider execution and transitions through `reserved -> dispatching -> captured/capture_failed`; assistant text is bounded on persistence, so durable thread capture is not confused with provider execution success.

## Remaining coverage

Literal A+B completion is not yet proven. The fresh recursive branch tree must still be reconciled against the canonical ledger for all owned backend app/core/api/schema files and modules, their non-engineering tests/configs/helpers/fixtures, the complete `frontend/` tree, and `docs/design-references/`. The next consolidation step must move these rows into `B-frontend-operator-ux.md`, continue direct reads, and compute the exact unaccounted count from a fresh recursive tree.

UNACCOUNTED_FILES: NOT_YET_ZERO

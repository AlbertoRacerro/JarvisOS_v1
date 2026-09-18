# Area D — Development / delivery / GitHub / security / operations

MAPPING_STATUS: IN_PROGRESS

Evidence baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Runtime/scripts/workflows/tests are primary evidence; prose is secondary. `READ` below means actual source-content inspection, not filename discovery.

## EXPLICIT FILE COVERAGE LEDGER

| Path | Status | Role / reason |
|---|---|---|
| `scripts/check_lineage_overview.py` | READ | Deterministic LINEAGE-OVERVIEW-1 conformance checker; exact request-generation stale guards, deterministic topological ordering with cyclic/null fallback, bounded lineage→selection mapping, workspace-discovery stale guard, mutation/fake-authority rejection and canonical spec-087 lifecycle validation. |
| `scripts/check_analytics_dock.py` | READ | Deterministic analytics dock conformance checker. |
| `scripts/check_engineering_data.py` | READ | Deterministic engineering-data conformance checker. |
| `scripts/check_app_shell.py` | READ | Deterministic app-shell conformance checker. |
| `scripts/check_model_inspection.py` | READ | Deterministic model-inspection conformance checker. |
| `scripts/check_operator_workbench.py` | READ | Deterministic operator-workbench conformance checker; verifies sidecar identity, compact tabs, bounded panes and technical-detail disclosure. |
| `scripts/check_runs_workbench.py` | READ | Deterministic runs-workbench conformance checker; verifies typed run/log/artifact reads, stale-response guards, bounded payload projection and negative mutation/authority checks. |
| `scripts/check_settings_surface.py` | READ | Deterministic settings-surface conformance checker; verifies frozen scope, credential non-disclosure, mutation locks, canonical endpoints and bounded error projection. |
| `scripts/check_ai_threads.py` | READ | Deterministic AI-THREADS-0 conformance checker; freezes PR scope, flow/idempotency authority, thread-history egress/privacy boundaries, stale ownership and unsafe-rendering prohibitions. |
| `scripts/check_jarvis_sidecar.py` | READ | Deterministic JARVIS-SIDECAR-1 conformance checker; freezes bounded context/digest authority, server-owned context rebuild, stale preview/submit ownership, credential-safe canonical execution projection and unsafe-rendering prohibitions. |
| `scripts/check_architecture_enforcement.py` | READ | Deterministic architecture-enforcement checker; validates exact exception targets and AE001-AE004 boundaries including mutation ownership, external-network call surfaces, protected-table writes and pinned delivery artifacts. |
| `scripts/check_bluecad_read_model.py` | READ | Deterministic BLUECAD read-model readiness checker; enforces exact changed-file scope, query-only aggregate contract, typed/encoded frontend client, canonical registry evidence and no premature UI consumption. |
| `scripts/check_bluecad_workbench.py` | READ | Deterministic BLUECAD workbench readiness checker; enforces bounded UI scope, aggregate/state authority, stale async guards, resource cleanup, accessibility and forbidden backend/dependency/workflow/schema changes. |
| `scripts/check_ai_advisory_governance.py` | READ | Deterministic AI-advisory governance checker; validates policy vocabulary/enforcement across advisory/provider/LLM surfaces, including provider allow-list/egress and budget gates, sensitive-data handling, redaction/confirmation requirements and fail-closed behavior. Model output remains advisory rather than authoritative. |
| `scripts/check_pr_attention_integration.py` | READ | Deterministic read-only PR-attention integration guard; requires pull_request rather than pull_request_target, explicit read-only permissions, immutable action pin and exact head binding, while rejecting semantic-authority inputs and downstream mutation-capable actions/commands. |
| `scripts/check_proposal_review.py` | READ | Deterministic proposal-review readiness checker; enforces bounded implementation diff, canonical proposal/promote/reject routes, stale request/mutation guards, inert rendering and prohibition of provider/grading/client authority. |

### Ledger continuity

Branch history contains the earlier exact READ evidence for root files, `.github/**`, workflows, delivery/review/CI/continuation/codegen/recovery scripts, `docs/RUNBOOKS.md`, and data-root recovery files. This checkpoint deepens the already-credited lineage checker from direct master source inspection; referenced frontend/docs paths remain uncredited by that checker read.

### Remaining coverage

- Continue literal source reads for remaining D-owned `scripts/**`, governance/docs/config/test surfaces from the exact 2036-file master set.
- Reconcile latest A #658, B #660, C #659 and D #657 exact ledgers mechanically; historical backend A+B temporary rows on B remain excluded.
- Keep `GLOBAL_FILE_COVERAGE: IN_PROGRESS` until exact union counters, duplicate/ambiguous sets and literal orphan queues satisfy the 2036-file invariant.

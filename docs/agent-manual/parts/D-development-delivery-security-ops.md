# Area D — Development / delivery / GitHub / security / operations

MAPPING_STATUS: IN_PROGRESS

Evidence baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Runtime/scripts/workflows/tests are primary evidence; prose is secondary. `READ` below means actual source-content inspection, not filename discovery.

## EXPLICIT FILE COVERAGE LEDGER

| Path | Status | Role / reason |
|---|---|---|
| `scripts/cheap_review.py` | READ | Tiered advisory PR-review orchestrator; bounded evidence packs, provider retry/stream parsing and non-authoritative model verdicts. |
| `scripts/check_lineage_overview.py` | READ | Deterministic LINEAGE-OVERVIEW-1 conformance checker. |
| `scripts/check_analytics_dock.py` | READ | Deterministic analytics dock conformance checker. |
| `scripts/check_engineering_data.py` | READ | Deterministic engineering-data conformance checker. |
| `scripts/check_app_shell.py` | READ | Deterministic app-shell conformance checker. |
| `scripts/check_model_inspection.py` | READ | Deterministic model-inspection conformance checker. |
| `scripts/check_operator_workbench.py` | READ | Deterministic operator-workbench conformance checker. |
| `scripts/check_runs_workbench.py` | READ | Deterministic runs-workbench conformance checker. |
| `scripts/check_settings_surface.py` | READ | Deterministic settings-surface conformance checker. |
| `scripts/check_ai_threads.py` | READ | Deterministic AI-THREADS-0 conformance checker. |
| `scripts/check_jarvis_sidecar.py` | READ | Deterministic JARVIS-SIDECAR-1 conformance checker. |
| `scripts/check_architecture_enforcement.py` | READ | Deterministic architecture-enforcement checker. |
| `scripts/check_bluecad_read_model.py` | READ | Deterministic BLUECAD read-model readiness checker. |
| `scripts/check_bluecad_workbench.py` | READ | Deterministic BLUECAD workbench readiness checker. |
| `scripts/check_ai_advisory_governance.py` | READ | Deterministic AI-advisory governance checker. |
| `scripts/check_pr_attention_integration.py` | READ | Deterministic read-only PR-attention integration guard. |
| `scripts/check_proposal_review.py` | READ | Deterministic proposal-review readiness checker. |
| `scripts/check_review_secret_boundary.py` | READ | Deterministic provider-secret review boundary guard. |
| `scripts/check_spec_status.py` | READ | Deterministic canonical spec-registry/PR consistency gate. |
| `scripts/check_typecheck_ratchet.py` | READ | Fail-closed per-file backend mypy-debt ratchet. |
| `scripts/check_ui_foundation.py` | READ | Deterministic UI-foundation/spec-070 checker. |
| `scripts/classify_ci_scope.py` | READ | Deterministic CI scope classifier. |
| `scripts/cloud_delivery_bridge.py` | READ | Exact-head durable patch bridge with untrusted-input validation and guarded push. |
| `scripts/codex_pr_autopush.py` | READ | Bounded Codex PR autopush actuator using shared guarded delivery. |
| `scripts/codex_result_delivery_dispatch.py` | READ | Authority-free dispatcher for eligible Codex result comments. |
| `scripts/daily_development_continuation.py` | READ | Deterministic spec-079 continuation control plane. |
| `scripts/event_bound_continuation_plan.py` | READ | Exact-front E1 continuation adapter. |
| `scripts/event_driven_continuation.py` | READ | Fail-closed E1 workflow-run wake bridge. |
| `scripts/generate_frontend_contracts.py` | READ | Bounded backend-to-TypeScript contract generator for spec 133. |
| `scripts/init-database.ps1` | READ | Local database/bootstrap launcher; creates/verifies backend venv, installs requirements, sets PYTHONPATH and invokes bootstrap. Referenced backend files are not transitively credited. |
| `scripts/jarvis_silent_start.vbs` | READ | Windows silent launcher. Derives repo/backend paths from its own location, probes `http://127.0.0.1:8000/`, launches backend via `.venv\\Scripts\\pythonw.exe -m uvicorn app.main:app` with `JARVISOS_MANAGE_OLLAMA=1` only when not already responding, redirects output to `C:\\JarvisOS\\jarvis.log`, polls readiness for about 40 seconds, then opens the UI. Referenced backend/runtime components are not transitively credited. |

### Ledger continuity

Branch history contains earlier exact READ evidence for root files, `.github/**`, workflows, delivery/review/CI/continuation/codegen/recovery scripts, `docs/RUNBOOKS.md`, and data-root recovery files. This checkpoint adds direct master-source evidence for `scripts/jarvis_silent_start.vbs`; referenced backend/runtime files are not newly credited by this read.

### Remaining coverage

- Continue literal source reads for remaining D-owned `scripts/**`, governance/docs/config/test surfaces from the exact 2036-file master set.
- Reconcile latest A #658, B #660, C #659 and D #657 exact ledgers mechanically; historical backend A+B temporary rows on B remain excluded.
- Keep `GLOBAL_FILE_COVERAGE: IN_PROGRESS` until exact union counters, duplicate/ambiguous sets and literal orphan queues satisfy the 2036-file invariant.

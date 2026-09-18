# Area D — Development / delivery / GitHub / security / operations

MAPPING_STATUS: IN_PROGRESS

Evidence baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Runtime/scripts/workflows/tests are primary evidence; prose is secondary. `READ` below means actual source-content inspection, not filename discovery.

## EXPLICIT FILE COVERAGE LEDGER

| Path | Status | Role / reason |
|---|---|---|
| `scripts/check_lineage_overview.py` | READ | Deterministic lineage overview conformance checker. |
| `scripts/check_analytics_dock.py` | READ | Deterministic analytics dock conformance checker. |
| `scripts/check_engineering_data.py` | READ | Deterministic engineering-data conformance checker. |
| `scripts/check_app_shell.py` | READ | Deterministic app-shell conformance checker. |
| `scripts/check_model_inspection.py` | READ | Deterministic model-inspection conformance checker. |
| `scripts/check_operator_workbench.py` | READ | Deterministic operator-workbench conformance checker; verifies sidecar identity, compact tabs, bounded panes and technical-detail disclosure. |
| `scripts/check_runs_workbench.py` | READ | Deterministic runs-workbench conformance checker; verifies typed run/log/artifact reads, stale-response guards, bounded payload projection and negative mutation/authority checks. |
| `scripts/check_settings_surface.py` | READ | Deterministic settings-surface conformance checker; verifies frozen scope, credential non-disclosure, mutation locks, canonical endpoints and bounded error projection. |

### Ledger continuity

Branch history contains the earlier exact READ evidence for root files, `.github/**`, workflows, delivery/review/CI/continuation/codegen/recovery scripts, `docs/RUNBOOKS.md`, and data-root recovery files. This checkpoint adds three directly inspected checker paths without inferring unread paths from directory membership.

### Remaining coverage

- Continue literal source reads for remaining D-owned `scripts/**`, governance/docs/config/test surfaces from the exact 2036-file master set.
- Reconcile latest A #658, B #660, C #659 and D #657 exact ledgers mechanically; historical backend A+B temporary rows on B remain excluded.
- Keep `GLOBAL_FILE_COVERAGE: IN_PROGRESS` until exact union counters, duplicate/ambiguous sets and literal orphan queues satisfy the 2036-file invariant.

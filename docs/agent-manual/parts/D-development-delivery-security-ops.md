# Area D — Development / delivery / GitHub / security / operations

MAPPING_STATUS: IN_PROGRESS

Evidence baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Runtime/scripts/workflows/tests are primary evidence; prose is secondary. `READ` below means actual source-content inspection, not filename discovery.

## EXPLICIT FILE COVERAGE LEDGER

This ledger preserves the previously committed Area-D READ evidence. The following newly reconciled exact paths are additionally credited after direct source inspection at the baseline SHA:

| Path | Status | Role / reason |
|---|---|---|
| `scripts/check_lineage_overview.py` | READ | Deterministic LINEAGE-OVERVIEW-1 conformance checker over frontend lineage/workspace state plus STATUS lifecycle evidence; includes stale-response, ordering, selection-boundary and fake-authority negative checks. |
| `scripts/check_analytics_dock.py` | READ | Deterministic ANALYTICS-DOCK-1 conformance checker; verifies bounded run/output selection, exact model-version/unit comparability, stale-response guards, and rejects conversion/statistical/fake-authority behavior. |
| `scripts/check_engineering_data.py` | READ | Deterministic ENGINEERING-DATA-1 conformance checker; verifies typed engineering-record projection/filtering, workspace-generation guards, partial-failure behavior, and rejects mutation/fake freshness-authority behavior. |

### Ledger continuity

The branch history before this commit contains the existing 79 exact READ rows for root files, `.github/**`, workflows, delivery/review/CI/continuation/codegen/recovery scripts, `docs/RUNBOOKS.md`, and data-root recovery files. This commit does not revoke those rows; it adds the two directly inspected checker paths above while preserving `scripts/check_lineage_overview.py`. Global audit must parse canonical branch history/current ledger evidence conservatively and must not infer unread paths from directory membership.

### Remaining coverage

- Continue literal source reads for remaining D-owned `scripts/**`, governance/docs/config/test surfaces from the exact 2036-file master set.
- Reconcile latest A #658, B #660, C #659 and D #657 exact ledgers mechanically; historical backend A+B temporary rows on B remain excluded.
- Keep `GLOBAL_FILE_COVERAGE: IN_PROGRESS` until exact union counters, duplicate/ambiguous sets and literal orphan queues satisfy the 2036-file invariant.

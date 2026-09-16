# JarvisOS agent manual — strict file coverage audit

GLOBAL_FILE_COVERAGE: IN_PROGRESS

Fresh master baseline: `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

This audit is fail-closed. `READ` is credited only where an active owner ledger establishes actual content inspection; capability prose, directory discovery, or filename mention does not count.

## Active owner set

- **A+B:** PR #660 / `docs/capability-map-B-frontend-ux`.
- **C:** PR #659 / `docs/capability-map-C-engineering`.
- **D:** PR #657 / `docs/capability-map-D-devops-security`.

PR #658 is superseded as an execution owner and cannot independently satisfy union ownership.

## Current union state

| Owner | Current evidence | Union eligibility |
|---|---|---|
| A+B | #660 now contains literal READ sidecar/increment ledgers, but they explicitly remain `MAPPING_STATUS: IN_PROGRESS` / `UNACCOUNTED_FILES: NOT_YET_ZERO` and are not yet consolidated into the canonical owner ledger | IN PROGRESS |
| C | #659 capability map remains `MAPPING_STATUS: IN_PROGRESS` under the strict bar; PR body says runner/BLUECAD/tests/configs/schemas/reports/assets and zero-orphan reconciliation remain; no canonical literal ledger is yet mechanically enumerable | BLOCKED |
| D | Canonical literal ledger contains 70 committed READ rows. Three further scripts have now been re-read from fresh master and have durable exact-path evidence, but are not credited until their rows are committed into the canonical ledger | IN PROGRESS |
| Fresh tree | master `240d5e0...`; recursive tree remains authoritative comparison set | READY FOR UNION once all owner ledgers are canonical and enumerable |

## Counts

- Total tracked files: **PENDING strict mechanical enumeration**. No count is inferred from a truncated recursive-tree rendering.
- Covered files globally: **PENDING union**.
- A+B READ / GENERATED-ASSET: **PENDING canonical A+B consolidation and zero-orphan reconciliation**.
- C READ / GENERATED-ASSET: **PENDING C literal ledger**.
- D READ: **70 committed canonical rows**; 3 additional inspected paths pending canonical-row commit.
- D GENERATED/ASSET: **0 currently**.
- Duplicate ownership count: **PENDING union**.
- Ambiguous ownership count: **non-zero** until all three canonical ledgers are enumerable and cross-owner rows reconcile exactly.

## UNACCOUNTED_FILES

`UNACCOUNTED_FILES: UNKNOWN_NONZERO`

A literal zero is not defensible yet. The exact orphan list becomes mechanically valid only when all three active ledgers are canonical/enumerable against one fresh tracked tree.

### Active-owner blockers

- **A+B (#660):** literal sidecar/increment rows now exist, but #660 itself states that they must be folded into `B-frontend-operator-ux.md`; remaining backend/frontend/design-reference scope is not yet zero-orphan.
- **C (#659):** capability mapping exists, but strict file-by-file completion is explicitly still in progress; runner, BLUECAD, engineering tests/schemas/configs/reports/assets and final reconciliation remain.
- **D (#657):** `.github/browser-proof/**` is completely literalized. Remaining work includes committing the three newly re-read checker rows, then reading/classifying the rest of `scripts/**` plus D-owned governance/operations docs/config/tests/repository metadata.

## Freshness / added-file guard

For each owner, compare its ledger baseline to the fresh master tree. Any tracked file added after an owner's baseline is automatically unaccounted until the exact path is explicitly classified by an active owner. Capability prose cannot grandfather later files.

## D evidence established

The canonical D map remains strict `MAPPING_STATUS: IN_PROGRESS` with 70 committed `READ` rows. In this audit pass, the following master-baseline files were re-read in full/actual source content and have durable inspection evidence, but are deliberately not counted in D's canonical total until ledger rows are committed:

- `scripts/check_ai_threads.py` — freezes spec-090 scope, pre-created-flow authority, idempotent thread ownership, no-history egress, product-surface and lifecycle invariants.
- `scripts/check_analytics_dock.py` — enforces bounded run/output payloads, exact model-version/unit comparability, no implicit conversion, no fake analytics/statistical authority, and stale-response/cap harnesses.
- `scripts/check_app_shell.py` — freezes historical shell footprint and validates route/router/stage/accessibility/storage/style contracts.

Previously established D evidence includes all seven root files, root `.github` policy/template and worktree-control files, all 17 workflows, all `.github/browser-proof/**`, and the committed delivery/review/CI/continuation/codegen/recovery script tranche.

A concrete existing defect remains recorded: `.github/browser-proof/plans/115-project-search.json` references capture `mutationBaseline` without creating it; the generic executor fails closed on missing captures. Runtime is intentionally untouched by issue #656.

## Completion gate

Set `GLOBAL_FILE_COVERAGE: COMPLETE` only when all are mechanically checkable against one fresh tracked tree:

1. every tracked file resolves to exactly one active owner as `READ` or `GENERATED/ASSET`;
2. every `OUT_OF_SCOPE` entry resolves to an exact destination-ledger path;
3. `UNACCOUNTED_FILES: 0`;
4. duplicate ownership count = 0 after normalized cross-references;
5. ambiguous ownership count = 0;
6. files added after any owner baseline are explicitly reconciled.

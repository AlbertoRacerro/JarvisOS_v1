# JarvisOS agent manual — strict file coverage audit

GLOBAL_FILE_COVERAGE: IN_PROGRESS

Fresh master baseline: `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

This audit is fail-closed. `READ` is credited only where an active owner ledger establishes actual content inspection; capability prose, directory discovery, filename mention, or historical temporary ledgers do not count.

## Active owner set

- **A:** PR #658 / `docs/capability-map-A-product-backend`.
- **B:** PR #660 / `docs/capability-map-B-frontend-ux`.
- **C:** PR #659 / `docs/capability-map-C-engineering`.
- **D:** PR #657 / `docs/capability-map-D-devops-security`.

The temporary backend A+B increment files on PR #660 are historical source only. They do not count as B ownership and do not create duplicate union ownership. Their backend paths count only after Area A re-reads/absorbs them into PR #658.

## Current union state

| Owner | Current evidence | Union eligibility |
|---|---|---|
| A | PR #658 is again an active owner for product/backend scope. Historical backend rows on #660 are not credited to A until re-read/absorbed into A's canonical ledger. | IN PROGRESS |
| B | PR #660 owns frontend/operator UX/design-reference scope only. Historical temporary backend A+B increment rows are excluded from B and from duplicate calculations. | IN PROGRESS |
| C | PR #659 owns engineering/modeling scope; strict literal ledger and zero-orphan reconciliation remain required before final union. | IN PROGRESS |
| D | Canonical literal ledger contains 70 committed READ rows. Three further D scripts were re-read from fresh master and have exact-path evidence, but are not credited until their rows are committed into the canonical D ledger. | IN PROGRESS |
| Fresh tree | master `240d5e0...`; recursive tracked tree is the authoritative comparison set. | READY FOR UNION once all four canonical ledgers are enumerable and fresh |

## Counts

- Total tracked files: **PENDING strict mechanical enumeration**. No count is inferred from a truncated recursive-tree rendering.
- Covered files globally: **PENDING four-owner union**.
- A READ / GENERATED-ASSET: **PENDING canonical A reconciliation**.
- B READ / GENERATED-ASSET: **PENDING canonical B reconciliation; historical backend A+B temp rows excluded**.
- C READ / GENERATED-ASSET: **PENDING canonical C reconciliation**.
- D READ: **70 committed canonical rows**; 3 additional inspected paths pending canonical-row commit.
- D GENERATED/ASSET: **0 currently**.
- Duplicate ownership count: **PENDING union**; historical A+B temp rows on #660 are ignored by definition.
- Ambiguous ownership count: **non-zero** until all four canonical ledgers are enumerable and cross-owner rows reconcile exactly.

## UNACCOUNTED_FILES

`UNACCOUNTED_FILES: UNKNOWN_NONZERO`

A literal zero is not defensible yet. The exact orphan list becomes mechanically valid only when all four active ledgers are canonical/enumerable against one fresh tracked tree.

### Active-owner blockers

- **A (#658):** must re-read/absorb backend paths formerly represented only in temporary A+B increment material on #660; those historical rows do not count globally.
- **B (#660):** must finish canonical frontend/operator-UX/design-reference literal coverage while excluding historical backend temp rows from ownership.
- **C (#659):** must finish engineering/modeling literal coverage and final zero-orphan reconciliation.
- **D (#657):** `.github/browser-proof/**` is completely literalized. Remaining work includes committing the three newly re-read checker rows, then reading/classifying the rest of `scripts/**` plus D-owned governance/operations docs/config/tests/repository metadata.

## Freshness / added-file guard

For each owner, compare its ledger baseline to the fresh master tree. Any tracked file added after an owner's baseline is automatically unaccounted until the exact path is explicitly classified by an active owner. Capability prose or historical sidecars cannot grandfather later files.

## D evidence established

The canonical D map remains strict `MAPPING_STATUS: IN_PROGRESS` with 70 committed `READ` rows. In the current audit tranche, the following master-baseline files were re-read in actual source content and have inspection evidence, but are deliberately not counted in D's canonical total until ledger rows are committed:

- `scripts/check_ai_threads.py` — freezes spec-090 scope, pre-created-flow authority, idempotent thread ownership, no-history egress, product-surface and lifecycle invariants.
- `scripts/check_analytics_dock.py` — enforces bounded run/output payloads, exact model-version/unit comparability, no implicit conversion, no fake analytics/statistical authority, and stale-response/cap harnesses.
- `scripts/check_app_shell.py` — freezes historical shell footprint and validates route/router/stage/accessibility/storage/style contracts.

Previously established D evidence includes all seven root files, root `.github` policy/template and worktree-control files, all 17 workflows, all `.github/browser-proof/**`, and the committed delivery/review/CI/continuation/codegen/recovery script tranche.

A concrete existing defect remains recorded: `.github/browser-proof/plans/115-project-search.json` references capture `mutationBaseline` without creating it; the generic executor fails closed on missing captures. Runtime is intentionally untouched by issue #656.

## Completion gate

Set `GLOBAL_FILE_COVERAGE: COMPLETE` only when all are mechanically checkable against one fresh tracked tree:

1. every tracked file resolves to exactly one active owner as `READ` or `GENERATED/ASSET`;
2. every `OUT_OF_SCOPE` entry resolves to an exact destination-ledger path;
3. historical A+B temporary backend rows on #660 are excluded from B/union ownership and any needed backend paths are independently covered by A;
4. `UNACCOUNTED_FILES: 0`;
5. duplicate ownership count = 0 after normalized cross-references;
6. ambiguous ownership count = 0;
7. files added after any owner baseline are explicitly reconciled.

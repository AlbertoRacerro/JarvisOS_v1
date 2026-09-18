# JarvisOS agent manual — strict file coverage audit

GLOBAL_FILE_COVERAGE: IN_PROGRESS

Fresh master baseline: `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; root tree `26db144c1d54e4b9dd4a9ebd9ef32829bbba99ed`.

This audit is fail-closed. `READ` is credited only where an active owner ledger establishes actual content inspection; capability prose, directory discovery, filename mention, or historical temporary ledgers do not count.

## Active owner set

- **A:** PR #658 / `docs/capability-map-A-product-backend`.
- **B:** PR #660 / `docs/capability-map-B-frontend-ux`.
- **C:** PR #659 / `docs/capability-map-C-engineering`.
- **D:** PR #657 / `docs/capability-map-D-devops-security`.

The temporary backend A+B increment files on PR #660 are historical source only. They do not count as B ownership and do not create duplicate union ownership. Their backend paths count only after Area A re-reads/absorbs them into PR #658.

## Exact mechanical denominator — ESTABLISHED

Supervisor-verified exact enumeration is authoritative for this baseline. The root non-recursive Git tree is `truncated:false` and contains 7 root blobs. Each top-level subtree was fetched independently with recursive Git-tree traversal and independently verified `truncated:false`; all returned non-tree entries were blobs and no submodules were present.

| Top-level set | Exact tracked blobs |
|---|---:|
| root | 7 |
| `.github` | 43 |
| `backend` | 613 |
| `configs` | 5 |
| `docs` | 459 |
| `frontend` | 135 |
| `reports` | 661 |
| `schemas` | 15 |
| `scripts` | 67 |
| `tests` | 31 |
| **TOTAL_TRACKED_FILES** | **2036** |

The previous breadth-first reconstruction is retired for denominator purposes unless master SHA changes. Exact normalized path extraction and four-ledger union are now the active task.

Required counters:

- `TOTAL_TRACKED_FILES: 2036`
- `READ_FILES: PENDING_FOUR_LEDGER_UNION`
- `GENERATED_ASSET_FILES: PENDING_FOUR_LEDGER_UNION`
- `COVERED_FILES: PENDING_FOUR_LEDGER_UNION`
- `UNACCOUNTED_FILES_COUNT: PENDING_EXACT_PATH_LEDGER_UNION`
- `COVERAGE_PERCENT: PENDING_EXACT_PATH_LEDGER_UNION`
- A assigned / covered / remaining: `PENDING_EXACT_PATH_LEDGER_UNION`
- B assigned / covered / remaining: `PENDING_EXACT_PATH_LEDGER_UNION`
- C assigned / covered / remaining: `PENDING_EXACT_PATH_LEDGER_UNION`
- D assigned / covered / remaining: `PENDING_EXACT_PATH_LEDGER_UNION`
- duplicate ownership count: `PENDING_FOUR_LEDGER_UNION`
- ambiguous ownership count: `PENDING_EXACT_PATH_LEDGER_UNION`

**Accounting invariant gate:** `2036 = COVERED_FILES + UNACCOUNTED_FILES_COUNT` must hold after duplicate/ambiguity normalization before the audit can be valid. It is not asserted until the exact path-set/ledger union is computed.

## Exact path extraction checkpoint

The normalized master-set extraction has started from the fixed tree rather than re-deriving the denominator. The root tree was re-fetched directly and is `truncated:false`; its exact seven blob paths are:

- `.gitignore`
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `Start-JarvisOS-Backend.cmd`
- `Start-JarvisOS-Frontend.cmd`
- `Start-JarvisOS.cmd`

The same root response establishes the exact subtree SHAs used for independent recursive extraction, including `scripts` = `f641460e1746c8b22c0c0fb5606ac2982c9de8ca`. A recursive fetch of that exact scripts tree was issued and GitHub's returned tree begins with the expected normalized blob sequence and nested `data_root_recovery/**` paths. The connector display truncates the large response before all 67 blobs can be copied into this document, so this run does **not** claim a complete literal scripts path set from the displayed payload. The supervisor-verified cardinality of 67 remains denominator evidence, not path-union evidence. No partial scripts list is credited as exhaustive.

A previously inspected D file, `scripts/check_lineage_overview.py`, was re-read from the exact master SHA this run. Its content is a deterministic LINEAGE-OVERVIEW-1 conformance checker over frontend lineage/workspace state plus STATUS lifecycle evidence, with explicit stale-response, ordering, selection-boundary and fake-authority negative checks. It remains excluded from global `READ_FILES` until the canonical D ledger contains its exact READ row; this preserves actual-read plus canonical-ledger semantics.

## Current union state

| Owner | Current evidence | Union eligibility |
|---|---|---|
| A | PR #658 active product/backend owner; historical backend rows on #660 are not credited until independently re-read/absorbed by A. | IN PROGRESS |
| B | PR #660 owns frontend/operator UX/design-reference scope only; historical temporary backend rows are excluded. | IN PROGRESS |
| C | PR #659 owns engineering/modeling scope. | IN PROGRESS |
| D | Canonical literal ledger contains 79 committed READ rows; `scripts/check_lineage_overview.py` is actually read but remains uncredited pending canonical-ledger insertion. | IN PROGRESS |
| Fresh tree | exact denominator established at 2036 tracked files; root exact path set is now durably extracted, top-level recursive literal path extraction continues. | IN PROGRESS |

## UNACCOUNTED_FILES

Exact literal `UNACCOUNTED_FILES` is pending mechanical extraction of the 2036 normalized paths and union against the latest canonical A/B/C/D ledgers. This is not interpreted as zero and does not satisfy completion.

### Deterministic next work

1. Continue independent recursive extraction of each top-level subtree at the fixed baseline and materialize every blob path; do not substitute cardinality for literal paths.
2. Normalize/deduplicate with the seven root paths to an exact 2036-path master set; fail closed if cardinality differs from 2036.
3. Fetch latest canonical A/B/C/D ledgers from PR branches; exclude B historical backend A+B temporary rows.
4. Parse exact READ and GENERATED/ASSET paths and mechanically union them against master paths.
5. Persist exact counters, duplicate/ambiguous sets, and literal orphan queues grouped by provisional owner/directory.
6. Consume D-owned orphans by actual reading; leave exact A/B/C queues for their owners.

### Active-owner blockers

- **GLOBAL:** finish literal normalized 2036-path extraction and mechanically union four canonical ledgers.
- **A (#658):** re-read/absorb backend paths formerly represented only in temporary A+B material on #660.
- **B (#660):** finish canonical frontend/operator-UX/design-reference literal coverage while excluding historical backend temp rows.
- **C (#659):** finish engineering/modeling literal coverage and zero-orphan reconciliation.
- **D (#657):** insert the already-read `scripts/check_lineage_overview.py` into the canonical ledger; then continue from mechanically generated D orphan queue.

## Freshness / added-file guard

For each owner, compare its ledger baseline to fresh master tree. Any tracked file added after an owner's baseline is automatically unaccounted until exact path is explicitly classified by an active owner. Capability prose or historical sidecars cannot grandfather later files. If master changes from `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`, invalidate the denominator/path set and enumerate the new tree before completion.

## D evidence established

Canonical D map remains strict `MAPPING_STATUS: IN_PROGRESS` with 79 committed `READ` rows. `scripts/check_lineage_overview.py` has been actually inspected from fresh master but remains uncredited until canonical-ledger insertion. No runtime/product code is modified by this audit.

Previously established D evidence includes all seven root files, root `.github` policy/template and worktree-control files, all 17 workflows, all `.github/browser-proof/**`, and the committed delivery/review/CI/continuation/codegen/recovery script tranche.

A concrete existing defect remains recorded: `.github/browser-proof/plans/115-project-search.json` references capture `mutationBaseline` without creating it; generic executor fails closed on missing captures. Runtime is intentionally untouched by issue #656.

## Completion gate

Set `GLOBAL_FILE_COVERAGE: COMPLETE` only when all are mechanically checkable against this exact 2036-file fresh tree:

1. exact normalized tracked-path set cardinality is 2036;
2. `2036 = COVERED_FILES + UNACCOUNTED_FILES_COUNT` after duplicate/ambiguity normalization;
3. every tracked file resolves to exactly one active owner as `READ` or `GENERATED/ASSET`;
4. every `OUT_OF_SCOPE` entry resolves to an exact destination-ledger path;
5. historical A+B temporary backend rows on #660 are excluded and any needed backend paths are independently covered by A;
6. `UNACCOUNTED_FILES_COUNT: 0`;
7. duplicate ownership count = 0;
8. ambiguous ownership count = 0;
9. cross-owner references resolve and files added after any owner baseline are explicitly reconciled.

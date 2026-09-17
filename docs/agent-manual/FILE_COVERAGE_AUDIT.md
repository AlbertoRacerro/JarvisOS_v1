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

## Mechanical denominator status — BLOCKED, fail closed

Fresh remote master was re-resolved on 2026-09-17 through the GitHub branch API and remains exactly `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; its root tree is `26db144c1d54e4b9dd4a9ebd9ef32829bbba99ed`.

The required exact recursive Git-tree enumeration was attempted first, before further qualitative mapping, using `GET /repos/AlbertoRacerro/JarvisOS_v1/git/trees/master?recursive=1`, which is semantically equivalent to recursively enumerating the commit tree. The connector accepted the request but its response surface is oversized/truncated and does not expose the complete JSON payload to a machine-processing tool. A direct `git clone`/`git ls-tree -r --name-only origin/master` fallback was also attempted in the execution container and failed because that container has no DNS/network route to `github.com` (`Could not resolve host: github.com`). Therefore an exact integer denominator cannot be derived without guessing in this run.

**Accounting invariant is intentionally NOT asserted while the denominator is unavailable.** No approximate count, percentage, or orphan total is published. This is the exact external blocker that must be cleared before qualitative mapping resumes: obtain a non-truncated recursive tree payload or a Git-capable checkout, then compute normalized path sets and enforce `TOTAL_TRACKED_FILES = COVERED_FILES + UNACCOUNTED_FILES_COUNT` after duplicate/ambiguity normalization.

Required counters remain gated as follows:

- `TOTAL_TRACKED_FILES: BLOCKED_ON_EXACT_TREE_ENUMERATION`
- `READ_FILES: BLOCKED_ON_FOUR_LEDGER_UNION`
- `GENERATED_ASSET_FILES: BLOCKED_ON_FOUR_LEDGER_UNION`
- `COVERED_FILES: BLOCKED_ON_FOUR_LEDGER_UNION`
- `UNACCOUNTED_FILES_COUNT: BLOCKED_ON_EXACT_TREE_ENUMERATION`
- `COVERAGE_PERCENT: BLOCKED_ON_EXACT_TREE_ENUMERATION`
- A assigned / covered / remaining: `BLOCKED_ON_EXACT_TREE_ENUMERATION`
- B assigned / covered / remaining: `BLOCKED_ON_EXACT_TREE_ENUMERATION`
- C assigned / covered / remaining: `BLOCKED_ON_EXACT_TREE_ENUMERATION`
- D assigned / covered / remaining: `BLOCKED_ON_EXACT_TREE_ENUMERATION`
- duplicate ownership count: `BLOCKED_ON_FOUR_LEDGER_UNION`
- ambiguous ownership count: `BLOCKED_ON_EXACT_TREE_ENUMERATION`

## Current union state

| Owner | Current evidence | Union eligibility |
|---|---|---|
| A | PR #658 active product/backend owner; historical backend rows on #660 are not credited until independently re-read/absorbed by A. | IN PROGRESS |
| B | PR #660 owns frontend/operator UX/design-reference scope only; historical temporary backend rows are excluded. | IN PROGRESS |
| C | PR #659 owns engineering/modeling scope. | IN PROGRESS |
| D | Canonical literal ledger contains 79 committed READ rows; `scripts/check_lineage_overview.py` is actually read but remains uncredited until canonical-ledger insertion succeeds. | IN PROGRESS |
| Fresh tree | master `240d5e0...`, root tree `26db144c...`; exact recursive enumeration currently blocked as documented above. | BLOCKED |

## UNACCOUNTED_FILES

Exact literal `UNACCOUNTED_FILES` cannot be generated until the exact normalized tracked-file set is available. This is not interpreted as zero and does not satisfy completion.

### Active-owner blockers

- **GLOBAL:** exact mechanical denominator/tree payload is unavailable through the current execution surfaces; this is now the first blocker.
- **A (#658):** must re-read/absorb backend paths formerly represented only in temporary A+B increment material on #660.
- **B (#660):** must finish canonical frontend/operator-UX/design-reference literal coverage while excluding historical backend temp rows.
- **C (#659):** must finish engineering/modeling literal coverage and zero-orphan reconciliation.
- **D (#657):** canonical insertion of `scripts/check_lineage_overview.py` remains pending; after denominator recovery, continue only from the mechanically generated D orphan queue.

## Freshness / added-file guard

For each owner, compare its ledger baseline to the fresh master tree. Any tracked file added after an owner's baseline is automatically unaccounted until the exact path is explicitly classified by an active owner. Capability prose or historical sidecars cannot grandfather later files.

## D evidence established

The canonical D map remains strict `MAPPING_STATUS: IN_PROGRESS` with 79 committed `READ` rows. `scripts/check_lineage_overview.py` has been actually inspected from fresh master but remains uncredited because its attempted canonical-ledger insertion was rejected before execution by the GitHub connector safety check. No runtime/product code is modified by this audit.

Previously established D evidence includes all seven root files, root `.github` policy/template and worktree-control files, all 17 workflows, all `.github/browser-proof/**`, and the committed delivery/review/CI/continuation/codegen/recovery script tranche.

A concrete existing defect remains recorded: `.github/browser-proof/plans/115-project-search.json` references capture `mutationBaseline` without creating it; the generic executor fails closed on missing captures. Runtime is intentionally untouched by issue #656.

## Completion gate

Set `GLOBAL_FILE_COVERAGE: COMPLETE` only when all are mechanically checkable against one fresh tracked tree:

1. exact `TOTAL_TRACKED_FILES` is derived from a complete recursive Git-tree enumeration;
2. `TOTAL_TRACKED_FILES = COVERED_FILES + UNACCOUNTED_FILES_COUNT` after duplicate/ambiguity normalization;
3. every tracked file resolves to exactly one active owner as `READ` or `GENERATED/ASSET`;
4. every `OUT_OF_SCOPE` entry resolves to an exact destination-ledger path;
5. historical A+B temporary backend rows on #660 are excluded and any needed backend paths are independently covered by A;
6. `UNACCOUNTED_FILES_COUNT: 0`;
7. duplicate ownership count = 0;
8. ambiguous ownership count = 0;
9. files added after any owner baseline are explicitly reconciled.

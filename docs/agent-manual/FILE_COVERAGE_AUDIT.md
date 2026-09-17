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

## Mechanical denominator status — BREADTH-FIRST TRAVERSAL IN PROGRESS

The previous recursive-tree blocker is no longer treated as terminal. On 2026-09-17 the exact non-recursive root Git tree was fetched successfully and returned `truncated:false`. Breadth-first traversal has begun by fetching child tree SHAs individually without `recursive=1`.

Verified non-recursive tree checkpoints:

- root `26db144c1d54e4b9dd4a9ebd9ef32829bbba99ed`: complete (`truncated:false`); immediate trees are `.github`, `backend`, `configs`, `docs`, `frontend`, `reports`, `schemas`, `scripts`, `tests`; root also contains seven blobs.
- `.github` tree `5e5814bc5febc97050d9d7468961c1197b2f6439`: complete (`truncated:false`); child trees `browser-proof` and `workflows`, plus four immediate blobs.
- `backend` tree `181f4ceb6706cd9d6277103479926eae9f73cd09`: complete (`truncated:false`); child trees `app` and `tests`, plus five immediate blobs.
- `configs` tree `ae088584f40dddbf92507b87f7e69bbc53ea2b5d`: complete (`truncated:false`); five immediate blobs, no child trees.
- `docs` tree `e46f18ea475c6f5f79895e4811acaa15a82640a4`: the connector display is still oversized/truncated even without recursive traversal. Therefore `docs` must be enumerated through a smaller retrieval surface or split via exact child-directory discovery; no denominator is inferred from the partial response.

Durable traversal queue/checkpoint for the next continuation:

1. Resolve `docs` safely without using its truncated payload for counts; prefer code-search/directory-specific child discovery or another exact Git-data surface.
2. Fetch root child trees `frontend` (`3773cd76215df3b9d1227768f5160de7376fbe01`), `reports` (`e0f1cb39da18db6b61cde9b1767efaa38d7b4696`), `schemas` (`ca6b6a51355c42461b94d751b66744b658a488bb`), `scripts` (`f641460e1746c8b22c0c0fb5606ac2982c9de8ca`), and `tests` (`4125f0a449045ff55b5aa0f051d722642c5e6865`).
3. Descend `.github/browser-proof` (`8d322344d8c6708d0c531d280f603730f4e68297`), `.github/workflows` (`6892f52a31222cd4dacc481d0165bf8c9416039b`), `backend/app` (`7d5e0a165afa17a9841a3a0bafa88dedae9f7823`), and `backend/tests` (`dd6d280a2c16625b57dd9f700f9f3578776b96bf`).
4. Continue breadth-first until every queued tree resolves exclusively to blobs/submodules. Only then construct the normalized tracked-path set and publish the exact denominator.

**Accounting invariant is intentionally NOT asserted until traversal completes.** No approximate count, percentage, or orphan total is published.

Required counters remain gated:

- `TOTAL_TRACKED_FILES: PENDING_EXACT_BFS_TREE_COMPLETION`
- `READ_FILES: PENDING_FOUR_LEDGER_UNION`
- `GENERATED_ASSET_FILES: PENDING_FOUR_LEDGER_UNION`
- `COVERED_FILES: PENDING_FOUR_LEDGER_UNION`
- `UNACCOUNTED_FILES_COUNT: PENDING_EXACT_BFS_TREE_COMPLETION`
- `COVERAGE_PERCENT: PENDING_EXACT_BFS_TREE_COMPLETION`
- A assigned / covered / remaining: `PENDING_EXACT_BFS_TREE_COMPLETION`
- B assigned / covered / remaining: `PENDING_EXACT_BFS_TREE_COMPLETION`
- C assigned / covered / remaining: `PENDING_EXACT_BFS_TREE_COMPLETION`
- D assigned / covered / remaining: `PENDING_EXACT_BFS_TREE_COMPLETION`
- duplicate ownership count: `PENDING_FOUR_LEDGER_UNION`
- ambiguous ownership count: `PENDING_EXACT_BFS_TREE_COMPLETION`

## Current union state

| Owner | Current evidence | Union eligibility |
|---|---|---|
| A | PR #658 active product/backend owner; historical backend rows on #660 are not credited until independently re-read/absorbed by A. | IN PROGRESS |
| B | PR #660 owns frontend/operator UX/design-reference scope only; historical temporary backend rows are excluded. | IN PROGRESS |
| C | PR #659 owns engineering/modeling scope. | IN PROGRESS |
| D | Canonical literal ledger contains 79 committed READ rows; `scripts/check_lineage_overview.py` is actually read but remains uncredited until canonical-ledger insertion succeeds. | IN PROGRESS |
| Fresh tree | master `240d5e0...`, root tree `26db144c...`; exact breadth-first traversal is now active with a durable queue above. | IN PROGRESS |

## UNACCOUNTED_FILES

Exact literal `UNACCOUNTED_FILES` will be generated only after the normalized tracked-file set is complete. This is not interpreted as zero and does not satisfy completion.

### Active-owner blockers

- **GLOBAL:** finish the exact breadth-first Git-tree traversal, then mechanically union the four canonical ledgers.
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

1. exact `TOTAL_TRACKED_FILES` is derived from complete breadth-first/non-recursive Git-tree enumeration;
2. `TOTAL_TRACKED_FILES = COVERED_FILES + UNACCOUNTED_FILES_COUNT` after duplicate/ambiguity normalization;
3. every tracked file resolves to exactly one active owner as `READ` or `GENERATED/ASSET`;
4. every `OUT_OF_SCOPE` entry resolves to an exact destination-ledger path;
5. historical A+B temporary backend rows on #660 are excluded and any needed backend paths are independently covered by A;
6. `UNACCOUNTED_FILES_COUNT: 0`;
7. duplicate ownership count = 0;
8. ambiguous ownership count = 0;
9. files added after any owner baseline are explicitly reconciled.

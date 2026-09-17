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

Exact non-recursive root Git tree remains `truncated:false`. Breadth-first traversal continues by fetching child tree SHAs individually without `recursive=1`.

Verified non-recursive tree checkpoints:

- root `26db144c1d54e4b9dd4a9ebd9ef32829bbba99ed`: complete (`truncated:false`); immediate trees `.github`, `backend`, `configs`, `docs`, `frontend`, `reports`, `schemas`, `scripts`, `tests`; seven root blobs.
- `.github` `5e5814bc5febc97050d9d7468961c1197b2f6439`: complete; child trees `browser-proof`, `workflows`, plus four blobs.
- `.github/browser-proof` `8d322344d8c6708d0c531d280f603730f4e68297`: complete (`truncated:false`); 11 immediate blobs and child trees `fixtures` (`d47f563078f690209dbca163bf567b0b5a08fff7`) and `plans` (`382aae278505cefc7c358b13f3fe8fba7ffdb68c`).
- `.github/browser-proof/fixtures` `d47f563078f690209dbca163bf567b0b5a08fff7`: complete; 3 blobs.
- `.github/browser-proof/plans` `382aae278505cefc7c358b13f3fe8fba7ffdb68c`: complete; 8 blobs.
- `.github/workflows` `6892f52a31222cd4dacc481d0165bf8c9416039b`: complete; 17 blobs.
- `backend` `181f4ceb6706cd9d6277103479926eae9f73cd09`: complete; child trees `app`, `tests`, plus five blobs.
- `backend/app` `7d5e0a165afa17a9841a3a0bafa88dedae9f7823`: **complete (`truncated:false`)**; exactly 2 immediate blobs (`__init__.py`, `main.py`) and four child trees: `api` (`ec580ba4d7177bc6f4eeab686321e37ec1d3a4e6`), `core` (`11e938416a01b4e608c375fc436e53920bce0a96`), `modules` (`a5756e1dd0f64d64ca3e94462c1843d01c31838d`), `schemas` (`f0e412397c67dda9ecfe27b6b6cd610776eb4c5a`).
- `backend/tests` `dd6d280a2c16625b57dd9f700f9f3578776b96bf`: underlying non-recursive tree is connector-display-truncated; partial immediate blob list is excluded. Two exact child trees were recovered from the visible prefix: `backend/tests/bluecad` (`d99528f63bd3cc449eb34d4dbc9c2c6fbd0858c7`) and `backend/tests/fixtures` (`e212e3cc698db7ae9ccf27ffc67a27327f301e93`).
- `backend/tests/fixtures` `e212e3cc698db7ae9ccf27ffc67a27327f301e93`: **terminal complete (`truncated:false`)**; exactly 2 blobs.
- `backend/tests/bluecad` `d99528f63bd3cc449eb34d4dbc9c2c6fbd0858c7`: connector-display-truncated because of its large immediate blob set; partial blobs excluded. Exact child `fixtures` (`923df0fb0e374203b053a3bd74a61b497325bee9`) recovered.
- `backend/tests/bluecad/fixtures` `923df0fb0e374203b053a3bd74a61b497325bee9`: **complete (`truncated:false`)**; 10 immediate blobs and child trees `fem_verification` (`5044ac4f4db1165baf79747e6d5b92c1bee2ba9f`) and `property_geometry` (`3a77399b6e49a8212a96bb0f7c437da6e33d2303`).
- `backend/tests/bluecad/fixtures/property_geometry` `3a77399b6e49a8212a96bb0f7c437da6e33d2303`: **terminal complete**; exactly 2 blobs.
- `backend/tests/bluecad/fixtures/fem_verification` `5044ac4f4db1165baf79747e6d5b92c1bee2ba9f`: **complete**; 2 immediate blobs and child trees `cantilever` (`db8d0f88c1eb66e59a84686ab655deae8f4c9b40`), `plate_with_hole` (`d9a7bad8baa4b8ac339a71983f5667ed89abecef`), `segmented_cylinder` (`a99eeb27eb486d3a6c883f284205127d7914af33`).
- those three FEM fixture child trees are **terminal complete** and each contains exactly 2 blobs (`manifest.json`, `model.step`).
- `configs` `ae088584f40dddbf92507b87f7e69bbc53ea2b5d`: complete; five blobs.
- `frontend` `3773cd76215df3b9d1227768f5160de7376fbe01`: complete; five immediate blobs and child trees `public`, `src`, `tests`.
- `schemas` `ca6b6a51355c42461b94d751b66744b658a488bb`: complete; 15 blobs.
- `reports` `e0f1cb39da18db6b61cde9b1767efaa38d7b4696`: complete; one immediate blob plus 39 child trees checkpointed previously.
- `tests` `4125f0a449045ff55b5aa0f051d722642c5e6865`: connector-display-truncated; partial immediate blobs excluded; exact child `tests/fixtures` (`7431123ed0af068136cef1ccc2534b39257358fb`) queued.
- `docs` `e46f18ea475c6f5f79895e4811acaa15a82640a4`: Git-tree and repository-contents parent payloads exceed connector display budget; partial payloads excluded.
- `scripts` `f641460e1746c8b22c0c0fb5606ac2982c9de8ca`: parent response connector-truncated; partial blobs excluded. Exact child `scripts/data_root_recovery` (`0afa149242e66a78a4db0a2090353d56ba956208`) queued.

### Durable traversal queue/checkpoint

1. Resolve `docs` exact immediate entries through smaller exact retrieval surfaces; do not count truncated parent payload.
2. Resolve complete immediate `scripts/**` blob set; descend `scripts/data_root_recovery` (`0afa149242e66a78a4db0a2090353d56ba956208`).
3. Resolve complete immediate `tests/**` blob set; descend `tests/fixtures` (`7431123ed0af068136cef1ccc2534b39257358fb`).
4. Descend frontend child trees: `frontend/public` (`278c79dffe00104511969635ba02454ebad1f90d`), `frontend/src` (`16fc4b1a6fd39f0e0f6b0ae948af19058a8c1dac`), `frontend/tests` (`15747481e17a349b68a8b1e6efe098c7fc4c9d7d`).
5. Continue backend BFS through `backend/app/api` (`ec580ba4d7177bc6f4eeab686321e37ec1d3a4e6`), `backend/app/core` (`11e938416a01b4e608c375fc436e53920bce0a96`), `backend/app/modules` (`a5756e1dd0f64d64ca3e94462c1843d01c31838d`), and `backend/app/schemas` (`f0e412397c67dda9ecfe27b6b6cd610776eb4c5a`). Resolve the complete immediate blob sets of oversized `backend/tests` and `backend/tests/bluecad`; their recovered fixture descendants listed above are terminal-complete.
6. Descend all 39 exact `reports/**` child-tree SHAs checkpointed in prior audit revision.
7. Continue BFS until every queued tree resolves exclusively to blobs/submodules. Only then construct normalized tracked-path set and publish exact denominator.

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
| Fresh tree | master `240d5e0...`, root tree `26db144c...`; `.github` is terminal-enumerated and backend traversal now reaches app child queues plus terminal fixture descendants. | IN PROGRESS |

## UNACCOUNTED_FILES

Exact literal `UNACCOUNTED_FILES` will be generated only after the normalized tracked-file set is complete. This is not interpreted as zero and does not satisfy completion.

### Active-owner blockers

- **GLOBAL:** finish exact BFS Git-tree traversal, then mechanically union four canonical ledgers.
- **A (#658):** re-read/absorb backend paths formerly represented only in temporary A+B material on #660.
- **B (#660):** finish canonical frontend/operator-UX/design-reference literal coverage while excluding historical backend temp rows.
- **C (#659):** finish engineering/modeling literal coverage and zero-orphan reconciliation.
- **D (#657):** canonical insertion of `scripts/check_lineage_overview.py` remains pending; after denominator recovery, continue only from mechanically generated D orphan queue.

## Freshness / added-file guard

For each owner, compare its ledger baseline to fresh master tree. Any tracked file added after an owner's baseline is automatically unaccounted until exact path is explicitly classified by an active owner. Capability prose or historical sidecars cannot grandfather later files.

## D evidence established

Canonical D map remains strict `MAPPING_STATUS: IN_PROGRESS` with 79 committed `READ` rows. `scripts/check_lineage_overview.py` has been actually inspected from fresh master but remains uncredited because its attempted canonical-ledger insertion was rejected before execution by the GitHub connector safety check. No runtime/product code is modified by this audit.

Previously established D evidence includes all seven root files, root `.github` policy/template and worktree-control files, all 17 workflows, all `.github/browser-proof/**`, and the committed delivery/review/CI/continuation/codegen/recovery script tranche.

A concrete existing defect remains recorded: `.github/browser-proof/plans/115-project-search.json` references capture `mutationBaseline` without creating it; generic executor fails closed on missing captures. Runtime is intentionally untouched by issue #656.

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

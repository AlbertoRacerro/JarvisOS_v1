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
- `backend` `181f4ceb6706cd9d6277103479926eae9f73cd09`: complete; child trees `app`, `tests`, plus five blobs.
- `configs` `ae088584f40dddbf92507b87f7e69bbc53ea2b5d`: complete; five blobs.
- `reports` `e0f1cb39da18db6b61cde9b1767efaa38d7b4696`: **complete (`truncated:false`)**. Immediate level contains one blob `reports/bluecad_spike_a1_a2.md` and 39 child trees: `024-C-PREFLIGHT` (`bed3911fff589610420a881591a0f616b6856174`), `024-C1-VERIFICATION-KERNEL` (`1745e32b406425e245bedaaea973f9e16b816a06`), `024-C2-ANALYTIC-BATTERY` (`621cfb4340f220ebfa6d4703c62f0771e4980572`), `056-DEFINITION-RECONCILIATION` (`557a93d9ad0891d3cf1cd54d0e5912dc173ab8b7`), `056-PROPERTY-BASED-GEOMETRY-TESTING` (`29aa6842e3da38257cf620a41ecf777474185202`), `059-EGRESS-AUTOPILOT-AMENDMENT` (`faa7bf1280028f24832694e849b0c04a57b85b0a`), `059-IP-EGRESS-DEFINITION` (`1458f58fabbaa67962f4f8ac91e5e0e6ea034f15`), `059A-IP-EGRESS-SENSITIVITY-CONTEXT` (`bd333205d7a13f3c35d247852242c595684ecc59`), `059B-FULL-SPEC-RECONCILIATION` (`8a8d6a34bbb3b55604851d77a542708f0ca57b15`), `059B-POLICY-AUTOPILOT-IMPLEMENTATION` (`e4ee4d20a07abec2e0ad096978ea61e944929d05`), `BLUEREV-ENGINEERING-PLAYBOOK-V1` (`7fcdeae542bf7c877adfd042bd6e368599bdfa43`), `E1-EXTERNAL-EGRESS-SAFETY-GATE` (`fc903861e45caeee4e7408bfb29a8552ba63ea5f`), `E2-EXTERNAL-ROUTING-FLAG-GOVERNANCE` (`aebf7dc38a5bc155222acb48f7789423811f7154`), `E3-EXTERNAL-BUDGET-SESSION-GATE` (`82d05e698fddcb4a08246ac1e6c60d2feaeced4d`), `E4-A1-DETERMINISTIC-EGRESS-SCOPE` (`69bc20aa0c112fd939bc34e3cc64fdd605befa1b`), `E4-A2-CANONICAL-DIGEST-HELPER` (`8b9911cdb1dfe768d48b90d5a01b8efd32ac2716`), `E4-A3-CONFIRMATION-DIGEST-BINDING-INTEGRATION` (`f73ba2736e048469adc4d74f10a39312bd523995`), `E4-A3-PRE-DIGEST-BINDING-CONTRACT` (`8b59d75857bbe5a67cfc43a6f0fb1864fd72c3b2`), `E4-A4-CONFIRMATION-DECISION-REVALIDATION-BOUNDARY` (`532e780ab005b2a77bceb10daa0cca753464909a`), `E4-A5-CONFIRMED-EXECUTION-ACTIVATION-BOUNDARY` (`ab108cdb374a0132739af74244594653fc47398b`), `E4-A6-CONFIRMED-EXECUTION-CONSUMPTION-DURABLE-TICKET-BOUNDARY` (`35d1877364bca72ce7a92030ea31be1acd9cf584`), `E4-A7-PRE-3-NO-PROVIDER-RUNTIME-AUTHORITY-CHAIN-DRY-RUN` (`fe70628f030a1abe36931af8fcb611674933e321`), `E4-A7-PRE-4-BENCHMARK-FIXTURE-SCHEMA-REPLAY-HARNESS` (`2cd8cd8671653b8895e1462a2798661fd81fe539`), `E4-A7-PRE-5-ROUTING-RECOMMENDATION-FALLBACK-CONTRACT-NO-PROVIDER-PERMISSION` (`8d6a204bb7f7df11455f446bd00ac5993bcb4746`), `E4-A7-PRE-ECONOMIC-EXECUTION-POLICY-BOUNDARY` (`3fd9d47a527de6f36bdfe3acd99b1c75cd8d0422`), `E4-BASELINE-CLEANUP` (`d78935cf8a5aa7987a8e9aa4e690fe4841eb79e2`), `E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB` (`5c39df5cc52b7547c9d2e698229c5c2e9d703190`), `E4-PRE-ROUTER-EXTERNAL-PROPOSAL-INVARIANT` (`19e56dcd18010bd864c36b8b130efc4bd2225585`), `POST-101-LIFECYCLE-GATE-FIX` (`aa007258f6b707ff591fb195f3b921979996fd65`), `POST-ADR059-LIFECYCLE-RECONCILIATION` (`51be89772ddf42ac73f11a117a545d3804f3ac78`), `WP2-ROUTING-MEMORY-KERNELS` (`440d5f8e599974f4cadd229dba2d9c9238c6e7a3`), `WP3-ROADMAP-RESEQUENCE` (`2cbcb818ed91ac4a51d0e393f4e780a37c797861`), `WP4-AUTOPILOT-ADR` (`8432540864cd101b2e2f53ccedf1401ff967653e`), `WP5-HERMES-INTEGRATION-KERNELS` (`d013f9ba41f843b753ad99099b9c611b123d7282`), `WP6-HERMES-ADOPTION-ADR` (`6600bbf9aebeb33b58a296078d0214ed600910b0`), `bluecad_spike_a1_a2_artifacts` (`9333eed20669d4c4c786af2a55fb4fa4829e1e54`), `local_model_smoke` (`7c47669ff4f691fd4523e65e46ecc7792e02954e`), `router_policy` (`1e65792549bb1ddc09726052492d7ac5c62f809f`).
- `docs` `e46f18ea475c6f5f79895e4811acaa15a82640a4`: both Git-tree and repository-contents directory payloads exceed connector display budget; their partial payloads are excluded from counts. This remains the exceptional directory requiring smaller exact child discovery.
- `scripts` `f641460e1746c8b22c0c0fb5606ac2982c9de8ca`: non-recursive request itself is accepted, but its payload is connector-display truncated because of the large immediate blob list. Its partial payload is excluded from denominator counts. One exact child tree was nevertheless visible before truncation: `scripts/data_root_recovery` (`0afa149242e66a78a4db0a2090353d56ba956208`). The immediate `scripts/**` blob list must be recovered through a smaller exact surface before counting.

### Durable traversal queue/checkpoint

1. Resolve `docs` exact immediate entries through smaller directory-specific/code-search/Git-data retrieval; do not count its truncated parent payload.
2. Resolve the complete immediate `scripts/**` blob set through a smaller exact retrieval surface; descend `scripts/data_root_recovery` (`0afa149242e66a78a4db0a2090353d56ba956208`).
3. Fetch still-unvisited root child trees `frontend` (`3773cd76215df3b9d1227768f5160de7376fbe01`), `schemas` (`ca6b6a51355c42461b94d751b66744b658a488bb`), `tests` (`4125f0a449045ff55b5aa0f051d722642c5e6865`).
4. Descend `.github/browser-proof` (`8d322344d8c6708d0c531d280f603730f4e68297`), `.github/workflows` (`6892f52a31222cd4dacc481d0165bf8c9416039b`), `backend/app` (`7d5e0a165afa17a9841a3a0bafa88dedae9f7823`), `backend/tests` (`dd6d280a2c16625b57dd9f700f9f3578776b96bf`).
5. Descend all 39 exact `reports/**` child-tree SHAs listed above.
6. Continue BFS until every queued tree resolves exclusively to blobs/submodules. Only then construct normalized tracked-path set and publish exact denominator.

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
| Fresh tree | master `240d5e0...`, root tree `26db144c...`; exact BFS has complete root/.github/backend/configs/reports parent checkpoints and a durable child queue. | IN PROGRESS |

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
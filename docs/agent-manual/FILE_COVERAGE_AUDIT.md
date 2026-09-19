# JarvisOS agent manual — strict file coverage audit

GLOBAL_FILE_COVERAGE: IN_PROGRESS

Fresh master baseline: `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; root tree `26db144c1d54e4b9dd4a9ebd9ef32829bbba99ed`.

This audit is fail-closed. `READ` is credited only where an active owner ledger establishes actual content inspection; capability prose, directory discovery, filename mention, or historical temporary ledgers do not count.

## Active owner set

- **A:** PR #658 / `docs/capability-map-A-product-backend`.
- **B:** PR #660 / `docs/capability-map-B-frontend-ux`.
- **C:** PR #659 / `docs/capability-map-C-engineering`.
- **D:** PR #657 / `docs/capability-map-D-devops-security`.

Historical backend A+B temporary rows on PR #660 are source-only and never count as B/global coverage.

## Exact mechanical denominator — ESTABLISHED

Supervisor-verified enumeration is authoritative for this baseline. Root non-recursive tree is `truncated:false` with 7 blobs. Each top-level subtree was independently fetched recursively with `truncated:false`; all non-tree entries were blobs and no submodules were present.

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

Required counters remain fail-closed pending exact path union:

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

**Accounting invariant gate:** `2036 = COVERED_FILES + UNACCOUNTED_FILES_COUNT` must hold after duplicate/ambiguity normalization before this audit can be valid.

## Exact root paths

- `.gitignore`
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `Start-JarvisOS-Backend.cmd`
- `Start-JarvisOS-Frontend.cmd`
- `Start-JarvisOS.cmd`

## Canonical owner-ledger discovery checkpoint

- **A:** canonical main ledger `docs/agent-manual/parts/A-product-backend-ai-data.md` plus `A-product-backend-ai-data.increment-11.md`; #660 backend hints remain source-only.
- **B:** exact `docs/agent-manual/parts` inventory was recovered from the branch Contents response. It contains **29 files total**: 27 increment/progress artifacts plus the canonical `B-frontend-operator-ux.md` and `B-frontend-operator-ux-ledger-progress.md`. The exact names are checkpointed below, so B inventory is no longer a connector-truncation blocker.
- **C:** exact four inputs: `C-engineering-bluecad-process.md`, `C-engineering-bluecad-process.file-coverage-progress.md`, `C-engineering-bluecad-process-audit.md`, `C-engineering-bluecad-process-audit-progress.md`.
- **D:** canonical current ledger `docs/agent-manual/parts/D-development-delivery-security-ops.md`.

### Exact B parts inventory

1. `B-file-coverage-increment-2026-09-17-11.md`
2. `B-file-coverage-increment-2026-09-17-domain-foundation.md`
3. `B-file-coverage-increment-2026-09-18-0231.md`
4. `B-frontend-operator-ux-increment-2026-09-17T2030.md`
5. `B-frontend-operator-ux-ledger-increment-11.md`
6. `B-frontend-operator-ux-ledger-increment-17.md`
7. `B-frontend-operator-ux-ledger-increment-2026-09-16T1506Z.md`
8. `B-frontend-operator-ux-ledger-increment-2026-09-16T2102Z.md`
9. `B-frontend-operator-ux-ledger-increment-2026-09-17T0132Z.md`
10. `B-frontend-operator-ux-ledger-increment-2026-09-17T0232Z.md`
11. `B-frontend-operator-ux-ledger-increment-2026-09-17T0730Z.md`
12. `B-frontend-operator-ux-ledger-increment-2026-09-17T0927Z.md`
13. `B-frontend-operator-ux-ledger-increment-2026-09-17T1129Z.md`
14. `B-frontend-operator-ux-ledger-increment-2026-09-17T1331Z.md`
15. `B-frontend-operator-ux-ledger-increment-2026-09-17T1427Z.md`
16. `B-frontend-operator-ux-ledger-increment-2026-09-17T1630Z.md`
17. `B-frontend-operator-ux-ledger-increment-2026-09-17T1933Z.md`
18. `B-frontend-operator-ux-ledger-increment-2026-09-17T2132Z.md`
19. `B-frontend-operator-ux-ledger-increment-2026-09-17T2230.md`
20. `B-frontend-operator-ux-ledger-increment-2026-09-18-0828.md`
21. `B-frontend-operator-ux-ledger-increment-2026-09-18T0030.md`
22. `B-frontend-operator-ux-ledger-increment-2026-09-18T0130.md`
23. `B-frontend-operator-ux-ledger-progress.md`
24. `B-frontend-operator-ux.md`
25. `B-ledger-increment-2026-09-18-0532.md`
26. `B-ledger-increment-2026-09-18-0629.md`
27. `B-ledger-increment-2026-09-18-0730.md`
28. `B-ledger-increment-2026-09-18T0327-threads.md`
29. `B-ledger-increment-2026-09-18T0429-coding-api.md`
30. `B-ledger-increment-2026-09-18T0932.md`

**Correction:** the exact response contains **30 files**, not the previously estimated 29. This explicit count is authoritative for this checkpoint. All 30 names above came from one complete Contents payload; future B additions remain subject to the freshness guard.

## Current union state

| Owner | Current evidence | Union eligibility |
|---|---|---|
| A | Main ledger + increment identified; #660 hints excluded. | READY FOR LITERAL ROW PARSE |
| B | Exact 30-file parts inventory recovered and checkpointed. | READY FOR LITERAL ROW PARSE |
| C | Four exact canonical part inputs identified. | READY FOR LITERAL ROW PARSE |
| D | Canonical ledger contains actual-read evidence. | READY FOR LITERAL ROW PARSE |
| Fresh tree | exact denominator established at 2036 tracked files. | IN PROGRESS |

## UNACCOUNTED_FILES

Exact literal `UNACCOUNTED_FILES` remains pending mechanical extraction of the normalized 2036 master paths and union against canonical A/B/C/D ledger rows. This is not interpreted as zero.

### Deterministic next work

1. Parse literal READ / GENERATED-ASSET / OUT_OF_SCOPE rows from all exact A/B/C/D inputs above, de-duplicating repeated B increment rows by exact path/status.
2. Materialize the exact normalized 2036 master path set from the fixed baseline; fail closed if cardinality differs from 2036.
3. Resolve OUT_OF_SCOPE only when the destination owner ledger contains the exact path.
4. Persist exact counters, duplicate/ambiguous sets and literal orphan queues grouped by provisional owner/directory.
5. Consume D-owned orphans by actual reading; publish exact A/B/C orphan queues for their owners.

## Freshness / added-file guard

Any tracked file added after an owner's baseline is unaccounted until explicitly classified. If master changes from `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`, invalidate denominator/path set before completion.

## Completion gate

Set `GLOBAL_FILE_COVERAGE: COMPLETE` only when all are mechanically checkable against the exact 2036-file tree: normalized master-set cardinality 2036; accounting invariant holds; every tracked file resolves exactly once as READ or GENERATED/ASSET; OUT_OF_SCOPE destinations resolve; historical #660 backend temporary rows are excluded; unaccounted=0; duplicate ownership=0; ambiguous ownership=0; cross-owner references and freshness guard pass.

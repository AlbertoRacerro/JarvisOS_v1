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

The union input locations were re-discovered directly from the live owner branches rather than guessed from prior notes.

- **A:** canonical main ledger is `docs/agent-manual/parts/A-product-backend-ai-data.md` (blob `9122dda08379f5421b1278652c944f54f3370b46`), with `A-product-backend-ai-data.increment-11.md` (blob `2a89d9127a0eea6266259cc7944e983216c383f8`) also present on the A branch. The main ledger explicitly states that PR #660 is hints-only and confers no coverage; its literal table contains `READ` and `OUT_OF_SCOPE` rows. This is now the canonical A parsing target.
- **B:** the B branch currently contains multiple timestamped `B-file-coverage-*` and `B-frontend-operator-ux-ledger-*` increment files. The directory response itself exceeded connector display budget, so this run does not pretend the visible prefix is a complete B ledger inventory. B must be parsed from its canonical B-owned frontend/operator-UX evidence only; historical backend temporary rows remain excluded.
- **C:** the C branch currently exposes exactly four part files in the inspected parts directory: `C-engineering-bluecad-process.md` (`82202e886fa2094dc425acb5c644448f50ef6237`), `C-engineering-bluecad-process.file-coverage-progress.md` (`61ecf11ebcfc38ebf3d1b2ce2887e94a9df279d0`), `C-engineering-bluecad-process-audit.md` (`9514c703d32ee66e0656451650d793024bacb898`), and `C-engineering-bluecad-process-audit-progress.md` (`db812e5b9a40b56d9eb3098442c9261500722fe3`). These are now the deterministic C parsing inputs.
- **D:** canonical current ledger is `docs/agent-manual/parts/D-development-delivery-security-ops.md`; `scripts/check_lineage_overview.py` is now a committed exact `READ` row.

This checkpoint removes filename ambiguity for A/C/D and records the remaining B-inventory extraction problem explicitly. It does **not** infer coverage counts from prose or from file presence.

## Current union state

| Owner | Current evidence | Union eligibility |
|---|---|---|
| A | Canonical main ledger and increment-11 identified; main ledger explicitly excludes #660 hints-only coverage. | READY FOR LITERAL ROW PARSE |
| B | Multiple canonical B increments exist; directory payload is display-truncated and needs exact inventory/row parse. | IN PROGRESS |
| C | Four exact canonical part inputs identified with blob SHAs. | READY FOR LITERAL ROW PARSE |
| D | Canonical ledger contains actual-read evidence including `scripts/check_lineage_overview.py`. | READY FOR LITERAL ROW PARSE |
| Fresh tree | exact denominator established at 2036 tracked files. | IN PROGRESS |

## UNACCOUNTED_FILES

Exact literal `UNACCOUNTED_FILES` remains pending mechanical extraction of the normalized 2036 master paths and union against canonical A/B/C/D ledger rows. This is not interpreted as zero.

### Deterministic next work

1. Parse exact literal READ / GENERATED-ASSET / OUT_OF_SCOPE rows from the identified A/C/D inputs and finish exact B input inventory.
2. Materialize the exact normalized 2036 master path set from the fixed baseline; fail closed if cardinality differs from 2036.
3. Resolve OUT_OF_SCOPE only when the destination owner ledger contains the exact path.
4. Persist exact counters, duplicate/ambiguous sets and literal orphan queues grouped by provisional owner/directory.
5. Consume D-owned orphans by actual reading; publish exact A/B/C orphan queues for their owners.

## Freshness / added-file guard

Any tracked file added after an owner's baseline is unaccounted until explicitly classified. If master changes from `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`, invalidate denominator/path set before completion.

## Completion gate

Set `GLOBAL_FILE_COVERAGE: COMPLETE` only when all are mechanically checkable against the exact 2036-file tree: normalized master-set cardinality 2036; accounting invariant holds; every tracked file resolves exactly once as READ or GENERATED/ASSET; OUT_OF_SCOPE destinations resolve; historical #660 backend temporary rows are excluded; unaccounted=0; duplicate ownership=0; ambiguous ownership=0; cross-owner references and freshness guard pass.

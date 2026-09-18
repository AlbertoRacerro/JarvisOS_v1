# Global file-coverage union — durable mechanical progress

Baseline: `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; exact denominator `TOTAL_TRACKED_FILES = 2036` from `FILE_COVERAGE_AUDIT.md`.

This sidecar is fail-closed staging evidence for the final global audit. Counts below are only for literal rows actually parsed from complete, retrievable owner shards; they are **not** global coverage counters and must not be promoted to `FILE_COVERAGE_AUDIT.md` until all owner inputs and the exact 2036-path master set are reconciled.

## Mechanical parse checkpoint — 2026-09-18

### Area A

Parsed complete shard `docs/agent-manual/parts/A-product-backend-ai-data.increment-11.md` on branch `docs/capability-map-A-product-backend`.

- literal READ rows: 8
- GENERATED/ASSET rows: 0
- OUT_OF_SCOPE rows: 0
- paths are all under `backend/app/modules/ai/`
- these rows remain staged because the shard itself requires merge-back into A's canonical ledger before final credit.

### Area C

Parsed the complete retrievable staging ledgers:

- `C-engineering-bluecad-process.file-coverage-progress.md`: 16 READ rows
- `C-engineering-bluecad-process-audit-progress.md`: 22 READ rows
- `C-engineering-bluecad-process-audit.md`: 2 READ rows

Exact-path normalization across those three shards yields **28 unique READ paths**. Repeated rows are duplicate evidence inside the same owner and are de-duplicated by exact path; they are not cross-owner duplicate ownership. All 28 are under `backend/app/modules/runner/`.

The canonical `C-engineering-bluecad-process.md` response is larger than the connector display budget, so no global C count is asserted from a partial canonical read. C remains incomplete until its canonical ledger plus all staging rows are losslessly parsed and normalized.

### Master-set spot check

The fixed root tree `26db144c1d54e4b9dd4a9ebd9ef32829bbba99ed` was re-fetched non-recursively and remains `truncated:false`, with the same seven root blobs and the same nine top-level subtree SHAs. The `schemas` subtree was independently fetched recursively at `ca6b6a51355c42461b94d751b66744b658a488bb`; it is `truncated:false` with exactly 15 blobs, matching the supervisor-verified denominator component.

## Fail-closed state

`GLOBAL_FILE_COVERAGE: IN_PROGRESS`

Do not derive `READ_FILES`, `COVERED_FILES`, `UNACCOUNTED_FILES_COUNT`, owner totals, duplicate ownership, ambiguous ownership, or coverage percentage from this partial checkpoint. The next mechanical work is to parse remaining A/B/C/D ledger inputs and materialize the exact normalized 2036-path set, then compute the set union/difference and deterministic orphan queues.

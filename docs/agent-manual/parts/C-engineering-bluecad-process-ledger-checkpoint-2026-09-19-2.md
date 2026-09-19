# Area C explicit-ledger checkpoint — 2026-09-19 (continuation)

MAPPING_STATUS: IN_PROGRESS

Fresh-tree baseline: `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

This continuation is a durable literal-inspection shard pending lossless consolidation into `C-engineering-bluecad-process.md`; it does not supersede the canonical ledger and COMPLETE is not claimed.

| path | status | one-line role/reason |
|---|---|---|
| `backend/tests/bluecad/test_spec_stage1.py` | READ | Stage-1 GeometrySpec/golden-fixture contract battery: enumerates every non-expected JSON fixture, validates and canonicalizes each with stable `sha256:` spec identity, requires matching positive analytic part/total-volume oracle files, proves canonical JSON/spec ID invariance under key-order permutations, and requires unsupported part kind, NaN geometry and impossible wall thickness to fail as structured `SPEC_INVALID` with the exact offending JSON path. |

CHECKPOINT_UNACCOUNTED_FILES: >0

Next: continue literal BLUECAD test/helper/fixture coverage and fresh-tree reconciliation; consolidate all checkpoint rows into the canonical `## EXPLICIT FILE COVERAGE LEDGER` before any COMPLETE claim.

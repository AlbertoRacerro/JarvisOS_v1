# Area C explicit-ledger checkpoint — 2026-09-19 (continuation)

MAPPING_STATUS: IN_PROGRESS

Fresh-tree baseline: `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

This continuation is a durable literal-inspection shard pending lossless consolidation into `C-engineering-bluecad-process.md`; it does not supersede the canonical ledger and COMPLETE is not claimed.

| path | status | one-line role/reason |
|---|---|---|
| `backend/tests/bluecad/test_spec_stage1.py` | READ | Stage-1 GeometrySpec/golden-fixture contract battery: enumerates every non-expected JSON fixture, validates and canonicalizes each with stable `sha256:` spec identity, requires matching positive analytic part/total-volume oracle files, proves canonical JSON/spec ID invariance under key-order permutations, and requires unsupported part kind, NaN geometry and impossible wall thickness to fail as structured `SPEC_INVALID` with the exact offending JSON path. |
| `backend/tests/bluecad/test_manifest_determinism_canary.py` | READ | Determinism canary: runs a child build through parents with distinct `PYTHONHASHSEED` values and requires identical child payloads while pinning the child seed to `0`; under the explicit Ubuntu 24/Python 3.11 canary profile it rebuilds four canonical geometry fixtures twice, compares spec IDs and full manifest digests to the checked-in expected oracle, records artifact SHA-256 diagnostics, and optionally writes mismatch diagnostics without weakening the equality assertion. |
| `backend/tests/conftest.py` | READ | Shared pytest harness with Area-C-relevant controls: adds the `--require-bluecad-real-tools` fail-vs-skip gate for hash-verified Gmsh/CalculiX proof tooling, replaces the resolved client only for the named bundled-047 and legacy-runner test files, and forces every test onto an isolated temporary `JARVISOS_DATA_ROOT`; its separate ScaleWay compatibility bridge is generic AI test infrastructure outside Area C. |

CHECKPOINT_UNACCOUNTED_FILES: >0

Next: continue literal BLUECAD/engineering test-helper/fixture coverage and fresh-tree reconciliation; consolidate all checkpoint rows into the canonical `## EXPLICIT FILE COVERAGE LEDGER` before any COMPLETE claim.
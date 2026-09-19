# Area C engineering-test file coverage — 075 checkpoint

MAPPING_STATUS: IN_PROGRESS

Temporary durable Area-C audit shard for issue #656. Rows are backed by actual content inspection from fresh `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb` and MUST be consolidated into `docs/agent-manual/parts/C-engineering-bluecad-process.md` before Area C may be marked COMPLETE.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | one-line role/reason |
|---|---|---|
| `backend/tests/test_process_kernel_075.py` | READ | Process-kernel integrity/compatibility test battery: proves independent parameterized Pipe instances and non-mutating stream outputs; pins the 048 rounded CO2:C screening constants; verifies the registered 047 bundle is a closed explicit file set; and fail-closed tests modified, missing, extra, symlinked, stale-manifest, top-level sibling/directory and modified-entrypoint cases with deterministic runner bundle error codes. |
| `backend/tests/test_process_kernel_075_identity.py` | READ | Exact 075↔canonical-047 identity oracle: runs the legacy bundled 047 script for turbulent and laminar cases and requires matching diagnostics, per-output units and float hex, canonical JSON bytes and SHA-256; separately proves supported equivalent physical units normalize to the same case/result within tight numerical tolerance. |
| `backend/tests/test_process_kernel_075_runner.py` | READ | End-to-end exact-profile runner proof: registration is idempotent, binding preview resolves all nine DOF, repeated real jobs are stable with reduced deterministic environment and immutable bundle manifest, only result.json is registered; exhaustive profile-identity/package/contract/registry/constants/import-policy tampering is rejected before subprocess, and generic calc_v0 cannot import process_kernel. |
| `backend/tests/test_bluerev_geometry_hydraulics_v0_laminar.py` | READ | Focused 047 laminar-regime oracle: executes the bundled model as a subprocess with a low-velocity canonical case, requires success/result emission, proves Re<2300, pins Darcy friction factor to 64/Re at 1e-15 relative tolerance, and requires diagnostics to identify the Darcy convention and `laminar_64_over_Re` correlation. |

UNACCOUNTED_FILES: >0

Next: inspect and ledger remaining engineering-specific runner tests, then BLUECAD tests/schemas/configs/reports/assets; consolidate every staging row into the canonical ledger and perform the final fresh-tree set difference before COMPLETE.

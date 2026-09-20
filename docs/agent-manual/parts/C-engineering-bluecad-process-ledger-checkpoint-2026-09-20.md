# Area C explicit-ledger checkpoint — 2026-09-20

MAPPING_STATUS: IN_PROGRESS

Fresh-tree baseline inspected: `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.
PR #659 head inspected before this run: `12c4b79da4caad9289a3a8846eec7ffeb453e6b7`.

This checkpoint records literal content inspection pending lossless consolidation into `C-engineering-bluecad-process.md`. It does not supersede the canonical `## EXPLICIT FILE COVERAGE LEDGER`; COMPLETE is not claimed.

| path | status | one-line role/reason |
|---|---|---|
| `backend/tests/bluecad/test_registry.py` | READ | BLUECAD tool-registry fail-closed battery: rejects duplicate IDs, unknown fields and missing SPDX; pins explicit-path > operator-env > default registry precedence while proving request-shaped candidate data cannot select a registry; distinguishes unknown/disabled/missing/unhashed/hash-drift tool failures; exercises bounded subprocess cwd/output/timeout behavior; enforces license/integration boundaries and shipped YAML consistency; checks forbidden in-process solver-import detection; and verifies registry-check success/failure exit evidence. |
| `backend/tests/bluecad/alpha_real_tools_support.py` | READ | Real-tool proof helper: builds the bounded static AnalysisSpec and offline synthetic provider bindings, reads candidate-scoped artifact/evidence/simulation rows, and asserts the complete validation→mesh→FEM chain including immutable artifact hashes, three typed pass evidence records, completed simulation output, positive mesh/group counts, optional exact volume-element type, real (non-fake) solver identity and finite non-negative displacement/stress metrics. |
| `backend/tests/bluecad/hashseed_determinism_runner.py` | READ | Determinism subprocess helper: loads a named golden fixture, builds and validates it in a temporary directory, snapshots spec ID/manifest digest/artifact hashes, and—regardless of the parent process seed—spawns the actual BLUECAD child with canonical `PYTHONHASHSEED=0`, bounded timeout and machine-readable sorted JSON output. |
| `backend/tests/bluecad/test_capped_manifold.py` | READ | Capped-manifold contract/kernel battery: cross-checks schema, canonical validator and AI prompt vocabulary; rejects non-integer/bool/out-of-range branch counts, non-positive gaps/stubs/caps, invalid wall ratios, unexpected params and derived overflow before kernel execution; under the pinned canary proves exact common/branch ports, bbox/final volume, valid manifold solid, open bores with closed cap, mirrored parallel-path assembly consistency for 1/2/12 branches, and repeat-build manifest determinism. |
| `backend/tests/test_process_kernel_075_identity.py` | READ | 075 scientific identity proof: runs the legacy exact-bundled 047 script and process-kernel implementation on canonical turbulent and laminar cases, requires identical schema/status/diagnostics/output units, float-hex values, canonical JSON bytes and SHA-256 digest, then proves physically equivalent alternate units normalize to the same case and numerically equivalent outputs. |

CHECKPOINT_UNACCOUNTED_FILES: >0

Next: continue literal process-kernel/runner and BLUECAD test/helper/fixture coverage, then perform fresh-tree owned-scope set-difference and fold every checkpoint row into the canonical explicit ledger before any COMPLETE claim.

## Durable consolidation blocker

The connected GitHub write surface still exposes whole-file replacement rather than patch editing, while the canonical Area-C document is returned only through bounded reads. Replacing that canonical document from partial content risks deleting prior mapping evidence. This checkpoint therefore preserves actual inspection progress without making a false COMPLETE claim; consolidation remains mandatory before completion.
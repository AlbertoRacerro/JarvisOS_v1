# Area C explicit-ledger checkpoint — 2026-09-19

MAPPING_STATUS: IN_PROGRESS

Fresh-tree baseline: `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

This checkpoint records literal inspection completed for immediate consolidation into `C-engineering-bluecad-process.md`. It does not supersede the canonical `## EXPLICIT FILE COVERAGE LEDGER`, and COMPLETE is not claimed.

| path | status | one-line role/reason |
|---|---|---|
| `backend/tests/fixtures/bluerev_process_topology_m1_valid.json` | READ | Canonical positive 072/M1 topology fixture: two parallel branches, nonzero illuminated/dark straight lengths and bends, explicit common sections/manifold volumes, tube diameters, fluid properties, pump efficiency and distributed minor-loss coefficients for deterministic topology/hydraulics tests. |
| `backend/tests/fixtures/bluerev_process_topology_m1_zero_bend.json` | READ | Canonical 072/M1 degenerate-boundary fixture: one branch with zero bends, zero common lengths/manifold volumes and zero associated loss coefficients while retaining valid tube/fluid/pump inputs, exercising the supported zero-bend/zero-common-section topology boundary. |
| `schemas/bluerev_process_topology_m1_v0_1.schema.json` | READ | Draft-2020-12 closed schema for the 072/M1 topology manifest: pins model/schema identity, the complete 26-field executed-input envelope and units, 1–12 symmetric branches, ordered loop components, branch geometry/bend semantics, laminar-or-Blasius hydraulic bases/loss coefficients, geometry totals, SHA-256 input binding and explicit non-spatial/no-network-solver/no-recycle/no-property-package/no-pump-curve limitations. |
| `backend/tests/test_bluerev_process_topology_m1.py` | READ | End-to-end 072/M1 scientific test battery: pins the value-free 26-variable contract and closed schema, exact output set and symmetric conservation relations, canonical byte-stable topology manifest plus raw SHA-256 binding, cross-field fail-closed geometry/source-ID validation, exact one-path reduction to 047 hydraulics, qualified laminar/Blasius correlation boundaries, deterministic repeated manifests, and rejection of false single-length/M0 equivalence when dark straight or non-illuminated bend geometry remains. |

CHECKPOINT_UNACCOUNTED_FILES: >0

Durable consolidation note: these rows must be copied into the canonical explicit ledger before Area C may claim completion. The current GitHub connector exposes existing-file replacement rather than append/patch semantics; the canonical document is returned only through bounded/truncated reads, so this checkpoint preserves inspected-file progress rather than risking destructive reconstruction of that long document. Once lossless patch/full-file access is available, consolidate all Area-C shards into the canonical ledger and delete the temporary shards.

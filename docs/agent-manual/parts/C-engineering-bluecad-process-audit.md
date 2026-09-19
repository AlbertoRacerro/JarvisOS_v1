# Area C explicit file audit — durable continuation shard

MAPPING_STATUS: IN_PROGRESS

This file is a temporary durable continuation shard for issue #656 / PR #659. The canonical ledger remains `docs/agent-manual/parts/C-engineering-bluecad-process.md` under `## EXPLICIT FILE COVERAGE LEDGER`; every row here MUST be folded into that ledger before Area C may be marked COMPLETE.

Fresh-tree baseline inspected: `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.
Latest PR head inspected before this run: `0fe414c42d24ef2f00bf1322b6706afd78016725`.

| path | status | one-line role/reason |
|---|---|---|
| `backend/app/modules/runner/local_python.py` | READ | Cross-platform local Python execution transport: creates single-owner sessions backed by caller/owner/child OS locks, delegates execution to the owner process when prepared, otherwise uses direct `subprocess.run`; both paths use `shell=False`, a non-inherited allowlisted environment, hard timeout, bounded UTF-8 stdout/stderr, and deterministic command/environment metadata. Process-kernel examples additionally disable bytecode writes. |
| `backend/app/modules/runner/input_contracts.py` | READ | Canonical runner input-contract and binding layer: validates schema v1/v2/v3 contracts, canonicalizes and SHA-256 binds stored contracts, rejects noncanonical/hash-mismatched payloads, computes binding/DOF previews, validates manual/Parameter bindings against units/domains and schema-v2/v3 semantics, and normalizes exact execution input sets fail-closed. |

UNACCOUNTED_FILES: >0

## Durable blocker note

The connected GitHub write surface exposes whole-file replacement but no line/patch edit operation. The canonical Area C document is larger than the connector response budget when fetched whole; replacing it without a lossless full read would risk deleting existing capability-map content. Therefore newly inspected rows are committed here rather than fabricating a canonical rewrite. On a run with patch-capable repository access (or a lossless full-file read), fold these rows into the canonical `## EXPLICIT FILE COVERAGE LEDGER` and delete this temporary shard. This is an execution-surface blocker only; it is not evidence that file coverage is complete.

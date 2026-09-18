# Area C explicit file audit — durable continuation shard

MAPPING_STATUS: IN_PROGRESS

This file is a temporary durable continuation shard for issue #656 / PR #659. The canonical ledger remains `docs/agent-manual/parts/C-engineering-bluecad-process.md` under `## EXPLICIT FILE COVERAGE LEDGER`; this row MUST be folded into that ledger before Area C may be marked COMPLETE.

Fresh-tree baseline inspected this run: `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.
PR head before this run: `2ef0e2a70ffdef6e6a5867847d3b58cd9ba4d199`.

| path | status | one-line role/reason |
|---|---|---|
| `backend/app/modules/runner/local_python.py` | READ | Cross-platform local Python execution transport: creates single-owner sessions backed by caller/owner/child OS locks, delegates execution to the owner process when prepared, otherwise uses direct `subprocess.run`; both paths use `shell=False`, a non-inherited allowlisted environment, hard timeout, bounded UTF-8 stdout/stderr, and deterministic command/environment metadata. Process-kernel examples additionally disable bytecode writes. |

UNACCOUNTED_FILES: >0

## Durable blocker note

The connected GitHub write surface available in this run exposes whole-file replacement but no line/patch edit operation. The canonical Area C document is larger than the connector response budget when fetched whole; replacing it without a lossless full read would risk deleting existing capability-map content. Therefore this inspected row is committed here rather than fabricating a canonical rewrite. On a run with patch-capable repository access (or a lossless full-file read), fold this row into the canonical `## EXPLICIT FILE COVERAGE LEDGER` and delete this temporary shard. This is an execution-surface blocker only; it is not evidence that file coverage is complete.

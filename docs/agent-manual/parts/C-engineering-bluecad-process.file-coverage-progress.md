# Area C file-coverage durable progress

MAPPING_STATUS: IN_PROGRESS

Temporary staging ledger; every row must be consolidated into `docs/agent-manual/parts/C-engineering-bluecad-process.md` before completion. Fresh-tree baseline: `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | one-line role/reason |
|---|---|---|
| `backend/app/modules/runner/__init__.py` | READ | Tiny package marker identifying the minimal local runner boundary. |
| `backend/app/modules/runner/origin.py` | READ | Browser-origin mutation guard; permits missing Origin for non-browser clients and rejects origins outside configured CORS origins. |
| `backend/app/modules/runner/public_models.py` | READ | Caller-visible registration model; forbids extra fields and excludes executable/trust-shaped fields. |
| `backend/app/modules/runner/models.py` | READ | Runner API/evidence models covering run/binding states, implementation and preview payloads, bounded job creation, persisted run detail, logs and artifact provenance/integrity metadata. |
| `backend/app/modules/runner/linked_parameters.py` | READ | Fail-closed linked-Parameter freshness/revision guard for authoritative schema-v2/v3 contracts; validates workspace/lifecycle/freshness, revision and physical value identity through process-kernel unit normalization before execution. |
| `backend/app/modules/runner/input_contracts.py` | READ | Canonical schema-v1/v2/v3 input-contract validator and binding normalizer: hashes canonical payloads, enforces bounded unique variables/semantic context, validates manual or Parameter bindings, normalizes units through process-kernel conversion, and fails closed on hash/canonicality/domain/semantic mismatch. |
| `backend/app/modules/runner/local_python.py` | READ | Deterministic local-Python execution/ownership boundary: isolated allowlisted environment, cross-platform caller/owner/child locks, one-shot owner sessions, timeout handling, bounded UTF-8 stdout/stderr capture, and live/gone/unknown lock-state evidence. |

UNACCOUNTED_FILES: >0

Next: continue remaining runner runtime/helpers/examples/tests, then BLUECAD/tests/schemas/configs/reports/assets; consolidate staged rows into the canonical ledger and perform fresh-tree set difference. COMPLETE remains forbidden until `UNACCOUNTED_FILES: 0` is proven.

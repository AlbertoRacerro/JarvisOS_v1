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
| `backend/app/modules/runner/guarded_service.py` | READ | Trust-enforcing runner facade: normal registration accepts only the fixed bundled demo; reviewed scientific models use dedicated registrations; create/run require exact bundled identities, normalize exact process-kernel inputs, enforce linked-Parameter usability, preserve request-key idempotency, verify script hash/path and preflight policy, cap timeout at 60 s, and translate legacy sandbox violations to the public script-policy error. |
| `backend/app/modules/runner/recovery.py` | READ | Startup stranded-run recovery: scans persisted runner/simulation pairs without implicit DB bootstrap, leaves inconsistent/live/unknown ownership untouched, and atomically fails only coherently-running jobs whose runner-specific ownership is provably gone while emitting a deterministic failure event. |
| `backend/app/modules/runner/resilient_service.py` | READ | Concurrency/recovery wrapper for execution: validates persisted run paths before ownership, rejects a second owner as not queued, delegates execution only while holding the owner lock, and after an owned invocation failure starts a daemon follow-up that waits for ownership to become conclusive and retries stranded-job reconciliation through transient SQLite operational errors. |
| `backend/app/modules/runner/routes.py` | READ | FastAPI runner surface: exposes reviewed bundled BLUECAD/process/topology/kernel registration, implementation listing/binding preview, job creation/execution and run evidence reads; mutation endpoints use the Origin guard and RunnerSafetyError codes map deterministically to 404/409/400. |

UNACCOUNTED_FILES: >0

Next: read remaining runner `safety.py`, `service.py` plus runner examples/tests; then BLUECAD/tests/schemas/configs/reports/assets; consolidate staged rows into the canonical ledger and perform fresh-tree set difference. COMPLETE remains forbidden until `UNACCOUNTED_FILES: 0` is proven.

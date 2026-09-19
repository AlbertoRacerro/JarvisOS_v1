# Area A coverage increment 20

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

This additive shard exists to preserve the repaired canonical ledger without risking destructive replacement. Prior canonical ledger and increment shards remain authoritative evidence and are not superseded.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/egress_authority.py` | READ | External-egress prompt/manual-context authority boundary. Deterministically denies S4 prompts; S2/S3 require an already-approved derivative or exactly one explicitly local sanitizer path; marker-free prompts are eligible by default only in FAST_DEV. Local sanitizer bindings must resolve to a `local:` route and sanitizer outputs are post-validated before derivative approval. Canonical-source sanitization snapshots source bodies/digests before the local model call and revalidates them transactionally at derivative approval. Manual context delegates preview/selection to sensitivity policy, fails closed on withheld material or derivative drift/conflicting source digests, and enriches the authorized evidence manifest before returning eligible context. Important boundary: model-backed sanitization is advisory—the deterministic sensitivity floor, route locality, output validation, persisted derivative approval, source-digest revalidation and downstream egress controls remain the authority. |

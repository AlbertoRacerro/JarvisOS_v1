# Area A product/backend/AI/data — additive coverage increment 14

This is an additive evidence shard for issue #656 / PR #658. The protected canonical ledger is intentionally not rewritten here because a complete safe replacement was not established in this run. Prior canonical and increment shards remain authoritative cumulative evidence.

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
| --- | --- | --- |
| `backend/app/modules/ai/costs.py` | READ | Small AI cost/escalation helper. Defines a hard-coded per-route USD price registry, estimates input tokens as `ceil(chars/4)` with a minimum of one, defaults output allowance to 1024 tokens, computes an explicitly labeled estimate, and builds an `external:reasoning` escalation proposal using `execution.resolve_binding`. It includes the raw prompt as `outbound_text`, marks context excluded, and adds only a sensitivity warning for `confidential`/`sensitive_ip`; this module itself does not authorize egress, sanitize content, verify credentials, settle actual provider usage, or prove tokenizer-accurate cost. Failure/accuracy boundaries: unknown route classes raise via direct registry indexing; `max_output_tokens=0` is replaced by the 1024 default because `or` is used; negative nonzero output values are accepted arithmetically here unless rejected upstream; hard-coded prices and the four-chars/token heuristic can drift from provider pricing/tokenization. |

## Run note

Directly reopened `backend/app/modules/ai/costs.py` from fresh `master` before crediting it. No runtime/product code, STATUS, spec144, Hermes direction, secrets, canonical Area-A file, or other-owner docs were modified.

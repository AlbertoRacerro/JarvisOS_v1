# Area A file-coverage increment 39

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
| --- | --- | --- |
| `backend/app/modules/ai/deepseek_provider_smoke.py` | READ | DeepSeek-only diagnostic smoke surface. Applies settings/prompt/output-token/privacy gates before delegating external dispatch to canonical `run_ai_task`; projects canonical outcome into smoke response and persists started/blocked/completed audit events. The surface is intentionally not general provider routing. |

## Inspection notes

- Re-opened directly from fresh master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; credit is based on actual source inspection, not PR #660 history.
- Pre-dispatch gates require AI policy enabled, `provider_mode == "deepseek"`, non-empty prompt <= 1000 characters, requested output <= 160 tokens, and a privacy decision allowing external use with class `public` or `internal`.
- Actual external execution remains owned by `run_ai_task`; this file adds a narrower diagnostic policy envelope and audit projection around that canonical path.
- Audit writes use a separate SQLite connection/commit per smoke event. Therefore a started event can durably exist even when later execution or response projection fails; event sequences are audit evidence, not an atomic transaction spanning provider execution.
- `_reported_token` deliberately converts malformed/missing provider token metadata to `None`; reported usage is therefore not guaranteed to be present even after successful external execution.

Canonical Area-A file was not modified in this increment; this additive shard avoids destructive replacement risk while complete canonical-safe replacement is not required for durable progress.
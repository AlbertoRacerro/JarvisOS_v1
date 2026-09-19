# Area A file-coverage increment 40

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
| --- | --- | --- |
| `backend/app/modules/ai/egress_confirmation.py` | READ | Thin 059b confirmation façade over `egress_confirmation_core`: synchronizes two deliberately patchable bindings, preloads ticket metadata, consumes persisted rejected-continuation authority for expired/revoked tickets, projects that cleanup as a blocked `config_error` outcome, and otherwise delegates confirmed-ticket execution to the core implementation. |

## Inspection notes

- Re-opened directly and completely from fresh master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; credit is based on actual source inspection, not PR #660 history.
- The façade mutates `_core.evaluate_provider_budget_gate` and `_core._create_proposed_records_from_response` before each execution. This preserves monkey-patch/test seams but means those module-global core bindings are shared mutable process state rather than request-local dependencies.
- Rejected-continuation cleanup is only taken when ticket state is exactly `expired` or `revoked` and `continuation_authority_json` is present; it consumes persisted continuation state and returns without invoking the normal core confirmation execution path.
- For all other ticket states/metadata combinations, behavior and enforcement are delegated to `_core.run_confirmation_ticket`; this file alone is not the full confirmation authority.

Canonical Area-A file was not modified in this increment; this additive shard avoids destructive replacement risk while complete canonical-safe replacement is not required for durable progress.

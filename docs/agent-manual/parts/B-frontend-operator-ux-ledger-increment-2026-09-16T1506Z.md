# Area A+B explicit file coverage — durable increment

MAPPING_STATUS: IN_PROGRESS

This is a temporary durable ledger increment for issue #656 on PR #660. It records only files whose contents were directly inspected. It must be folded into `B-frontend-operator-ux.md` before completion; it is not a substitute for the canonical ledger.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | one-line role/reason |
|---|---|---|
| `backend/app/modules/ai/token_flow.py` | READ | Token-flow lifecycle/orchestration implementation; directly inspected in full for flow creation/reservation/finalization behavior and accounting/dispatch evidence handling. |
| `backend/app/modules/ai/token_flow_models.py` | READ | Typed token-flow request/response and evidence models; directly inspected to capture validation and operator-facing contract shape. |
| `backend/app/modules/ai/token_flow_routes.py` | READ | HTTP/API surface for token-flow operations; directly inspected for route-level validation/error mapping and service delegation. |
| `backend/app/modules/ai/token_flow_store.py` | READ | SQLite persistence primitives for token-flow state/evidence; directly inspected for durable storage and transactional update behavior. |
| `backend/app/modules/ai/egress_confirmation.py` | READ | Thin confirmation facade; syncs patchable core bindings, consumes persisted rejected continuations for expired/revoked tickets, otherwise delegates confirmed-ticket execution to the core. |
| `backend/app/modules/ai/deepseek_provider_smoke.py` | READ | DeepSeek-only diagnostic smoke surface; bounds prompt/output, applies policy/privacy gates, dispatches through canonical `run_ai_task`, and logs attempted/succeeded plus estimated/reported usage evidence. |
| `backend/app/modules/ai/token_guard.py` | READ | Legacy/simple token guard using `ceil(chars/4)` estimates and Scaleway monthly/hard-stop token caps; can annotate metadata with provider-reported usage. |
| `backend/app/modules/ai/privacy.py` | READ | Local deterministic privacy policy engine for smoke surfaces; blocks structural secret patterns and risky prompts and applies mode-specific allow/block classification before external smoke dispatch. |

## Absorbed Area-A capability facts

- Token-flow is a server-owned evidence/accounting lifecycle, not a frontend-owned inference. Flow state is persisted and exposed through typed models/routes rather than reconstructed from UI state.
- Provider dispatch/accounting evidence is bound to persisted flow/job state; operator UX must present unknown/failed/terminal evidence explicitly rather than infer success from a returned body alone.
- The store/service split is a reuse boundary: new operator surfaces should consume the existing API contract instead of creating a parallel browser-side flow ledger.
- Provider smoke is diagnostic only and deliberately reuses canonical execution rather than becoming a parallel provider gateway. It records whether an external call was attempted/succeeded and distinguishes estimated from reported token evidence.
- Smoke-console privacy enforcement is deterministic and local. Structural secret patterns and jailbreak/bypass markers are blocked before dispatch; operator UX must not imply that provider-side moderation is the privacy authority.
- `token_guard.py` is a simple estimate/cap seam, not proof of authoritative billing. Its character-based estimate and settings counters must not be presented as exact provider usage when reported usage is absent.
- Confirmation execution preserves persisted rejected-continuation semantics: expired/revoked tickets with continuation authority are consumed into an explicit blocked/config-error outcome rather than silently retried externally.

## Remaining coverage

Literal `UNACCOUNTED_FILES: 0` is not yet defensible. Remaining work includes unread/unreconciled A+B backend modules/tests/configs/helpers plus the complete tracked `frontend/` and `docs/design-references/` trees. A fresh recursive tree was re-read from the current PR head during this increment. Completion remains blocked until every owned tracked file has exactly one ledger row and a final fresh-tree diff returns zero unaccounted files.

### Canonical-ledger integration blocker

The connected GitHub write action replaces an existing file atomically and requires the complete current UTF-8 body plus blob SHA. The canonical `B-frontend-operator-ux.md` is larger than the connector response budget and the fetch response is truncated before the ledger tail, so replacing it from a partial body would destroy existing documentation. This increment is therefore committed separately rather than risking destructive overwrite. Next action: obtain the canonical document through a non-truncating checkout/materialization path or reconstruct it safely in bounded line ranges, then fold all durable increments into the required single `## EXPLICIT FILE COVERAGE LEDGER`.

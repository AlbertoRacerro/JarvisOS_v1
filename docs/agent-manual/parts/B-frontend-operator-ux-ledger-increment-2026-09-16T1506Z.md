# Area A+B explicit file coverage — durable increment

MAPPING_STATUS: IN_PROGRESS

This is a temporary durable ledger increment for issue #656 on PR #660. It records only files whose contents were directly inspected in this run. It must be folded into `B-frontend-operator-ux.md` before completion; it is not a substitute for the canonical ledger.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | one-line role/reason |
|---|---|---|
| `backend/app/modules/ai/token_flow.py` | READ | Token-flow lifecycle/orchestration implementation; directly inspected in full for flow creation/reservation/finalization behavior and accounting/dispatch evidence handling. |
| `backend/app/modules/ai/token_flow_models.py` | READ | Typed token-flow request/response and evidence models; directly inspected to capture validation and operator-facing contract shape. |
| `backend/app/modules/ai/token_flow_routes.py` | READ | HTTP/API surface for token-flow operations; directly inspected for route-level validation/error mapping and service delegation. |
| `backend/app/modules/ai/token_flow_store.py` | READ | SQLite persistence primitives for token-flow state/evidence; directly inspected for durable storage and transactional update behavior. |

## Absorbed Area-A capability facts

- Token-flow is a server-owned evidence/accounting lifecycle, not a frontend-owned inference. Flow state is persisted and exposed through typed models/routes rather than reconstructed from UI state.
- Provider dispatch/accounting evidence is bound to persisted flow/job state; operator UX must present unknown/failed/terminal evidence explicitly rather than infer success from a returned body alone.
- The store/service split is a reuse boundary: new operator surfaces should consume the existing API contract instead of creating a parallel browser-side flow ledger.

## Remaining coverage

Literal `UNACCOUNTED_FILES: 0` is not yet defensible. Remaining work includes unread/unreconciled A+B backend modules/tests/configs/helpers plus the complete tracked `frontend/` and `docs/design-references/` trees. A fresh recursive tree was re-read from the current PR head before this increment. Completion remains blocked until every owned tracked file has exactly one ledger row and a final fresh-tree diff returns zero unaccounted files.

### Canonical-ledger integration blocker for this run

The connected GitHub write action replaces an existing file atomically and requires the complete current UTF-8 body plus blob SHA. The canonical `B-frontend-operator-ux.md` is larger than the connector response budget and the fetch response is truncated before the ledger tail, so replacing it from a partial body would destroy existing documentation. This increment is therefore committed separately rather than risking destructive overwrite. Next action: obtain the canonical document through a non-truncating checkout/materialization path or reconstruct it safely in bounded line ranges, then fold all durable increments into the required single `## EXPLICIT FILE COVERAGE LEDGER`.

# A+B explicit file coverage ledger — 2026-09-16 21:02Z increment

MAPPING_STATUS: IN_PROGRESS

Durable literal-read increment for issue #656 / PR #660. These rows are pending consolidation into the canonical `B-frontend-operator-ux.md` `## EXPLICIT FILE COVERAGE LEDGER`. `READ` below means the file contents were directly opened and inspected on `docs/capability-map-B-frontend-ux`; no status is inferred from path/name.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | one-line role/reason |
|---|---|---|
| `backend/app/modules/ai/__init__.py` | READ | Tiny package boundary containing only the `AI gateway module boundary` module docstring; no hidden registration or import side effects. |
| `backend/app/modules/ai/budget.py` | READ | Server-owned external-provider/budget gate and AI-status projection: checks policy/paid-AI/global budget, provider enablement/credentials, provider token/cost caps, Scaleway switches, and month-to-date actual plus active/in-flight reservation usage before network execution. |
| `backend/app/modules/ai/context_builder.py` | READ | Deterministic AI context assembly and digest seam: validates caller blocks, separates PROJECT_CONTEXT as data from system/user instructions, builds bounded workspace packs from canonical records, excludes non-current parameters, and drops whole lower-priority blocks when over budget. |

## Capability facts absorbed from former Area A in this increment

- `budget.py` makes external execution fail closed when policy is disabled, paid AI is disabled, global monthly budget is zero/exhausted, the provider is disabled, required credentials are missing, or provider-specific token/cost caps are exhausted. The generic execution spine is expected to invoke this gate for each concrete network binding, including fallback attempts; request payload flags cannot self-authorize egress.
- Provider month-to-date accounting reads persisted `ai_jobs`; Scaleway additionally includes active non-expired and `in_flight` `egress_budget_reservations`, so status/gating does not ignore already-reserved spend. The status surface projects the same gate reasons instead of independently guessing whether external calls are available.
- `context_builder.py` explicitly treats PROJECT_CONTEXT as reference data, not instructions, and structurally separates it from SYSTEM and USER_REQUEST. Caller blocks are schema-bounded to source/content/type/id and canonicalized/digested deterministically.
- Normal workspace context includes only lifecycle-current parameters. Selected packs support decision/assumption/parameter/requirement/evidence with deterministic status defaults and ordering; over-budget packs drop whole blocks by priority rather than truncating record text, preserving a stable digest/source manifest for downstream inspection and dispatch checks.
- The tiny `ai/__init__.py` has no registration behavior. Any provider/route initialization must therefore be accounted for in explicit registry/composition files rather than attributed to package import magic.

## Remaining coverage

Literal A+B completion is not yet proven. Fresh branch truth at the start of this run was PR #660 head `09d05324712e7c61318790c65727e6192cc1935d`; the current recursive AI-directory listing was re-read before these files were inspected. Remaining owned backend modules/tests/configs/helpers, the complete `frontend/` tree, and `docs/design-references/` still require literal row reconciliation. The canonical document currently contains capability material but its own header still says `MAPPING_STATUS: COMPLETE`; that is not defensible under the maintainer's stricter literal-ledger rule and must be corrected during safe canonical consolidation. Until the canonical file can be reconstructed without truncation loss, verified rows are being committed as durable increments rather than replacing a partially fetched document.

UNACCOUNTED_FILES: NOT_YET_ZERO

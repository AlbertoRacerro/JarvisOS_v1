# Area B explicit file coverage increment

MAPPING_STATUS: IN_PROGRESS

This increment is B-owned frontend/operator-UX evidence only. It does not count historical Area-A rows as B ownership or global-union coverage.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
| --- | --- | --- |
| `frontend/src/app/useAppRouter.ts` | `READ` | Directly inspected from fresh master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Browser-history SPA router hook: resolves pathname, canonicalizes with `replaceState`, synchronizes `popstate`, preserves query/hash for same-origin programmatic navigation, delegates cross-origin destinations to `window.location.assign`, and exposes `{ resolved, navigate }`. Failure boundary: unguarded `new URL(href, window.location.href)` can throw for malformed href input. Route identity is pathname-derived; query/hash are carried in history targets. |

Reconciliation status: `UNACCOUNTED_FILES: 0` is NOT asserted. The canonical B document currently contains a stale `MAPPING_STATUS: COMPLETE`; that status remains non-defensible until literal fresh-tree reconciliation is finished. This increment must be folded into the canonical `docs/agent-manual/parts/B-frontend-operator-ux.md` ledger without dropping existing evidence.

# Area B explicit file coverage increment — 2026-09-19 22:30 Europe/Rome

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_RECONCILED

Evidence baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; PR #660 head at run start `43485b921e39fbc54ae83fdadbcdc87e350884af` on `docs/capability-map-B-frontend-ux`.

This increment is durable source evidence for the required canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not make the historical `MAPPING_STATUS: COMPLETE` in that document defensible; consolidation and a literal fresh-tree set reconciliation are still required before `UNACCOUNTED_FILES: 0` may be asserted.

## EXPLICIT FILE COVERAGE LEDGER — inspected increment

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/components/ui/Field.tsx` | READ | Shared accessible form-field wrapper. Direct inspection confirms it derives a stable React `useId()`-based control id when absent, clones the supplied control to link `label`/`htmlFor`, propagates `required`, composes pre-existing `aria-describedby` with generated hint/error ids, and forces `aria-invalid=true` when an error is rendered. It is presentation/accessibility wiring only: it performs no validation, persistence, authorization, mutation, sanitization, or backend operation. |

### Failure-mode notes from direct inspection

- `error` and `hint` are tested by React truthiness. Empty-string/zero-like content therefore produces neither its descriptive element nor generated `aria-describedby` id; callers must provide meaningful React content rather than treating presence of the prop key as state.
- The component accepts a generic `ReactElement<FieldControlProps>` and uses `cloneElement`; its accessibility linkage assumes the supplied control actually forwards `id`, `required`, `aria-describedby`, and `aria-invalid` to the interactive DOM element. A custom component that consumes/drops those props can visually render while breaking the intended label/error association.
- `Field` marks invalid state when an `error` node is rendered, but it does not validate input itself. Consumers must not treat `aria-invalid` or error presentation as evidence of server-side rejection or canonical validation.

## Scope reconciliation state

Fresh master tree was re-read at run start. This run intentionally adds no backend Area-A rows and makes no A/C/D ownership claim. The remaining B-owned `frontend/` and canonical operator design-reference files still require literal row-by-row reconciliation; therefore `MAPPING_STATUS` remains `IN_PROGRESS` and zero-unaccounted is explicitly not claimed.

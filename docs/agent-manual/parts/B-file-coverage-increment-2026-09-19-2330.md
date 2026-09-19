# Area B explicit file coverage increment — 2026-09-19 23:30 Europe/Rome

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_RECONCILED

Evidence baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; PR #660 head at run start `7679c46538e9de80b98ce79aaeab77c28a3a9575` on `docs/capability-map-B-frontend-ux`.

This increment is durable direct-source evidence for later consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not make the historical `MAPPING_STATUS: COMPLETE` there defensible; literal fresh-tree set reconciliation remains required before `UNACCOUNTED_FILES: 0` may be asserted.

## EXPLICIT FILE COVERAGE LEDGER — inspected increment

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/components/ui/InlineNotice.tsx` | READ | Shared inline status/feedback primitive. Direct inspection confirms five presentation tones (`info`, `success`, `warning`, `danger`, `neutral`), a fixed human-readable tone prefix, caller class/HTML-attribute forwarding, and `role="alert"` only for `danger`. It is presentation/accessibility signaling only: no validation, persistence, authorization, mutation, sanitization, backend authority, or automatic live-region semantics for non-danger notices. |

### Failure-mode notes from direct inspection

- Only `danger` defaults to `role="alert"`; success/warning/info/neutral updates are not automatically announced as live-region status. Consumers requiring asynchronous announcement must supply appropriate semantics deliberately rather than assuming the tone creates them.
- Props are spread after the component's computed `role`, so a caller can override or remove the default danger alert role. Accessibility therefore depends partly on caller discipline.
- The visible prefix (`Information`, `Success`, `Warning`, `Error`, `Notice`) is fixed by tone and always rendered in `<strong>`; the primitive does not infer severity from child content or backend state.
- A rendered notice is not evidence that the underlying operation succeeded, failed, was authorized, or reached canonical persistence; those truths remain owned by the caller/backend evidence.

## Scope reconciliation state

Fresh master tree was re-read at run start. This run adds no backend Area-A rows and makes no A/C/D ownership claim. Remaining B-owned `frontend/` and canonical operator design-reference files still require literal row-by-row reconciliation; therefore `MAPPING_STATUS` remains `IN_PROGRESS` and zero-unaccounted is explicitly not claimed.

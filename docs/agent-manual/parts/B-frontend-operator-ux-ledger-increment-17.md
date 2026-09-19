# Area B explicit file coverage — increment 17

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_ZERO

This increment is B-owned evidence only. It does not claim global-union coverage and contains no backend Area-A ownership rows. It must be consolidated into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md` before Area B can be marked complete.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/pages/AIDraft.tsx` | READ | Legacy/diagnostic AI execution workspace inspected directly. Exposes local/fake/external route selection, AI task execution/escalation, project-context opt-in, modeling draft creation, smoke tests/console, AI settings and Scaleway session-secret controls. Operator copy explicitly distinguishes fake deterministic routing, local routing and cloud routing; external execution is bounded by token/budget/provider guardrails. This is diagnostic/legacy UX, not evidence that these controls are primary production surfaces. |

## Failure-mode notes from direct inspection

- External-route submission validates `max_tokens >= 1`; route choice and project-context inclusion are controlled by explicit fields rather than prompt text.
- Scaleway API-key entry uses the dedicated secret API and the form is reset after save; the UI reads secret status rather than rendering the key back.
- Task non-success states (`needs_confirmation`, `needs_clarification`, `blocked`, provider/config/validation failures) are rendered explicitly rather than being presented as successful model output.
- Escalation requires a returned escalation proposal and a separate explicit confirmation action.
- This page includes `local:fake` by design; its existence must not be counted as proof of real-model execution or primary operator availability.

## Consolidation blocker

The canonical Area-B map still carries a stale `MAPPING_STATUS: COMPLETE` and does not yet contain the required literal one-row-per-file canonical ledger. This increment deliberately remains `IN_PROGRESS`; completion is forbidden until the canonical ledger is reconstructed/consolidated and a fresh tracked-tree comparison proves every B-owned file accounted with `UNACCOUNTED_FILES: 0`.

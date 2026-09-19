# Area B explicit file coverage increment — 2026-09-18 21:28 Europe/Rome

This is a durable increment toward the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It is B-owned frontend/operator-UX evidence only and must be folded into the canonical ledger before completion.

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_ZERO

## EXPLICIT FILE COVERAGE LEDGER — inspected increment

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/components/shell/AnalysisDock.tsx` | `READ` | Shell analysis panel. Direct inspection at PR #660 head `7c513e0699f28aee219209234fadfcc9f99928a0`: renders only when `open`; focuses its `h2` on open; Escape stops propagation and invokes `onClose`; explicit Close button invokes the same callback; caller-supplied `content` is rendered or a neutral unavailable notice is shown. This file owns presentation/focus/close interaction only, not analytics execution or persistence. Focus restoration after close is not implemented here and therefore depends on the parent shell contract. |

## Failure-mode / authority notes

- The fallback notice explicitly says analytics are unavailable in APP-SHELL-1; its presence must not be interpreted as analysis capability.
- `AnalysisDock` moves focus into the panel on open but does not itself restore focus to the opener on close. Parent `Layout` behavior is therefore required for the complete keyboard-focus contract.
- No backend request, persistence, mutation, authorization, or analysis computation exists in this file.

## Fresh-state accounting

Run-start PR #660 head: `7c513e0699f28aee219209234fadfcc9f99928a0` on `docs/capability-map-B-frontend-ux`. Fresh recursive tracked-tree enumeration was obtained from that exact head before this increment. Literal global B reconciliation remains unfinished, so `UNACCOUNTED_FILES: 0` is deliberately not asserted and the canonical document's older `MAPPING_STATUS: COMPLETE` must not be treated as current truth.

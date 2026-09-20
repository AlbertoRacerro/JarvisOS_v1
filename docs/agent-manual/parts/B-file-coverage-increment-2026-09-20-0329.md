# Area B file-coverage increment — 2026-09-20 03:29 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This is durable Area-B evidence for later consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. The canonical document's older `MAPPING_STATUS: COMPLETE` is not defensible until literal fresh-tree reconciliation proves every B-owned tracked file accounted for; this increment does **not** assert `UNACCOUNTED_FILES: 0`.

Fresh baseline for this run: `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; PR #660 head before this write `986b59ad7358e31252138ea03df514137262597b` on `docs/capability-map-B-frontend-ux`.

## EXPLICIT FILE COVERAGE LEDGER — increment

| path | status | concise role / verified boundary |
|---|---|---|
| `frontend/src/app/selection.ts` | READ | Directly inspected in full from fresh `master`. Pure TypeScript selection contract for operator-stage state. `RecordResource` is a closed union (`workspace`, `model-spec`, `assumption`, `parameter`, `simulation-run`, `decision`, `bluecad-candidate`); `RecordRef` binds resource + workspace + record IDs. `StageSelection` discriminates durable-record references from viewer-session-local geometry hits and BLUECAD binding/part selections, carrying the identifiers needed to relate ephemeral viewer objects to workspace/candidate/artifact/mesh/semantic/part context. It performs no validation, persistence, authorization, lookup, stale-session rejection, or backend mutation: constructing one of these objects is not evidence that any referenced record/artifact/part exists or remains current. Consumers must enforce workspace/session freshness and backend authority. |

## Scope discipline

No backend Area-A rows were added. Any older temporary A+B increment documents remain historical source evidence only and must not be counted as B ownership or global-union coverage; `HISTORICAL_A_SOURCE_NOT_UNION_OWNERSHIP` applies to those legacy backend-A rows pending Area-A absorption.

## Remaining-work rule

Fresh `frontend/src/app/` enumeration also contains `routes.ts`, which is not claimed READ by this increment and remains part of the literal reconciliation queue unless already supported by direct-inspection evidence elsewhere. Full tracked `frontend/` plus canonical operator `docs/design-references/` reconciliation is still required before Area B can become COMPLETE.
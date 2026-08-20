# 058c — SCENE-SEMANTICS-A1 readiness parameter-freshness correction

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-2026-08-20.md` and `docs/specs/058c-readiness-corrections-2026-08-20.md`  
Reason: close the exact-head review finding that current parameter-backed preflight can continue accepting a Parameter after replacement has marked that source `superseded`.

This correction record is part of the 058c readiness authority. Where it conflicts with either earlier readiness file, **this file wins**. All unrelated schema-v3, working-state, stale-safety, migration, deferral and non-goal decisions remain unchanged.

## 1. Exact runtime gap

Current `preview_model_bindings` loads a referenced Parameter from `parameters` using only `id`, `workspace_id`, `value`, and `unit`. The input-contract validator therefore proves existence/value/unit but does not know the Parameter lifecycle status.

Current replacement authority is stronger: accepting a configured Parameter replacement atomically marks the old accepted Parameter `status='superseded'`, marks the replacement `status='accepted'`, and persists freshness invalidation evidence. The superseded row intentionally remains in SQLite for lineage.

Therefore row existence is not freshness. Without an additional deterministic lifecycle check, a working binding can continue referencing the superseded row and still receive a ready preview. That contradicts the merged 058c definition's requirement that stale linked authority fail closed.

## 2. Minimum corrected source-freshness rule

058c V0 adds only the replacement-freshness rule proven necessary by current runtime:

- a Parameter reference with `status='superseded'` is invalid for binding preview and cannot authorize execution;
- the old Parameter remains visible/inspectable as lineage evidence and is **not** silently rewritten to its replacement;
- the operator must explicitly relink the working binding to the intended replacement Parameter before the binding can become ready again;
- same-workspace, exact-unit, numeric/domain and existing binding checks remain authoritative;
- this correction does **not** re-derive the broader lifecycle policy for other pre-existing Parameter statuses. Existing 071b behavior for non-superseded records remains unchanged unless another accepted specification changes it.

No frontend cached value may override this backend freshness decision merely because the old value is still present locally.

## 3. Execution boundary must not rely on frontend preflight alone

The frontend already requires a ready preview before normal Run, but that is not a server security/integrity boundary. A direct caller can reach runner creation without the React preflight.

The implementation must therefore reuse one deterministic Parameter-source usability check wherever a `source_parameter_id` is accepted for executable input, so a superseded source cannot create/persist a new simulation run or runner job merely by bypassing the UI preview.

The minimum implementation may extend the existing runner input/parameter-loading path; it must not add a new endpoint, service, durable store or lifecycle subsystem.

The check must occur before new run/job persistence. Existing immutable historical runs that already captured an older Parameter remain historical evidence and are not rewritten.

## 4. Corrected implementation allow-list

The earlier readiness allow-list is expanded only as needed for this proven gap:

Backend:

- `backend/app/modules/runner/input_contracts.py` — consume/validate authoritative source lifecycle state where appropriate;
- `backend/app/modules/runner/service.py` and/or the existing guarded runner create path — load Parameter lifecycle state and apply the same superseded-source fail-closed rule before preview-ready or new run/job persistence;
- focused runner/input-contract tests proving replacement freshness and no-run behavior.

No memory/replacement schema mutation is authorized: `parameters.status` and the existing replacement/freshness tables already provide the required authority.

Frontend paths and every other allow-list entry remain unchanged.

## 5. Corrected deterministic acceptance

In addition to all earlier readiness acceptance, exact-head implementation tests must prove:

1. a valid non-superseded Parameter binding preserves the pre-058c 071b preview behavior;
2. after an accepted replacement marks the old Parameter `superseded`, preview of a binding that still references the old ID is deterministically invalid/not-ready;
3. the old source is never silently substituted with the replacement ID or value;
4. explicitly relinking to the intended replacement restores normal validation when all existing value/unit/domain rules pass;
5. a direct runner-create attempt carrying a superseded `source_parameter_id` fails before creating a `simulation_runs` or `runner_jobs` row;
6. missing/cross-workspace/unit-mismatched source checks remain fail-closed as before;
7. historical run snapshots that already captured the older source are not rewritten by this change.

## 6. Corrected browser acceptance

Final 058c browser evidence must additionally cover a linked Parameter that is replaced while still referenced by the working configuration:

- the old binding becomes a real blocker/not-ready state rather than remaining executable;
- the old source remains inspectable as the historical source;
- the replacement is not auto-selected;
- after explicit relink to the replacement, Properties/preflight reflect the new source and normal readiness can recover;
- no Run is created while the superseded reference is still active.

## 7. Scope boundary remains unchanged

This correction does not authorize:

- a new Parameter lifecycle model or 098 lifecycle implementation;
- automatic source replacement;
- rewriting historical runs or records;
- SQL migration;
- a semantic backend service/endpoint;
- provider/Jarvis execution;
- formula parsing or invented `fx` content;
- any 092 scene-binding rewrite;
- 097, 098, 006b or 058b implementation;
- Notes, routine 062 grading UI or global visual identity work.

The minimum 058c implementation remains schema-v3 semantics on the existing input-contract path plus the bounded 071b controller extension, with this one additional server-side freshness guard for already-authoritative linked Parameters.

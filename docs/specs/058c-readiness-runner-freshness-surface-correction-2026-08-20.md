# 058c — fresh readiness correction: runner freshness enforcement surface

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-2026-08-20-fresh.md`, `docs/specs/058c-readiness-provenance-correction-2026-08-20.md`, and `docs/specs/058c-readiness-registration-surface-correction-2026-08-20.md`  
Reason: exact-head review of PR #317 proved that the prior correction required canonical 051 freshness at preview and immediately before persistence/execution but did not explicitly authorize the existing runner service path that currently owns preview binding resolution.

This correction is part of the 058c readiness decision. Where it conflicts with the earlier readiness records, this file governs. It changes no runtime code and does not promote `058c` from `planned`.

## 1. Failure mode closed

`backend/app/modules/runner/routes.py` exposes preview through `guarded_service.preview_model_bindings`, which currently resolves to the existing runner preview implementation in `backend/app/modules/runner/service.py::preview_model_bindings`.

That service currently loads linked Parameters for value/unit validation but does not consume canonical 051 node freshness. The base readiness allow-list mentioned `runner/service.py` only for semantic-companion registration. The provenance correction required canonical freshness but authorized only the flowsheet freshness query/service path, leaving the actual preview enforcement owner out of scope.

That scope mismatch would make the required stale-but-not-superseded rejection impossible to implement without violating readiness. It could also tempt a frontend-only or duplicate freshness check, which is forbidden.

## 2. Exact enforcement contract

Implementation must reuse the existing canonical flowsheet freshness authority and enforce linked-Parameter usability in the existing runner ownership path at both required integrity points:

1. **Preview:** `backend/app/modules/runner/service.py::preview_model_bindings` (or the exact existing helper it delegates to after implementation inspection) must consume canonical 051 freshness for each linked Parameter after same-workspace/source resolution and before returning a ready preview.
2. **Final pre-persistence execution guard:** the existing runner create/guarded path must re-check the same canonical freshness immediately before creating a new simulation-run / runner-job persistence boundary, so a source that becomes stale after preview cannot execute under the old authorization.

Required outcomes:

- canonically fresh linked Parameter + existing value/unit/domain validity → preserve current behavior;
- explicitly superseded source → fail closed;
- canonical `freshness_marks` stale source even if row status remains `proposed`, `accepted`, or otherwise non-superseded → fail closed;
- downstream Parameter made stale by upstream replacement → fail closed;
- source becoming stale after a previously ready preview → final create fails before new run/job persistence;
- no silent relink to replacement;
- no frontend freshness authority, parallel freshness state, or new lifecycle status.

The canonical helper may be reused directly or through the smallest existing runner-local adapter needed to resolve canonical Parameter refs. Do not add a second freshness store, endpoint, cache, or event system.

## 3. Exact allow-list amendment

The implementation allow-list is amended explicitly to include:

- `backend/app/modules/runner/service.py` — for canonical linked-Parameter freshness consumption in the existing preview/binding-resolution path, in addition to the already-authorized semantic-companion registration work;
- `backend/app/modules/runner/guarded_service.py` and/or the existing create service path only to perform the same canonical freshness re-check immediately before run/job persistence; use whichever current path actually owns that boundary after fresh implementation inspection;
- `backend/app/modules/runner/routes.py` only if a minimal existing-call signature pass-through is required; no new route is authorized;
- existing `backend/app/modules/flowsheet/freshness.py` / canonical graph-resolution helpers only for reuse of current 051 authority, with no new freshness semantics;
- focused runner preview/create tests covering stale-but-not-superseded and stale-after-preview cases.

No broader runner refactor, model-registration redesign, new persistence, frontend freshness check, or 098 lifecycle behavior is authorized.

## 4. Merge-blocking acceptance

Implementation evidence must prove at least:

1. a downstream linked Parameter that is canonically stale through 051 but whose own row is not `superseded` is rejected by the real runner preview path;
2. the same linked source being fresh at preview and becoming stale before create is rejected by the final pre-persistence guard;
3. rejection occurs before any new `simulation_runs` or `runner_jobs` row is persisted;
4. fresh compatible linked Parameters retain existing 071b preview/run behavior;
5. the runner and frontend do not create parallel freshness state or infer freshness from row status alone.

## 5. Review consequence

The Codex P1 delivered on PR #317 head `5ba57d4abe62e95ec38955ae58dd79405f8994d0` is valid and blocks that head because the required preview enforcement path was not explicitly in scope.

After this correction is published, all earlier exact-head CI/review evidence is stale for merge authority. The new exact head must pass fresh deterministic gates and receive an independent peer/GLM verdict that explicitly confirms the runner preview and final pre-persistence freshness enforcement surfaces are both authorized without introducing a parallel authority.

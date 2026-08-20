# 058c — fresh readiness correction: runner freshness enforcement surface

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-2026-08-20-fresh.md`, `docs/specs/058c-readiness-provenance-correction-2026-08-20.md`, and `docs/specs/058c-readiness-registration-surface-correction-2026-08-20.md`  
Reason: exact-head review of PR #317 proved that the prior correction required canonical 051 freshness at preview and immediately before persistence/execution but did not explicitly authorize the existing runner service path that currently owns preview binding resolution. A later exact-head review also proved that freshness must be rechecked when a persisted queued job is actually claimed for execution, otherwise a source can become stale after create but before `/run` dispatch.

This correction is part of the 058c readiness decision. Where it conflicts with the earlier readiness records, this file governs. It changes no runtime code and does not promote `058c` from `planned`.

## 1. Failure modes closed

`backend/app/modules/runner/routes.py` exposes preview through `guarded_service.preview_model_bindings`, which currently resolves to the existing runner preview implementation in `backend/app/modules/runner/service.py::preview_model_bindings`.

That service currently loads linked Parameters for value/unit validation but does not consume canonical 051 node freshness. The base readiness allow-list mentioned `runner/service.py` only for semantic-companion registration. The provenance correction required canonical freshness but authorized only the flowsheet freshness query/service path, leaving the actual preview enforcement owner out of scope.

That scope mismatch would make the required stale-but-not-superseded rejection impossible to implement without violating readiness. It could also tempt a frontend-only or duplicate freshness check, which is forbidden.

The runner also separates create from execution dispatch. A job may be persisted as `queued`, then remain there while its linked Parameter becomes canonically stale before `run_runner_job` claims it. A freshness check only at preview/create therefore leaves a time-of-check/time-of-use gap: the stored payload can execute after its authoritative source is no longer fresh. The execution-claim boundary must close this gap without re-reading mutable frontend state or silently relinking the source.

## 2. Exact enforcement contract

Implementation must reuse the existing canonical flowsheet freshness authority and enforce linked-Parameter usability in the existing runner ownership path at **three** integrity points:

1. **Preview:** `backend/app/modules/runner/service.py::preview_model_bindings` (or the exact existing helper it delegates to after implementation inspection) must consume canonical 051 freshness for each linked Parameter after same-workspace/source resolution and before returning a ready preview.
2. **Final pre-persistence create guard:** the existing runner create/guarded path must re-check the same canonical freshness immediately before creating a new simulation-run / runner-job persistence boundary, so a source that becomes stale after preview cannot create a queued run under the old authorization.
3. **Queued-job execution claim:** `backend/app/modules/runner/service.py::run_runner_job` / the existing queued→running claim helper must re-resolve every persisted `source_parameter_id` from the immutable stored run/job input snapshot and check the same canonical 051 freshness **inside the same SQLite claim transaction that conditionally owns `queued -> running`, before any script invocation**. A stale source at claim time must fail closed and the script must not execute. The check may not use current frontend working state, a cached preview result, or a silently substituted replacement Parameter.

The claim-time check is the execution authorization boundary. If the source becomes stale only after the successful atomic `queued -> running` claim, that later mutation does not retroactively cancel the already-started immutable execution; the race to prevent is stale-before-claim execution.

Required outcomes:

- canonically fresh linked Parameter + existing value/unit/domain validity → preserve current behavior;
- explicitly superseded source → fail closed;
- canonical `freshness_marks` stale source even if row status remains `proposed`, `accepted`, or otherwise non-superseded → fail closed;
- downstream Parameter made stale by upstream replacement → fail closed;
- source becoming stale after a previously ready preview → create fails before new run/job persistence;
- source fresh at create but stale before `/run` claim → queued job cannot transition to executable `running` state and no script is invoked;
- concurrent `/run` callers still have exactly one successful queued-job claimant; freshness validation and queued ownership are one fail-closed transaction, not two racy prechecks;
- no silent relink to replacement;
- no frontend freshness authority, parallel freshness state, or new lifecycle status.

If freshness fails for an already-persisted queued job, implementation must use the smallest existing terminal failure/error bookkeeping that keeps the immutable run/job inspectable and prevents retry from executing the stale snapshot; do not delete the persisted evidence, leave it indefinitely executable as `queued`, or invent a new lifecycle family. Exact status/error mapping must follow the current runner's existing failed-job conventions after fresh implementation inspection.

The canonical helper may be reused directly or through the smallest existing runner-local adapter needed to resolve canonical Parameter refs. Do not add a second freshness store, endpoint, cache, event system, or general cancellation framework.

## 3. Exact allow-list amendment

The implementation allow-list is amended explicitly to include:

- `backend/app/modules/runner/service.py` — for canonical linked-Parameter freshness consumption in the existing preview/binding-resolution path **and the existing `run_runner_job` / queued-job claim path**, in addition to the already-authorized semantic-companion registration work;
- `backend/app/modules/runner/guarded_service.py` and/or the existing create service path only to perform the same canonical freshness re-check immediately before run/job persistence and to preserve the existing guarded dispatch seam; use whichever current path actually owns that boundary after fresh implementation inspection;
- the existing runner queued→running claim helper, if separate from `service.py`, only to make freshness resolution/check + conditional claim atomic before script invocation;
- `backend/app/modules/runner/routes.py` only if a minimal existing-call signature pass-through is required; no new route is authorized;
- existing `backend/app/modules/flowsheet/freshness.py` / canonical graph-resolution helpers only for reuse of current 051 authority, with no new freshness semantics;
- focused runner preview/create/run tests covering stale-but-not-superseded, stale-after-preview, stale-after-create-before-dispatch, and concurrent-claim cases.

No broader runner refactor, model-registration redesign, new persistence, frontend freshness check, new execution state, or 098 lifecycle behavior is authorized.

## 4. Merge-blocking acceptance

Implementation evidence must prove at least:

1. a downstream linked Parameter that is canonically stale through 051 but whose own row is not `superseded` is rejected by the real runner preview path;
2. the same linked source being fresh at preview and becoming stale before create is rejected by the final pre-persistence guard;
3. rejection at create occurs before any new `simulation_runs` or `runner_jobs` row is persisted;
4. a linked source that is fresh when the queued run/job is persisted but becomes canonically stale before `/run` is atomically rejected at the queued-job claim boundary, with **zero script invocation**;
5. the stale queued job cannot later be retried into execution without a new valid run intent/snapshot under existing authority, and its persisted evidence remains inspectable using existing runner terminal/error conventions;
6. two concurrent `/run` calls still cannot execute the same queued job twice, including when freshness validation is part of the claim transaction;
7. fresh compatible linked Parameters retain existing 071b preview/create/run behavior;
8. the runner and frontend do not create parallel freshness state or infer freshness from row status alone.

## 5. Review consequence

The Codex P1 delivered on PR #317 head `5ba57d4abe62e95ec38955ae58dd79405f8994d0` is valid and blocks that head because the required preview enforcement path was not explicitly in scope.

The later Codex P1 delivered on exact head `931664205e82e51b64dc6c83f91091599fe8825b` is also valid: pre-persistence freshness alone leaves a stale-after-create/before-dispatch TOCTOU path. This correction closes that class by making canonical freshness part of the atomic queued-job execution claim before script invocation.

After this correction is published, all earlier exact-head CI/review evidence is stale for merge authority. The new exact head must pass fresh deterministic gates and receive an independent peer/GLM verdict that explicitly confirms preview, final pre-persistence create, and atomic queued-job claim freshness enforcement surfaces are all authorized without introducing a parallel authority.

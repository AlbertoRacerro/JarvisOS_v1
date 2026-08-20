# 058c — fresh readiness correction: dirty target transition, source navigation, and stale-claim outcome

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-2026-08-20-fresh.md` and all prior PR #317 readiness corrections  
Reason: final exact-head review found three remaining authority gaps: eligible-candidate switching with dirty object-scoped working edits was undefined; linked-Parameter Inspect content lacked the required direct navigation to its real Engineering Data authority; and stale-at-claim runner failure bookkeeping was not deterministic enough for clients/tests.

This correction is part of the 058c readiness decision. Where it conflicts with earlier readiness wording, this file governs. It changes no runtime code and does not promote `058c` from `planned`.

## 1. Dirty object-target transition

The three CAD-link-adopted Geometry fields are object-scoped working values tied to one exact semantic-source identity. Generic reviewed-047 inputs remain ordinary model-configuration state and are not object-scoped merely because a BLUECAD selection changes.

The existing 071b controller remains the sole mutable working-state owner. Implementation must associate the adopted object baseline/draft with the exact semantic target identity needed to prevent cross-object reuse: workspace, candidate, artifact, viewer session/generation, canonical `partId`/`partKind`, and `semantic_source` source simulation/model identity.

### 1.1 Clean A → B switch

If object-scoped Geometry fields for eligible target A are clean relative to A's adopted baseline, selecting a distinct eligible target B may immediately retire A's clean object baseline and adopt B's canonical snapshot after the full stale/provenance gate succeeds. Generic model-configuration working values retain their normal 071b state.

### 1.2 Dirty A → B switch

If any object-scoped Geometry field for eligible target A is dirty when the current 092 selection moves to a distinct target B:

1. A immediately loses active semantic edit/run authority because it is no longer the current 092 target.
2. B does **not** adopt its snapshot over A's dirty object draft automatically.
3. The existing controller retains A's dirty object draft only as one transient pending previous-target draft. This is not a durable per-object cache, variant store, history system, or second working-state owner.
4. Properties for the new selection enters a deterministic transition-blocked state. It must not label A's values as B, expose them as B-effective values, or allow preflight/run using A's object-scoped draft while B is current.
5. The operator is told that unsaved object changes from A must be resolved before B can become the editable semantic target. The required destructive action is explicit: **Discard previous object changes and load selected object**. Only that action clears A's object-scoped dirty draft and permits B snapshot adoption.
6. If the operator re-selects the exact still-current/available A target before discarding, the retained A draft becomes active again with its existing dirty/Undo/Revert semantics. No server mutation is required.
7. If A becomes unavailable because workspace/candidate/artifact authority changes, the pending draft remains non-executable and may be discarded explicitly; V0 is allowed to lose it on application teardown under the existing transient-working-state boundary, but it may not silently apply it to another object.
8. Repeated reads/refetches for the same target/source never erase dirty edits.

This is the minimum safe transition contract. Do not add a multi-object draft map, durable draft persistence, variant history, hidden autosave, scene-owned state, or 006b behavior.

### 1.3 Transition acceptance

Merge-blocking cases:

- clean eligible A → eligible B adopts B's exact source snapshot and does not retain A object values;
- dirty eligible A → eligible B does not discard A silently and does not expose/run A values as B;
- while transition-blocked, preflight/run for B is unavailable until the previous object draft is explicitly discarded;
- explicit discard then adopts B's exact canonical source snapshot and resets only the retired A object-scoped draft, not unrelated generic working configuration;
- reselecting exact A before discard restores A's pending dirty object draft;
- late A/B aggregate responses cannot resolve or overwrite a newer transition;
- no transition action mutates canonical Parameters/CAD links, registers a model, creates a run, calls Jarvis/provider paths, or creates durable draft state.

## 2. Direct navigation to linked Parameter authority

The base 058c definition requires source navigation to target the real authority. A linked Parameter therefore cannot be represented only as inert source text.

For an object-semantic field whose effective/baseline binding contains a verified same-workspace canonical `source_parameter_id`, L1 Inspect must expose a keyboard-reachable **Open source** action.

### 2.1 Exact navigation contract

The minimum existing-shell transport is:

`/engineering-data?kind=parameter&id=<URL-encoded canonical parameter id>`

Rules:

1. The action uses the canonical `source_parameter_id` already verified by the semantic-source/binding authority. It never searches by label, symbol, name, value, unit, or nearest match.
2. Navigation is same-origin and uses the existing application `navigate` function/history behavior; no new router or backend route is added.
3. `EngineeringData` consumes `kind=parameter&id=<id>` only as a read-side selection request for the current workspace. After the current workspace's Parameter list loads, it enables the Parameter kind if necessary and selects exactly `parameter:<id>` if that row exists in the current workspace.
4. If the exact Parameter is absent/inaccessible, Engineering Data shows a bounded truthful source-unavailable state and does not select an approximate record.
5. A later user search/filter change behaves normally; the deep-link request grants no mutation, promotion, lifecycle, or freshness authority.
6. Browser back/forward remains functional because the target is carried in the existing route query string.
7. Raw source identity may appear in the URL/Audit transport, but normal Properties presentation remains the semantic source label plus the human **Open source** action.

### 2.2 Minimum allow-list addition

Implementation may additionally touch only:

- `frontend/src/pages/EngineeringData.tsx` — consume the exact `kind=parameter&id=` read-side target and select/show the exact current-workspace Parameter;
- `frontend/src/components/engineering-data/engineeringDataState.ts` only if a small pure helper is useful for exact target selection; no new state framework;
- focused Engineering Data / Properties navigation tests.

`frontend/src/App.tsx` and `frontend/src/components/engineering/EngineeringProperties.tsx` are already authorized by prior corrections and may pass/use the existing `navigate` callback for this bounded action. No new backend API, record mutation, Engineering Data redesign, 098 lifecycle behavior, or global navigation framework is authorized.

### 2.3 Navigation acceptance

Merge-blocking cases:

- linked Geometry field → Open source navigates to `/engineering-data?kind=parameter&id=<exact id>` and selects exactly that Parameter after current-workspace data loads;
- duplicate labels/names do not affect selection;
- wrong-workspace/missing ID produces truthful unavailable state, not nearest-record fallback;
- keyboard activation and browser back/forward work;
- navigation performs zero engineering mutation, provider call, run creation, or hidden refresh-side persistence.

## 3. Deterministic stale-at-claim runner outcome

The prior runner-freshness correction correctly requires canonical freshness inside the atomic queued-job claim before script invocation, but delegating status/code/message choice to implementation leaves the persisted/returned failure contract ambiguous.

For a persisted queued job whose immutable stored input snapshot contains a linked Parameter that is no longer admissible at the atomic claim boundary because it is canonically stale, superseded, missing, cross-workspace, or otherwise fails the already-required linked-source integrity check, the outcome is frozen as follows.

### 3.1 Exact terminal contract

The single caller that atomically owns the still-queued job must transition the job and simulation run to the existing terminal status:

`failed`

with exactly:

- error code: `runner_linked_parameter_unusable`;
- error message: `A linked Parameter is no longer usable for this queued run.`

The existing failure representation is reused:

- `RunnerJobRunResponse.output = null`;
- `RunnerJobRunResponse.error = {"code":"runner_linked_parameter_unusable","message":"A linked Parameter is no longer usable for this queued run."}`;
- `simulation_runs.output_payload` is the existing canonical failed payload with `status="failed"` and the same error code/message;
- event type is existing `RunnerJobFailed` with existing payload shape including `simulation_run_id`, `status="failed"`, and `error_code="runner_linked_parameter_unusable"`;
- `completed_at`/job `updated_at` use the existing failed-job bookkeeping.

The stale-source rejection and conditional ownership of `queued -> failed` must be one SQLite claim transaction. No `RunnerJobStarted` event is emitted, no `running` transition occurs, no script/input-file execution side effect is performed, and `execute_python_script` is never invoked.

A concurrent second `/run` caller that did not win the queued claim receives the existing `runner_job_not_queued` safety error and cannot execute or rewrite the terminal failure. Retrying the already-failed job remains non-executable under existing runner semantics; a new valid run intent/snapshot is required.

This does not add a new runner lifecycle state, event family, response type, or cancellation subsystem.

### 3.2 Claim-outcome acceptance

Merge-blocking cases:

- fresh-at-create then stale-before-claim produces terminal `failed` with the exact code/message above and zero script invocation;
- persisted simulation-run failed payload and `RunnerJobFailed` event carry the same exact error code and status;
- no `RunnerJobStarted` event is emitted for the rejected job;
- two concurrent `/run` calls cannot both mutate/execute the job; one owns the stale failure, the other receives existing not-queued behavior;
- a later retry cannot execute the failed snapshot;
- fresh linked sources preserve current queued→running→terminal execution behavior.

## 4. Review consequence

The final current-head findings concerning dirty eligible-candidate switching, linked-source navigation, and stale-claim terminal bookkeeping are materially valid. This correction closes them without adding product authority beyond 058c: one transient previous-target draft in the existing 071b controller, one exact read-side Engineering Data deep-link, and one exact mapping onto the runner's existing failed-job machinery.

All gate/review evidence from earlier heads is stale for merge authority. The new exact head requires fresh deterministic CI and a new independent non-mutating peer/GLM verdict covering this file together with all earlier PR #317 corrections. No further Codex review is authorized on PR #317.
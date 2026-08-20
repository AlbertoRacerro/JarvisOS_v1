# 058c — SCENE-SEMANTICS-A1 readiness final correction

Date: 2026-08-20  
Applies to: all earlier 058c readiness records on PR #315  
Reason: close the final exact-head review findings on guarded execution reachability and the absence of a second authoritative production model option.

This file is part of the 058c readiness authority. Where it conflicts with any earlier 058c readiness record, **this file wins**. Untouched object-applicability, source-freshness, scene/stale-safety, formula non-fabrication, migration, 071b ownership, 092 ownership, downstream deferral and non-goal rules remain unchanged.

## 1. The semantic companion must be executable through the existing guarded runner boundary

The prior production-path correction authorizes one additive schema-v3 semantic companion for the reviewed bundled 047 M0 executable, but normal runner creation/execution is additionally protected by `backend/app/modules/runner/guarded_service.py::_require_exact_bundled` / `_is_exact_bundled`.

Current runtime recognizes the legacy reviewed calc profiles by exact server-known tuples including version label, script digest and canonical input-contract digest. A new semantic companion has a distinct version label and schema-v3 contract digest, so registration/listing alone is insufficient: without an exact guard update, the companion can be visible and previewable yet fail before normal runner execution.

The minimum implementation therefore additionally authorizes:

- `backend/app/modules/runner/guarded_service.py` only to recognize the single new semantic 047 companion as another **exact server-known bundled profile**;
- focused guarded-runner tests proving that recognition is exact and does not create a generic schema-v3 or label-based bypass.

Required guard semantics:

1. the semantic companion is accepted only when its exact distinct version label matches the readiness-authorized companion label, its stored script digest equals the existing reviewed 047 script digest, and its stored input-contract digest equals the canonical digest of the new checked-in schema-v3 companion contract;
2. arbitrary schema-v3 `calc_v0` rows remain rejected;
3. changing only label, only contract digest, only script digest, or implementation kind must fail closed;
4. the existing legacy 047 tuple and every pre-058c exact-bundled profile remain unchanged;
5. no wildcard, family-key, schema-version-only or frontend-controlled criterion may grant execution authority.

The final deterministic acceptance must include a successful normal create + run of the semantic companion through `guarded_service`, not merely registration/listing/preview. The run must use the same exact server-owned execution path as other bundled reviewed models and must not bypass the existing runner policy, request-key, preflight or persistence boundaries.

This is a bounded allow-list extension, not a new execution subsystem or provider path.

## 2. No second authoritative engineering option exists today; do not invent one

Fresh runtime inspection and review establish that the currently justified production schema-v3 path is exactly one semantic companion for reviewed 047 M0. The repository does not currently contain a second authoritative bundled implementation that is both:

- a genuine alternative engineering model for the same `model_family_key`; and
- production-reachable through the existing guarded registration/execution boundary.

Creating a duplicate companion with the same executable under a different label would fabricate a model alternative. Grouping unrelated reviewed models into one family would fabricate engineering semantics. Public registration of arbitrary `calc_v0` implementations is deliberately rejected by the guarded product boundary. None of those routes is authorized.

Therefore 058c V0 must **not claim or render a mutually-exclusive engineering family selector unless at least two authoritative object-applicable schema-v3 implementations with the same family key actually exist**.

For the initial production 047 companion:

- one option in a family is valid semantic metadata but is rendered as the active model identity/label, not as a fake choice control;
- the existing generic 071b implementation selector remains available according to its pre-058c behavior for generic model configuration, but unrelated implementations are not promoted into a semantic family by frontend inference;
- no second 047 option is synthesized for acceptance;
- no A/B family-switch behavior is advertised as current product capability.

## 3. Superseded model-choice acceptance from earlier readiness records

Because current runtime lacks two authoritative options in one semantic family, the earlier readiness requirements that specifically assume a real semantic A/B family choice are **prepared but not implementation-now** for 058c V0.

The following earlier requirements are therefore superseded as merge-blocking V0 acceptance:

- browser case requiring `two v3 options in one family`;
- A → B → A semantic-family inactive-value restoration;
- semantic-family A → B → Undo;
- semantic-family A → B → `Revert all`;
- per-implementation semantic-family baseline retention across successful Run A → B → A;
- initial pre-first-run baseline semantics whose only purpose is a new 058c family selector.

These contracts remain the compatibility target for a later accepted slice/readiness once a second genuine engineering option exists. That later work must reuse 071b working revision/Undo/Revert authority and must not create a second state owner.

This deferral does **not** weaken existing 071b behavior or permit destructive state loss. 058c V0 must preserve current generic implementation switching behavior and must not regress existing dirty/preflight/run semantics. It simply does not add unexercisable family-choice machinery now.

## 4. Corrected production V0 acceptance

The merge-blocking 058c V0 acceptance is now:

1. a fresh workspace can register the distinct schema-v3 semantic 047 companion through the existing server-owned bundled path;
2. the companion is returned by normal model-implementation reads with valid schema-v3 semantics;
3. `guarded_service` accepts that exact companion tuple and a normal runner job can be created and successfully executed;
4. near-miss or arbitrary schema-v3 `calc_v0` implementations remain rejected by the exact-bundled guard;
5. legacy bundled 047 bytes, label, contract digest, CAD-LINK identity checks and execution remain unchanged;
6. exact resolved `tube_run` + semantic companion exposes only `tube_length`, `tube_inner_diameter`, and `tube_outer_diameter` as selected-object `Geometry` properties;
7. the six remaining reviewed 047 inputs have `applicable_part_kinds = []`, remain reachable as generic model configuration and remain required by preview/run;
8. omitted variable applicability is invalid; empty applicability means generic/non-object-owned; non-empty kinds must be exact subsets of implementation applicability;
9. no category/name/unit/mesh/scene inference creates object ownership;
10. a one-option semantic family is shown truthfully without a fake selector or fabricated alternative;
11. if future/test fixture data contains two valid same-family options, any parser/rendering logic added now must fail safely and must not claim production support unless the current implementation actually covers it; broad family-choice state machinery is not required in V0;
12. superseded linked Parameters fail closed in preview and direct runner creation before run/job persistence, with explicit relink required and no silent replacement;
13. schema-v1/v2 generic models remain usable and unchanged;
14. no formula/`fx` evidence is invented.

## 5. Corrected browser acceptance

Final implementation browser evidence must use the real production semantic companion and prove:

- generic 071b Properties remains usable with no semantic scene target;
- unresolved/ambiguous/stale scene targets never become editable semantic targets;
- a resolved real `tube_run` plus the semantic 047 companion shows the three CAD-LINK-proven Geometry rows only;
- the six generic required inputs remain reachable outside selected-object groups;
- a one-option semantic family is presented as truthful model identity without a fake dropdown/alternative;
- linked superseded Parameter becomes blocker/not-ready, is not auto-replaced, and explicit relink recovers readiness;
- semantic selection/model presentation performs no provider/Jarvis mutation or implicit Run;
- 200%/compact, keyboard/focus, overflow, light/dark/system and reduced-motion invariants remain usable.

The browser harness must not create a fake second engineering option merely to satisfy obsolete A/B cases.

## 6. Final implementation allow-list delta

In addition to the still-valid earlier allow-list, implementation may touch:

- `backend/app/modules/runner/guarded_service.py` for the exact single-companion bundled execution tuple;
- focused guarded-runner tests proving exact acceptance/rejection and one successful companion execution.

The earlier production companion registration/contract paths and superseded-Parameter validation paths remain authorized.

No general model registry expansion, arbitrary `calc_v0` admission, second fake 047 option, model-family database, semantic service, SQL migration, provider path, formula engine, 092 rewrite, 097/098/006b/058b, Notes, routine 062 grading or global visual-identity change is authorized.

## 7. Readiness verdict after this correction

With this correction, 058c V0 is intentionally narrower but production-real:

- object-semantic grouping is exercised by one genuine reviewed model/object relationship;
- generic required runner inputs remain available;
- linked source freshness is enforced server-side;
- the semantic companion can actually execute through the current guarded product path;
- model-choice UI is not fabricated before the repository contains a genuine second engineering option;
- formula/derived semantics remain deferred rather than guessed.

That is the minimum implementation that creates real operator value while preserving 071b/092 authority and YAGNI.
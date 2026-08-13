# 085 BLUECAD-WORKBENCH-2 — async guard readiness addendum (2026-08-13)

This addendum is normative for the 085 readiness decision in `085-readiness-2026-08-13.md` and tightens, without broadening, the frozen request-race, GLB lifecycle, keyboard-focus, and required presentation-state contracts. The main readiness record links this addendum so implementers following `STATUS.md` traverse the complete authority chain.

## Validation-report completion guard

Validation-report JSON loading is a separate asynchronous request and must use the same production generation/context acceptance authority as aggregate detail. A request must be bound to the workspace, candidate, validation-report artifact and request generation that started it. A completion from an old workspace, candidate, report artifact, refresh generation or unmounted workbench must not replace the current candidate's validation checks, validation-detail diagnostic, message state or visible loading state.

`workbenchState.ts` must own this acceptance decision; it may not be an ad hoc React-only check. `workbenchStateHarness.ts` must execute a case where candidate A's validation report completes after candidate B becomes current and prove that A's completion is rejected without changing B's checks, diagnostics or messages. `scripts/check_bluecad_workbench.py` must verify that the production workbench routes validation-report acceptance through the same helper.

## Same-context stale-generation guard

Generation identity is authoritative even when workspace and candidate identity later return to the same values. A completion from request generation N must be rejected after generation N+1 has become current even if the current workspace/candidate pair again equals the pair captured by N, including A→B→A navigation and manual Refresh overlapping a mutation-triggered canonical reload. Context equality is therefore necessary but not sufficient for acceptance.

`workbenchState.ts` must compare the monotonic request generation in addition to the captured workspace/candidate context. `workbenchStateHarness.ts` must execute at least one same-context race where generation N completes after N+1, prove N is rejected, and prove N+1 is accepted. This case is beta-blocking because otherwise older discovery or aggregate data can overwrite newer canonical state while every ID comparison still matches.

## GLB stale error-callback guard

Every GLTF load, including its error callback, must be bound to the artifact/load generation that started it. If an old artifact's loader error arrives after a replacement artifact is current, or after the viewer unmounts, the callback must be ignored and must not overwrite the current artifact's message or visible status.

The existing 085 requirement to dispose owned scene resources on replacement/unmount and to dispose late successful loads remains unchanged. Deterministic regression proof plus browser/manual evidence must now cover all three cases: artifact replacement cleanup, late stale successful-load disposal, and stale/unmounted loader-error rejection. `scripts/check_bluecad_workbench.py` must fail if the viewer lacks the stale/unmounted error-callback guard.

## Candidate focus-recovery guard

When archive or archived filtering removes the keyboard-focused selected candidate row, focus must move deterministically to the newly selected replacement row. If no candidate remains, focus must move to a stable navigator section or empty-state target that is itself keyboard reachable. Focus may not fall to `document.body`, disappear, or remain attached to a removed row.

The deterministic selection helper remains the authority for which candidate replaces the removed selection; the rendered navigator must apply focus to that resolved target after the list transition. `scripts/check_bluecad_workbench.py` plus browser/manual evidence must prove both replacement-row focus and no-candidate focus recovery. This is lifecycle parity required by the selected 085 specification, not a new navigation model.

## Required discovery and mutation presentation states

The 085 migration must preserve the legacy workbench's usable failure and empty-state behavior rather than proving only the happy path. Deterministic rendering/source contracts plus browser/manual evidence must cover at minimum:

- no workspaces available;
- workspace discovery failure;
- candidate-list loading;
- candidate-list failure;
- a selected workspace with no candidates;
- mutation failure without falsely claiming success or corrupting canonical state;
- an archived-only workspace while archived rows are hidden, with a usable empty-state path to reveal archived candidates.

These states must remain distinct from aggregate-detail failures. A failure in candidate discovery must not fabricate stale detail, while a detail failure must not erase otherwise valid discovery state. Mutation failure must leave the backend result authoritative, surface a bounded diagnostic to the operator, and preserve/reload current canonical state according to the main readiness rules.

## Gate impact

All cases in this addendum are beta-blocking acceptance criteria. A conforming 085 implementation cannot claim readiness completion or merge while an older generation can overwrite newer same-context state, a secondary asynchronous path can overwrite state belonging to a newer selection/artifact, archive/filter transitions can strand keyboard focus, or mandatory discovery/mutation failure states are absent. No backend, schema, dependency, workflow, provider, credential, budget, egress or global visual-identity change is authorized by this addendum.
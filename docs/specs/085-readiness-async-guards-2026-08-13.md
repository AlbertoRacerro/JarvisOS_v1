# 085 BLUECAD-WORKBENCH-2 — async guard readiness addendum (2026-08-13)

This addendum is normative for the 085 readiness decision in `085-readiness-2026-08-13.md` and tightens, without broadening, the frozen request-race, GLB lifecycle, and keyboard-focus contracts. The main readiness record must link this addendum so implementers following `STATUS.md` traverse the complete authority chain.

## Validation-report completion guard

Validation-report JSON loading is a separate asynchronous request and must use the same production generation/context acceptance authority as aggregate detail. A request must be bound to the workspace, candidate, validation-report artifact and request generation that started it. A completion from an old workspace, candidate, report artifact, refresh generation or unmounted workbench must not replace the current candidate's validation checks, validation-detail diagnostic, message state or visible loading state.

`workbenchState.ts` must own this acceptance decision; it may not be an ad hoc React-only check. `workbenchStateHarness.ts` must execute a case where candidate A's validation report completes after candidate B becomes current and prove that A's completion is rejected without changing B's checks, diagnostics or messages. `scripts/check_bluecad_workbench.py` must verify that the production workbench routes validation-report acceptance through the same helper.

## GLB stale error-callback guard

Every GLTF load, including its error callback, must be bound to the artifact/load generation that started it. If an old artifact's loader error arrives after a replacement artifact is current, or after the viewer unmounts, the callback must be ignored and must not overwrite the current artifact's message or visible status.

The existing 085 requirement to dispose owned scene resources on replacement/unmount and to dispose late successful loads remains unchanged. Deterministic regression proof plus browser/manual evidence must now cover all three cases: artifact replacement cleanup, late stale successful-load disposal, and stale/unmounted loader-error rejection. `scripts/check_bluecad_workbench.py` must fail if the viewer lacks the stale/unmounted error-callback guard.

## Candidate focus-recovery guard

When archive or archived filtering removes the keyboard-focused selected candidate row, focus must move deterministically to the newly selected replacement row. If no candidate remains, focus must move to a stable navigator section or empty-state target that is itself keyboard reachable. Focus may not fall to `document.body`, disappear, or remain attached to a removed row.

The deterministic selection helper remains the authority for which candidate replaces the removed selection; the rendered navigator must apply focus to that resolved target after the list transition. `scripts/check_bluecad_workbench.py` plus browser/manual evidence must prove both replacement-row focus and no-candidate focus recovery. This is lifecycle parity required by the selected 085 specification, not a new navigation model.

## Gate impact

These cases are beta-blocking acceptance criteria. A conforming 085 implementation cannot claim readiness completion or merge while a secondary asynchronous path can overwrite state belonging to a newer selection/artifact, or while archive/filter transitions can strand keyboard focus. No backend, schema, dependency, workflow, provider, credential, budget, egress or global visual-identity change is authorized by this addendum.

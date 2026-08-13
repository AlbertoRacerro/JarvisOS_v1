# 085 BLUECAD-WORKBENCH-2 — async guard readiness addendum (2026-08-13)

This addendum is normative for the 085 readiness decision in `085-readiness-2026-08-13.md` and tightens, without broadening, the frozen request-race, GLB lifecycle, keyboard-focus, lifecycle-parity, and required presentation-state contracts. The main readiness record links this addendum so implementers following `STATUS.md` traverse the complete authority chain.

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

## Successful lifecycle mutation parity

Failure and stale-completion guards are not sufficient proof that the canonical lifecycle still works. The 085 implementation must exercise successful current-context create, archive, and promote flows against the existing clients and canonical reload path.

Required proof is beta-blocking:

- create: a backend-confirmed create must trigger canonical discovery reload and select the returned candidate only after that candidate is observable in the current workspace; it must not synthesize a local candidate row or claim success from request dispatch alone;
- archive: a backend-confirmed archive must trigger canonical reload; when archived rows are hidden the archived candidate disappears and selection/focus moves deterministically to the resolved replacement or empty-state target, while `show archived` may reveal the canonical archived row again;
- promote: a valid, unpromoted candidate must invoke the existing canonical promotion client, reload canonical candidate detail, and expose the returned promotion/decision linkage without fabricating local promotion state.

The executable state helper/harness must prove the current-context completion transitions used for create and at least one candidate-targeted mutation, in addition to the already-required stale-completion rejection. Deterministic source/checker proof must verify that the production workbench actually wires create, archive, and promote to the existing API clients and canonical reload path. Browser/manual acceptance must exercise all three successful actions. A no-op button, optimistic-only mutation, locally fabricated success, or success path that does not re-read canonical state is a beta-blocking failure.

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

## Parked-candidate diagnostic parity

A parked candidate is a valid lifecycle outcome, not an empty or generic-error state. When the canonical candidate exposes `parked_reason`, the native workbench must render that reason as operator-readable lifecycle diagnostic context and preserve the complete ordered attempt trail, including attempt errors already required by the main readiness record. A parked candidate with no GLB must therefore explain why geometry is unavailable rather than collapsing to a bare `no GLB` message.

Deterministic presentation/source proof plus browser/manual evidence must include at least one parked candidate with non-empty `parked_reason`, zero usable GLB artifact, and multiple attempts. `scripts/check_bluecad_workbench.py` must fail if the native migration drops `parked_reason` from the visible lifecycle/diagnostic surface or hides the attempt trail merely because the candidate is parked.

## Structured validation-detail readability

A valid canonical validation report may contain structured check detail such as `{actual, declared, rel_err, rel_tol}` rather than only scalar text. The native workbench must preserve the 006c readability contract: structured detail must be formatted into stable human-readable labeled values, must not render as raw unbounded JSON or `[object Object]`, and must never crash when optional keys are absent or additional keys are present.

Deterministic presentation/source proof plus browser/manual evidence must include at least one well-formed structured validation detail containing `actual`, `declared`, `rel_err`, and `rel_tol`, and one irregular-but-valid object shape. `scripts/check_bluecad_workbench.py` must fail if the native workbench removes the readable structured-detail formatter or falls back to unsafe implicit object stringification for validation detail.

## Duplicate-brief reveal and focus parity

Duplicate-brief remains a frontend-only creation-form transition, but lifecycle parity includes the existing one-click editing affordance. Invoking duplicate-brief must not only copy the source brief into the creation form: if the creation form lives in a shell region that is currently closed or collapsed, the action must reveal/open the owning region through the existing shell contribution/control seam, make the populated form visible, and move keyboard focus to the editable brief field without pointer-only recovery. If layout requires scrolling within a bounded local pane, the focused field must be brought into view without introducing page-level horizontal overflow.

The executable state harness continues to prove that duplicate-brief performs no backend mutation or silent clone. In addition, deterministic rendering/source proof plus browser/manual evidence must prove closed-region invocation, region reveal, populated value, focus transfer to the textarea/input, and retained keyboard operability. `scripts/check_bluecad_workbench.py` must fail if duplicate-brief can leave the populated form hidden or omit a deterministic focus/reveal path.

## Gate impact

All cases in this addendum are beta-blocking acceptance criteria. A conforming 085 implementation cannot claim readiness completion or merge while successful create/archive/promote lifecycle actions are unwired or locally fabricated; a parked candidate loses its canonical reason or attempt trail; an older generation can overwrite newer same-context state; a secondary asynchronous path can overwrite state belonging to a newer selection/artifact; archive/filter transitions can strand keyboard focus; structured validation detail becomes unreadable; duplicate-brief can leave its editable form hidden or unfocused; or mandatory discovery/mutation failure states are absent. No backend, schema, dependency, workflow, provider, credential, budget, egress or global visual-identity change is authorized by this addendum.
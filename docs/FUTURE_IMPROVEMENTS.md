# Future Improvements — advisory engineering parking lot

Status: advisory only; no implementation, queue, priority, dependency, readiness, merge, or roadmap authority.

`docs/specs/STATUS.md` is the sole live authority for JarvisOS work state and implementation authorization. An item in this file is not `planned`, `ready`, queued, prioritized, or approved for implementation. A parked item becomes executable only after the normal definition/specification/readiness/`STATUS.md` lifecycle grants that authority.

## Purpose

Preserve concrete, independently useful observations that are discovered during implementation, semantic review, or the bounded pre-merge quality check but are genuinely outside the accepted scope. This prevents useful evidence from being lost without contaminating the current slice or turning review into speculative refactoring.

This file is not a second backlog. Do not use it to sequence work, infer dependencies, reserve identifiers, justify implementation, or delay an otherwise valid merge.

## Pre-merge classification

For every observation that might affect the merge decision, classify it before acting:

1. **FIX** — a material correctness, security, maintainability, scope, or acceptance defect inside the current accepted correctness envelope. Repair the smallest causal issue now. A material defect may not be parked to bypass a merge gate.
2. **PARK** — a concrete, independently useful improvement that is genuinely outside the current accepted scope. Record it here if preserving it has clear future value; it does not block merge once current objective gates pass.
3. **DROP** — a vague idea, cosmetic preference, speculative refactor, elegance-only thought, or duplicate of live/parked work. Do not create registry noise.

After objective exact-head gates pass and no FIX item remains, the bounded semantic quality check should stop: PARK worthwhile out-of-scope improvements, DROP low-value ideas, and merge rather than chase perfection.

## Entry rules

Before adding an entry:

- deduplicate against this file and live `docs/specs/STATUS.md` / accepted specs;
- verify the observation against fresh enough repository evidence;
- do not assign priority, queue position, dependency semantics, readiness, or implementation authority;
- do not manufacture a dedicated PR solely to preserve a low-value note;
- prefer carrying a worthwhile entry only in an already-authorized bounded docs/reconciliation mutation.

Each entry must contain:

- stable short ID/title;
- origin: spec/PR/exact head or master context;
- concrete observation;
- why it is outside the accepted current scope;
- expected benefit or risk reduced;
- likely affected files/components when known;
- optional freshness invalidators.

## Entries

_No parked improvements recorded yet._

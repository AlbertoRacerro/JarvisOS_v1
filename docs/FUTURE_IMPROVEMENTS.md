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

### F10 — calc_v0 artifact/proposal partial-finalization — PARK

- **Origin:** fresh master `23bee946c06307ef77087ce7f3212424033fa831`; accepted spec 043 / merged PR #52.
- **Observation:** `backend/app/modules/runner/service.py` intentionally registers and commits the validated `result.json` run artifact before calling the spec-040 batch facade that creates calc-origin Parameter proposals. If that later facade call fails, `_finish_failed(...)` marks the runner job and simulation run failed while the already-registered artifact remains queryable for that exact run.
- **Disposition:** PARK / non-blocking. This is the ordering explicitly frozen by spec 043: artifact registration precedes the memory-facade call, while the all-or-nothing guarantee applies to Parameter proposal creation. Fresh evidence does not prove a current accepted-requirement violation, current in-scope bypass, regression, or material P0/P1 correctness/security defect beyond that accepted ordering.
- **Expected benefit if revisited:** a future product requirement could choose stronger finalization/visibility semantics for failed calc runs, but that would be a new contract rather than a repair of accepted 043 behavior.
- **Likely surface:** `backend/app/modules/runner/service.py`, calc-run artifact visibility, and focused `backend/tests/test_python_runner_calc_v0.py` failure fixtures.
- **Freshness invalidators:** reopen only if a concrete consumer treats failed-run artifacts as successful/authoritative output, a new accepted contract requires transactional artifact+proposal finalization, or evidence shows stale artifacts can cross an existing authority/promotion boundary.

### F11 — retire the `tools/` Tool/ToolResult stub in favor of the 145 tool contracts — PARK

- **Origin:** spec 145 / FOUNDATION-CONTRACTS-1 implementation on base `b623fa863b0e58739a4664f7aadad0202f3f8126`.
- **Observation:** `backend/app/modules/tools/base.py` still defines an unused placeholder `Tool` protocol and `ToolResult(status, output)` dataclass (only referenced by `tools/registry.py`). 145 freezes the governed `StructuredToolCall`/`StructuredToolResult` in `backend/app/modules/ai/agent_contracts.py`.
- **Disposition:** PARK / non-blocking. The stub is not a wire contract and has no product consumer; replacing or deleting it belongs with the H-146 capability/tool broker that will actually register executable tools.
- **Expected benefit if revisited:** one tool-exchange vocabulary; removes a misleading second `ToolResult` shape before any tool is registered.
- **Likely surface:** `backend/app/modules/tools/`, the H-146 broker.
- **Freshness invalidators:** drop if H-146 deletes or rewrites `app/modules/tools/`.

### F12 — restart-durable or cross-process resource leases — PARK

- **Origin:** spec 145 / FOUNDATION-CONTRACTS-1 resource-lease decision on base `b623fa863b0e58739a4664f7aadad0202f3f8126`.
- **Observation:** 145 freezes `RuntimeResourceSnapshot`, `ResourceReservationRequest`, `ResourceLease` and the pure `grant_lease`/`end_lease` generation+version CAS state machine in `backend/app/modules/local_ai/resource_contracts.py`, with no SQLite table. Every local GPU dispatch currently happens inside the single backend process through `run_ai_task`; after a restart the arbiter re-observes runtime truth rather than trusting surviving rows.
- **Disposition:** PARK / non-blocking. No accepted requirement needs a lease to outlive the backend process, and no existing owner arbitrates local GPU use.
- **Expected benefit if revisited:** correct admission if L-147/H-146 evidence shows admission spanning independent processes (for example a solver or worker that allocates GPU/RAM outside the backend) or restart-surviving occupancy that runtime observation cannot see.
- **Likely surface:** a K-owned additive migration storing exactly the frozen lease fields (id, request/owner/correlation, resources, snapshot generation, state, version, granted/expires/ended timestamps, release reason), with `WHERE id=? AND state=? AND version=?` transitions and startup reconciliation against observed runtime state.
- **Freshness invalidators:** reopen only with concrete L/H evidence of cross-process GPU/RAM admission or unobservable restart-surviving occupancy.

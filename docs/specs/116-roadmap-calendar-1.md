# 116 ROADMAP-CALENDAR-1

Status: planning contract; implementation remains unauthorized until canonical readiness.

Exact derivation base: `4dadba46e6d1220f4cc6235887c77d792e750efb`.
Governing queue authority: `docs/specs/100c-queue-rederivation-2026-08-28.md`.
Approved product reference: `docs/design-references/development-beta/DEVELOPMENT_BETA_APPROVED_2026-08-27.md`.

## Outcome

Make Development > Roadmap a truthful planning owner and Development > Roadmap > Calendar a truthful time-allocation owner.

Roadmap owns durable work-item identity, lifecycle, dependencies, constraints and deterministic done-when gates. Calendar owns actual scheduled time blocks down to dates/times/time zones. They are linked but are not the same state: a Roadmap window never implies occupied Calendar time, and one Roadmap item may link to zero, one or many Calendar blocks.

The standalone Board concept remains rejected. Execution status is a projection of the same Roadmap items under Timeline.

## Fresh-owner audit

Current `backend/app/modules/events` is an audit/event-log facility: `EventRecord` carries generic event metadata and `log_event()` appends redacted JSON payloads. It is not a mutable Roadmap/Calendar state owner and must not be promoted into one by encoding work items or schedules as opaque event payloads.

No current exact-master owner was found for stable Roadmap work items or real Calendar time allocations. Therefore 116 may introduce the minimum additive Development-domain persistence required for those two concepts, while continuing to use the existing event service only for audit evidence of accepted mutations.

The existing Development frontend routes/references already reserve Roadmap and Calendar presentation. 116 activates only the accepted Roadmap/Calendar semantics; Brainstorm remains 117.

## Canonical state contracts

### Roadmap work item

A Roadmap item has a stable workspace-scoped identity and at minimum:

- title and optional description;
- type from the bounded product vocabulary (`Task`, `Work package`, `Milestone`, `Investigation`, `Validation`, `Decision`, `Procurement`, `Manufacturing`, `Meeting/Review`);
- lifecycle status (`Planned`, `Ready`, `In progress`, `Blocked`, `Done`, `Cancelled`);
- priority (`Critical`, `High`, `Normal`, `Opportunity`);
- optional project-window start/end date;
- optional domain, owner, effort estimate, tags and notes;
- zero or more exact links to existing canonical objects by typed stable ref;
- zero or more dependency edges between Roadmap items;
- optional cannot-start-before / must-finish-before constraints;
- optional explicit `done_when` criterion;
- immutable creation provenance and mutation/audit timestamps.

Roadmap dependencies must reject cross-workspace references, self-dependency and cycles. Deleting an item with dependents or linked Calendar blocks must fail closed unless the caller explicitly resolves those references through a bounded accepted operation; silent cascade deletion is forbidden.

Transition to `Done` must be deterministic. If a declared `done_when`/acceptance gate is unsatisfied or cannot be evaluated, ordinary completion is refused. Any future acknowledged override must be an explicit typed operation with actor/reason/audit evidence; 116 does not authorize model-owned bypass.

Jarvis-created changes remain proposals. Manual operator mutations may COMMIT through the Development owner. No provider/model call is required to create, edit, schedule or transition an item.

### Calendar allocation

A Calendar allocation has its own stable workspace-scoped identity and at minimum:

- title and bounded event type;
- start and end instants plus an explicit IANA time-zone identifier used for operator interpretation;
- optional all-day/deadline semantics only when unambiguous;
- optional link to exactly one Roadmap item; a Roadmap item may have many allocations;
- optional description, priority, domain, location/meeting link, reminder metadata and tags;
- immutable creation provenance and mutation/audit timestamps.

Persist an unambiguous instant representation plus the time-zone identity needed to round-trip local wall-clock meaning. Reject nonexistent/ambiguous local times unless the request resolves the offset explicitly; never guess DST folds/gaps.

Calendar overlap is allowed by default because concurrent commitments can be truthful data. Availability/conflict presentation is a projection, not an implicit mutation or automatic rescheduler.

Deleting or editing a Calendar block never changes the parent Roadmap item's lifecycle/window. Editing a Roadmap window never silently moves Calendar blocks.

## API / authority boundary

116 owns bounded workspace-scoped CRUD/read operations for Roadmap items and Calendar allocations plus deterministic Roadmap transitions/dependency validation. Exact endpoint shape is implementation-selected, but requests must:

- reject unknown fields and cross-workspace object refs;
- use server-owned optimistic concurrency/CAS for mutable records so stale edits fail rather than overwrite;
- return structured domain errors through the existing shared error contract;
- log accepted mutations through the existing redacting event service without making that log the state owner;
- perform no provider, GitHub, filesystem, runner or external-network operation.

No second Board store, generic task engine, workflow engine, recurrence engine, notification daemon, collaboration/ACL subsystem or background scheduler is authorized.

## Frontend scope

Activate the approved Development Roadmap composition without redesign:

- Development owns exactly `Roadmap | Brainstorm`; this slice activates Roadmap only.
- Roadmap owns `Timeline | Calendar`; no standalone Board destination.
- Timeline uses Roadmap project windows and includes the collapsible execution-status projection over the same identities.
- Manual `+ Add work item`, details/edit/delete and lifecycle transitions use the canonical Roadmap owner.
- Calendar defaults to Week and supports `Day | Week | Month | Agenda` as projections over canonical allocations.
- `+ Add event`, details/edit/delete and `Open roadmap item` use the canonical Calendar/Roadmap owners.
- Opening/browsing does not silently add Jarvis context.
- Jarvis proposal affordances remain inert/unavailable until 122 owns the PROPOSE actions; 116 does not fabricate them.

The approved HTML/reference composition remains presentation authority. Implementation may reuse existing shared shell/fusion components but must not create React-local canonical Roadmap/Calendar state.

## Failure modes that must be covered

1. stale edit overwrites a newer item/allocation;
2. cross-workspace typed links or dependencies;
3. self/cyclic Roadmap dependencies;
4. `Done` despite unsatisfied/unknown declared acceptance gate;
5. silent cascade deletion of dependents or Calendar allocations;
6. conflating Roadmap project windows with Calendar occupied time;
7. DST gap/fold ambiguity or time-zone loss on round-trip;
8. malformed/unknown enum or request fields;
9. Jarvis/model proposal committed without explicit acceptance;
10. browser-local state diverging from server truth.

## Acceptance criteria

- Stable Roadmap item identity and Calendar allocation identity persist across restart in the canonical backend database.
- CRUD is workspace-scoped, stale-safe and rejects unknown/cross-workspace references.
- Dependency cycle/self-reference tests fail closed.
- `Done` transition is blocked when a declared acceptance condition is not satisfied/evaluable.
- One Roadmap item can have zero/one/many Calendar allocations; editing either side does not silently rewrite the other concept.
- Date/time/time-zone round-trip is deterministic, including explicit DST ambiguity tests.
- Existing event logging records accepted mutations with redaction but is not queried as primary Roadmap/Calendar state.
- Frontend deterministic tests prove Timeline/Calendar consume server-owned state and preserve no-Board composition.
- Exact-head trusted Chromium proof, using the generic declarative proof toolbox, covers at least: create Roadmap item, edit it, schedule two Calendar blocks linked to it, verify Timeline window remains distinct from blocks, exercise a blocked Done transition, and delete/edit behavior without hidden cross-owner mutation.
- No provider/network/filesystem/Git/runner authority is introduced.

## Non-goals

- Brainstorm or speech capture (117);
- Jarvis Development context/proposals (122);
- Board/Kanban store or page;
- automatic AI scheduling, auto-rescheduling or calendar optimization;
- external calendar sync, email/invitations, collaboration or multi-user permissions;
- recurrence rules, notifications or background jobs unless separately proven necessary later;
- generic workflow/task orchestration;
- changes to accepted Coding, Memory, Design or Settings authority.

## Readiness gate

Before changing `STATUS.md` from `planned` to `ready`, fresh exact-master evidence must freeze the minimum persistence/API owner and migration shape, confirm the existing Development route insertion points, confirm no duplicate active implementation/readiness PR exists, and identify deterministic + generic exact-head browser-proof paths. Readiness may be compressed into the same planning PR only if those facts are resolved without widening security/destructive authority.

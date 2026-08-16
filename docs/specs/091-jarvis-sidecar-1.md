# 091 — JARVIS-SIDECAR-1

## Status

Definition-only. Registry row 091 remains `planned`; runtime implementation requires a separate readiness decision derived from the merged definition and exact current master.

Derived from exact reconciled master `dd4504c3e89a93cede1f98fc7a4f25f2d69ca0ba` after merged/reconciled 090 AI-THREADS-0.

## Objective

Turn the existing 083 contextual sidecar shell region into the primary contextual Jarvis interaction surface without creating a second conversation engine, a second execution path, autonomous-agent authority, or a parallel memory/accounting model.

The sidecar must let the operator interact with Jarvis while staying inside the current application context. It reuses 090 thread persistence/provenance and the canonical 042/059b/061 execution, egress, budget, continuation and proposal boundaries. It may expose bounded advisory role profiles, but those profiles are presentation/prompt-policy choices only; they are never independent agents, identities with separate memory, route owners, or promotion authorities.

## Current-master authority inventory

Current master already provides the minimum authorities 091 must compose rather than duplicate:

- 083 application shell owns one `ContextualSidecar` region, open/close/focus behavior, App-owned route state, workspace state, stage selection, shell-region contributions and no-global-overflow/accessibility behavior.
- 090 owns workspace-scoped episodic threads, durable interaction→canonical-flow provenance, bounded local assistant snapshots, idempotent request ids, stale-response handling and the `/ai/threads` API/client.
- 042 owns deterministic context-pack selection/preview over accepted engineering records.
- 059b owns external egress policy, sensitivity, sanitization, budget reservation, confirmation and provider permission.
- 061a/061b own canonical flow/attempt/continuation accounting and final assembled output.
- 041 owns proposal capture from approved AI output; proposal promotion/rejection remains explicit elsewhere.

091 must not fork any of these authorities.

## Product contract

### 1. One contextual sidecar, not a new application shell

091 consumes the existing 083 sidecar region. It does not add a second global drawer, floating chat window, modal assistant, background panel system, or alternate navigation shell.

The sidecar is available from application routes where App already has a workspace context. Stage-owned contributions may provide bounded context descriptors/actions, but App/Layout remain the single shell owner.

The existing `/ai-threads` page remains a non-primary inspection/history surface. 091 is the normal conversational entry point; it reads/writes the same 090 threads and must never maintain a separate transcript store.

### 2. Workspace and context binding

Every sidecar interaction is bound to the current App-owned workspace id. No thread may silently move between workspaces.

The sidecar may derive a bounded contextual hint from the current route/stage selection, for example selected candidate/run/engineering record identifiers already exposed by current frontend state. Such context is advisory UI state only until converted through existing canonical context-pack/execution boundaries.

Raw complete-thread history, arbitrary DOM state, hidden page text, filesystem paths, secrets, credentials and unbounded page payloads must never be forwarded to a provider.

A route/workspace/selection change must synchronously invalidate stale UI ownership. Late list/detail/submit/context responses from the old context must be ignored and must not leave the new context busy, disabled, errored or overwritten.

### 3. Thread lifecycle reuse

091 must use the 090 thread API and persistence model. Minimum behavior:

- select an existing workspace thread;
- create a new thread;
- submit a prompt with 090 idempotent request semantics;
- render bounded persisted user/assistant snapshots and canonical provenance state;
- preserve request-id reuse for an unchanged retry after uncertain persistence;
- never redispatch merely because the sidecar closed, route changed, or snapshot persistence failed.

The implementation may add a narrowly scoped 090 read/client projection only if readiness proves a missing field is necessary for the sidecar. It may not add a second thread table, message table, transcript cache, provider ledger or proposal store.

### 4. Context-pack preview and execution boundary

The operator must be able to tell whether project context is being used before submission. 091 may expose a compact context summary/preview using existing 042 authority or a readiness-approved minimal wrapper around it.

If project context is included, execution still goes through the same canonical thread-submit → `run_ai_task` path and 059b/061 controls. The frontend never calls providers directly and never chooses provider permission.

No sidecar control may bypass confirmation, sensitivity, sanitization, budget or fallback policy. Provider/cost/token/latency evidence remains canonical in the existing flow/attempt authority and is read, not duplicated.

### 5. Advisory role profiles

091 may expose a small fixed set of JarvisOS-owned advisory role profiles if readiness proves they can be implemented as bounded prompt/context policy over the existing execution spine. Examples of intended semantics are engineering review, concise operator assistance, and exploratory explanation.

Profiles must satisfy all of the following:

- deterministic stable ids and human-readable labels;
- no separate memory, credentials, tools, budgets, provider accounts or permissions;
- no claim of independent agency or autonomous presence;
- no hidden authority to promote/reject engineering records;
- no automatic provider escalation merely because a profile is selected;
- selected profile and its policy version are inspectable in the UI and, where execution provenance already supports it, represented without creating a second ledger.

Readiness may reduce the profile set further or defer profiles entirely if current runtime contracts cannot carry the selection without disproportionate backend expansion.

### 6. Proposal and engineering-authority boundary

Jarvis responses remain advisory. Existing 041 proposal capture may create proposals through the canonical execution flow. The sidecar may show that proposals were produced and navigate to the existing Review/Engineering Data surfaces, but 091 does not promote, reject, grade, overwrite or silently apply them.

The blocked 062 grade surface is strictly excluded.

### 7. Failure states

The UI must distinguish at least:

- no workspace selected;
- thread list unavailable;
- selected thread unavailable;
- context preview unavailable;
- submit in progress;
- canonical execution/confirmation/failure state as exposed by current authority;
- local snapshot persistence uncertainty;
- stale response discarded after workspace/thread/selection change.

A provider/network failure must not destroy the local thread or erase prior durable interactions. A local sidecar render failure must not alter canonical flow state. Closing/reopening the sidecar must not dispatch work.

## UX and accessibility contract

- Desktop-first engineering workstation density; reuse existing 070 tokens/primitives and 083 sidecar chrome.
- Light/off-white base and natural leaf/chlorophyll green only through existing semantic tokens; no global visual-identity implementation in this slice.
- Sidecar must remain usable at effective 200% zoom without global horizontal page overflow.
- Keyboard operation must cover opening/closing, thread selection, composer focus, submit, retry and context-preview controls.
- Closing with Escape returns focus through existing shell behavior.
- Status/error changes use appropriate accessible announcements without stealing focus unnecessarily.
- Untrusted model/user text is rendered inertly; no HTML execution or unsafe links.
- Reduced-motion and theme behavior remain inherited from 070/083.

## Expected minimum implementation boundary

Readiness must inventory exact current contracts before authorizing files. The expected minimum is primarily frontend composition over existing 083 and 090 capabilities, with only the smallest backend/API extension that is proven necessary for contextual preview/profile provenance.

Likely frontend ownership:

- `frontend/src/App.tsx` and/or stage contribution wiring only as required to supply workspace/selection/context to the existing sidecar;
- `frontend/src/components/shell/ContextualSidecar.tsx` or a new sidecar-local content component, without changing global shell ownership;
- `frontend/src/api/threads.ts` only for proven missing 090 projections;
- sidecar-local deterministic state helpers/tests;
- bounded local CSS using existing tokens.

Any backend/schema/migration change is presumptively out of scope and requires explicit readiness evidence that the acceptance criteria cannot be satisfied through existing 042/090 contracts.

## Acceptance criteria

1. On a workspace-backed application route, the existing shell sidecar opens a Jarvis interaction surface without navigating away from the current workbench.
2. The operator can create/select a 090 thread and submit through the canonical 090→`run_ai_task` execution path; no second transcript/execution/provider path exists.
3. Workspace changes and thread/context changes reject stale responses and immediately release obsolete UI-local busy state without cancelling or redispatching canonical backend work.
4. The operator can inspect whether bounded project context is included before submission; raw complete-thread/page state is never sent as provider context.
5. Any role profile is explicitly advisory, inspectable, bounded and unable to change provider permission, budget, memory, tools or promotion authority.
6. Canonical confirmation/failure/provenance and local persistence uncertainty are rendered distinctly; provider failure does not corrupt the thread.
7. Proposal references may navigate to existing review surfaces but 091 performs no promotion/rejection/grade mutation.
8. Existing `/ai-threads` inspection remains reachable and uses the same persisted threads.
9. Keyboard/focus behavior, inert hostile text, reduced motion, theme inheritance and effective-200%-width containment pass exact-head browser evidence.
10. No secrets, credentials, provider packets, unbounded context, filesystem paths or fabricated engineering evidence appear in frontend state/rendering.
11. All inherited 070/083/090 conformance gates, frontend build, repository CI and BLUECAD proof pass on the exact merge head.
12. Rollback is independently removable: removing 091-specific composition restores the pre-091 shell while preserving 090 threads/flows/proposals and all canonical engineering data.

## Required adversarial matrix

Readiness and implementation evidence must cover at minimum:

- submit on thread X → select Y before completion → stale X completion cannot alter or lock Y;
- submit → workspace A→B→A race;
- close/reopen sidecar during in-flight submit;
- context preview request → route/selection changes before completion;
- duplicate click/Enter and unchanged retry request-id behavior;
- confirmation-required, failed-terminal, partial-terminal and persistence-failure presentations;
- hostile user/model strings including markup-like text and long bounded content;
- no-workspace and empty-thread states;
- effective-200%-width plus keyboard/Escape/focus restoration;
- provider/network calls absent from frontend tests and no raw full-thread egress.

## Non-goals

- Hermes runtime, MCP, autonomous agents, background execution or multi-agent presence;
- semantic memory/RAG transcript history or automatic memory consolidation;
- provider selection/permission/budget policy redesign;
- new durable conversation/message/ledger stores;
- streaming/token-by-token UI unless separately authorized later;
- voice, attachments, file upload, web search, tool execution controls or command palette expansion;
- 062 grading UI;
- proposal promotion/rejection inside the sidecar;
- global visual identity, Penpot/design-token redesign or broad shell restyling;
- Settings (029), scene binding (092), scene semantics (058c), variants (006b) or comparison history (058b).

## Rollback

Rollback removes only 091-owned sidecar composition, local state helpers, optional bounded profile/context UI and any readiness-approved narrow read projection. Existing 083 shell regions, 090 thread tables/API/data, canonical AI flows/jobs, 042 context authority, proposals, budgets and engineering records remain untouched and usable.

## Readiness questions

Before implementation authority, a separate readiness record must answer from exact merged master:

1. Which current component should own sidecar content while preserving `Layout` as shell owner?
2. Can 090 thread submit already accept the exact context/profile semantics required, or is one internal/read-model seam necessary?
3. Which 042 preview endpoint/client fields are sufficient for a compact inspectable context summary?
4. Which existing execution/provenance fields can represent selected advisory profile without a new ledger/schema?
5. What is the minimum fixed profile set, if any, that adds real operator value without fake-agent semantics?
6. Which exact frontend files form the allow-list and which inherited checkers must be preserved?
7. How will the browser proof reproduce stale sidecar/thread/context races and effective-200%-width behavior on one exact head?

Until that readiness decision merges, registry row 091 remains `planned` and no runtime implementation is authorized.
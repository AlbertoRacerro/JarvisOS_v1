# 111 — JARVIS-CONTEXT-ACTION-FOUNDATION-1

## Status

Full specification only. Derived from exact post-definition master `198775cb2e3f98fcdb4a8b4cb64a18c80db23ae1`, where definition PR #418 is merged. Registry row `111` remains `planned`; runtime implementation requires a separate fresh exact-master readiness decision plus registry reconciliation to `ready`.

## Objective

Provide one stable, backend-owned common context/action contract between all canonical operator pages and Jarvis while reusing the existing AI execution, egress, budget, provider, thread and proposal authorities.

The binding seam is:

`Pages -> stable Jarvis Context/Action contracts -> Jarvis service/policy -> current AI runtime now / Hermes adapter later`

111 makes context explicit, inspectable, stale-safe and domain-owner-preserving. It does not make Jarvis a second domain authority and does not implement any 112–126 domain feature.

## Exact-master authority inventory

The exact source master already contains the authorities 111 must compose rather than fork:

- `backend/app/modules/ai/context_builder.py` owns deterministic canonical context serialization, `canonical_digest`, `ContextBundle`, source manifests and bounded workspace context selection. Its own documented extension seam is `blocks + digest + source manifest + budget + provenance`; current generic blocks carry `source`, `content`, optional `type`, optional `id` but do not yet carry a general exact revision/ref identity.
- `backend/app/modules/ai/models.py` owns `ContextPackSelectionRequest`, `ContextPackPreviewRequest/Response` and provider-neutral task request/response models. Existing preview returns blocks, context digest, source manifest, counts and budget evidence.
- `backend/app/modules/ai/routes.py` exposes `/ai/context/packs/preview` and `/ai/tasks/run`; provider access remains server-side.
- `backend/app/modules/ai/thread_models.py` owns thread submit shape. A submit already binds `context_selection` to an `expected_context_digest`, so mismatched context can fail closed rather than silently changing.
- `backend/app/modules/ai/thread_service.py` owns workspace-scoped 090 thread execution/idempotency and delegates actual work through `run_ai_task`; it already rebuilds context before dispatch and preserves immutable request identity.
- `backend/app/modules/ai/execution.py`, `token_flow_*`, `egress_*`, `budget.py`, `provider_registry.py`, `gateway.py`, `privacy.py` and `sensitivity.py` own canonical execution, continuation, egress, accounting, provider and safety behavior.
- merged 090 owns thread persistence; merged 091 owns Jarvis sidecar composition over that persistence; merged 054/097 own proposal/review and stale-safe engineering-action boundaries.
- domain modules remain owners of their own records, revisions, validators and COMMIT/EXECUTE behavior.

### Exact mismatch to solve

The existing context-pack seam is strong enough to reuse but too project-record-specific for the final cross-domain Jarvis contract. In particular:

1. the generic context block/source manifest shape does not express owner + exact revision/version/ref for arbitrary future Project Knowledge, Development, Coding, BLUECAD or Process refs;
2. current selection describes record kinds/ids but does not distinguish route-local selection from an operator-maintained explicit removable added-context basket;
3. there is no single typed registry describing which generic Jarvis action classes a route/ref may expose while mechanically prohibiting common Jarvis code from acquiring COMMIT/EXECUTE authority;
4. current preview/digest must be lifted into the stable cross-domain contract without creating a parallel canonical-context store.

111 therefore authorizes the smallest additive contract/service layer around these current owners. It does not replace them.

## Product contract

### 1. Three distinct states: route, selection, added context

These states are separate and must never be conflated:

- **Route descriptor**: bounded presentation identity for the active canonical operator surface, e.g. a stable route/surface id plus optional mode/tab id. It is not AI context by itself.
- **Selected refs**: exact refs exposed by the active domain owner because the operator currently selected/inspected something. Selection is not AI context by itself.
- **Added-context refs**: exact refs explicitly added with a `CONTEXT` action. Only this basket is eligible for common Jarvis context assembly, subject to owner validation and policy.

Navigation, opening, expanding, hovering, focus, selection changes, browser back/forward and route transitions MUST NOT implicitly append/remove added context.

### 2. Stable exact ref contract

A common Jarvis ref is a bounded descriptor of an object owned elsewhere. The contract must support at minimum:

- `owner` / domain namespace;
- `kind`;
- stable object `id`;
- exact `version`, `revision`, immutable `ref`, or equivalent owner-issued identity when available;
- optional owner-issued content/evidence digest when needed for exact binding;
- workspace identity;
- bounded source/provenance descriptor;
- state needed to distinguish `current`, `stale`, `unavailable`, or `unknown` without inventing owner truth.

The common layer stores/replays only refs and bounded inspected evidence. It does not copy the canonical object as a second domain record.

If an owner has no exact version identity yet, 111 must preserve `unknown/unavailable` and must not manufacture a timestamp/hash/version. Such a ref may be rejected from AI context when safe exact binding cannot be proven.

### 3. Explicit removable context basket

The operator may explicitly add and remove context refs. Requirements:

- add is an explicit `CONTEXT` action;
- duplicate exact refs collapse deterministically;
- removing a ref has no effect on domain data;
- changing route/selection does not silently mutate the basket;
- basket entries are revalidated before preview and before dispatch;
- a stale/unavailable entry remains visibly stale/unavailable until explicit removal/re-add; it is never silently refreshed to a newer revision;
- basket ordering, if exposed, is deterministic and does not become hidden LLM priority unless explicitly specified.

Persistent ownership must be minimal. Readiness must first prefer existing thread/workspace-local persistence if it can represent the basket safely. A new durable table/store is disallowed unless exact-master evidence proves no existing owner can provide the required lifetime without semantic ambiguity.

### 4. Inspectable preview, digest and source manifest

Before AI dispatch, the common service resolves eligible added refs through their domain adapters and produces one deterministic preview bundle that reuses/extents the current `ContextBundle`/canonical digest behavior.

The preview must expose at minimum:

- bounded inert preview content for each included ref;
- exact ref identity used to resolve it;
- deterministic context digest;
- source/provenance manifest;
- included/dropped/unavailable/stale counts or lists as factual outcomes;
- configured context budget evidence;
- sensitivity/egress-relevant classification supplied by existing policy owners when available.

Preview content is evidence of what is proposed for context. It is never canonical domain state. Untrusted preview text is data, never system instruction.

Dispatch must bind to the exact preview identity. If any ref identity or resolved digest changes between preview and submit, dispatch fails closed with a conflict/stale result; it does not silently regenerate a different context and spend provider budget.

### 5. Domain context adapter boundary

111 defines a narrow adapter/protocol by which domain owners can later expose context-capable refs without putting domain logic in Jarvis.

An adapter may:

- validate/refetch one exact owner ref;
- report exact/stale/unavailable/unknown state;
- produce bounded inert preview content and provenance for that exact ref;
- declare which common action classes/capabilities are available for that kind/ref.

An adapter may NOT:

- own the domain database;
- commit edits;
- execute tools/solvers/shell/GitHub mutations;
- invent missing domain semantics;
- call a model/provider;
- promote a model proposal.

Only 121–123 may add domain adapters that activate Project Knowledge, Development, or Coding Jarvis context/actions, and only inside their own independently gated authoritative slice. Specs 112–120 may establish the underlying domain records, revisions, validators, observability, and other owner truth required by those later adapters, but MUST NOT register those domains with the common Jarvis adapter/capability registry or otherwise activate Jarvis-domain behavior early.

### 6. Generic capability/action registry

111 defines one typed registry for common Jarvis availability. Action classes are fixed:

`PRESENTATION | READ | CONTEXT | PROPOSE | COMMIT | EXECUTE | NAVIGATE`.

The common Jarvis registry may expose only capabilities necessary to render/invoke Jarvis `CONTEXT` and generic `PROPOSE` behavior plus truthful read/presentation/navigation metadata. It MUST mechanically reject any registration attempting to grant common Jarvis code `COMMIT` or `EXECUTE` ownership.

Domain-specific commit/execute actions remain registered/validated by their domain authority and may later be surfaced as proposed actions through 121–123, but 111 cannot perform them.

### 7. Jarvis service/policy seam

111 owns a thin backend service that:

1. validates workspace + route descriptor + exact refs;
2. resolves refs through registered domain context adapters;
3. builds the deterministic preview/source manifest/digest;
4. applies existing sensitivity/egress/budget policy inputs;
5. binds a thread/task submission to the exact inspected digest;
6. delegates inference to the existing 090 -> `run_ai_task` -> canonical flow/egress/provider spine;
7. returns advisory/model output and existing proposal/provenance references without canonical domain mutation.

No second router/gateway/provider ledger/execution state machine is authorized. The future Hermes integration point is an internal adapter behind this stable service; swapping that adapter must not force pages/domain owners to change the context/action contract.

#### External-context authorization bridge

The inspected Jarvis preview digest is not, by itself, egress authority. Current external execution sends supplied manual context through `authorize_manual_context()`, whose 059a boundary accepts only exact, current approved sanitized derivatives. 111 MUST preserve that boundary rather than forwarding ordinary resolved domain-ref blocks directly to an external provider.

For any external route that 111 claims to support with added context, readiness must freeze one exact bridge from inspected exact refs to the existing 059a-approved derivative authority. The bridge must preserve an auditable mapping among (a) the inspected owner refs/digest, (b) the exact approved derivative ids/content digests/effective levels actually authorized for egress, and (c) the effective context digest bound to dispatch. If a ref has no current approved derivative or that derivative/source identity changes after preview, external dispatch must pause/fail closed before provider spend; the implementation must not silently drop the ref, substitute latest content, or bypass `authorize_manual_context()`.

A backend-only/local route may continue to use the existing policy path appropriate to that route. An implementation may alternatively leave ordinary exact-ref external context explicitly unavailable in 111 if no safe minimum bridge exists, but it must then expose that limitation truthfully and must not satisfy acceptance by advertising an external-context path that deterministically ends in `manual_context_not_authorized` for every normal domain ref.

### 8. Thread and proposal reuse

- Conversation persistence stays in 090 thread tables/service.
- Jarvis sidecar uses that same thread identity; no sidecar-specific transcript truth.
- Existing request-id/idempotency behavior remains authoritative.
- Model output is advisory.
- Existing proposal/action evidence mechanisms remain the only path toward later explicit domain-owned promotion.
- 111 does not approve/reject/apply proposals.

### 9. Frontend boundary

Frontend responsibility is limited to typed presentation of backend-owned contract state and explicit operator intent:

- route descriptor from the canonical router/surface identity;
- selected-ref descriptors supplied by current page/domain state;
- explicit add/remove/inspect context controls where readiness proves a minimal integration is required;
- preview/digest/stale/unavailable rendering;
- existing Jarvis thread/composer UI.

Frontend MUST NOT:

- resolve canonical refs independently;
- calculate authoritative revisions/provenance;
- call providers, GitHub, filesystem, shell or process APIs directly;
- hold a canonical context copy/store;
- infer availability from DOM text;
- silently add context on selection/navigation.

Any visible modification must preserve the merged 100f/100g canonical composition and requires exact-head browser proof. Readiness should prefer a backend/common-contract-first slice with the smallest visible delta.

## Failure-mode contract

111 must fail closed for at least:

- workspace mismatch;
- unknown adapter/owner/kind;
- missing object;
- missing required exact version/ref;
- stale owner revision;
- digest mismatch after preview;
- stale preview submitted after object mutation;
- duplicate/conflicting ref identity;
- context budget overflow/drop with deterministic disclosure;
- sensitivity/egress rejection;
- external exact-ref context lacking a current approved 059a derivative/authorization bridge;
- approved derivative/source digest drift between inspected preview and dispatch;
- unauthorized action class;
- attempt to register or invoke common COMMIT/EXECUTE;
- malformed/oversized hostile preview content;
- route/selection races in the browser;
- provider/network failure after durable thread reservation;
- local snapshot capture failure after canonical execution.

A context failure must not dispatch a provider call. A provider failure must not mutate canonical domain state. A UI race must not cancel/rewrite a canonical flow or leak stale state into a new workspace/ref.

## Expected implementation seams for readiness to validate

Readiness must re-read exact master and freeze the minimum allow-list. The expected candidate seams are:

Backend common layer:
- `backend/app/modules/ai/context_builder.py` — additive exact-ref/source-manifest support only if necessary while preserving existing context pack compatibility;
- `backend/app/modules/ai/models.py` and/or a new narrowly scoped `jarvis_context_models.py` — typed common ref/preview/action contracts;
- a new narrowly scoped `backend/app/modules/ai/jarvis_context.py` service/adapter registry if extending `context_builder.py` would mix domain/business concerns;
- `backend/app/modules/ai/routes.py` or a dedicated `/ai/jarvis/...` sub-router for preview/validation only when current endpoints cannot express exact-ref requests;
- `backend/app/modules/ai/thread_models.py` / `thread_service.py` only for the minimum exact inspected-preview binding that current `context_selection + expected_context_digest` cannot represent;
- existing `backend/app/modules/ai/egress_authority.py` / sensitivity derivative authority only through a minimum additive bridge if readiness proves external exact-ref context is supported in 111; no bypass or parallel egress authority.

Frontend, only if required for acceptance:
- existing final Jarvis sidecar/fusion component(s) and current API client;
- no new page shell or domain store.

Tests:
- backend contract/service tests for exact refs, stale detection, preview/digest and forbidden action authority;
- thread/execution integration tests proving zero dispatch on stale/digest mismatch and reuse of current flow/ledger;
- external-context tests proving either a successful exact-ref -> approved-derivative -> authorized external dispatch with digest/ref binding, or truthful explicit unavailability before dispatch;
- focused frontend/browser tests only for any newly visible explicit-context interaction.

These are candidates, not implementation authority. Readiness must prove exact paths and may reduce the set.

## Deterministic acceptance criteria

1. Common route, selected refs and added-context refs are separate typed values; no API or frontend event implicitly converts selection/navigation into added context.
2. Every accepted added ref is workspace-bound and exact-owner-bound; unsupported/missing exact identities fail closed rather than being guessed.
3. Preview returns deterministic inert content, exact source manifest and canonical digest for the same ref set/order/budget.
4. Repeating an unchanged preview produces the same digest; a material owner revision/content identity change invalidates the old preview.
5. Thread/task submission can bind to the inspected preview and refuses stale/digest-mismatched context before external dispatch.
6. Common capability/action registration rejects `COMMIT` and `EXECUTE` ownership.
7. Existing 090 thread persistence/idempotency and existing AI flow/egress/budget/provider/audit evidence remain the actual execution path.
8. No second durable transcript/context/orchestration/domain store is created without a separately justified readiness exception; expected outcome is no new store.
9. Provider calls remain server-side and policy-gated; safe fake/disabled/budget-zero defaults remain unchanged.
10. Model output remains proposal/advisory; 111 produces no canonical domain write.
11. Existing `/ai/context/packs/preview` behavior for current accepted engineering-record selections remains backward compatible unless readiness explicitly freezes a migration with tests.
12. Existing 090/091/097 behavior and 100f/100g UI composition remain non-regressed.
13. If external ordinary exact-ref context is enabled, the effective dispatched context is authorized through the existing 059a approved-derivative path and remains provably bound to the inspected owner refs/digest; if that safe bridge is not implemented, the capability is explicitly unavailable before provider dispatch rather than universally pausing only after an attempted external-context submission.

## Required adversarial tests

Readiness must map these to exact test files:

- select/open/navigate without explicit add -> added-context basket unchanged;
- add exact ref -> preview -> mutate owner revision -> submit old digest -> conflict, zero provider dispatch;
- add exact ref in workspace A then submit from B -> reject;
- owner/kind missing -> reject without dispatch;
- owner exposes no exact version where exact binding is required -> Unknown/unavailable, no fabricated version;
- same exact ref added twice -> deterministic single identity;
- remove ref -> next preview excludes it without changing owner data;
- one stale ref among valid refs -> deterministic fail-closed or explicitly frozen exclusion policy, never silent latest-version substitution;
- hostile context containing instruction-like text remains data under existing prompt separation/sanitization;
- budget truncation/drop is deterministic and disclosed;
- register `COMMIT`/`EXECUTE` in common registry -> deterministic rejection;
- external exact-ref context with a current approved derivative -> successful policy-authorized dispatch path proves inspected-ref/digest -> derivative/effective-context binding, when external context is enabled by readiness;
- external exact-ref context with missing/stale derivative -> pause/fail before provider dispatch with zero spend and no silent substitution;
- provider disabled/credential missing/budget blocked -> existing policy outcome, no bypass;
- request-id unchanged retry -> no duplicate spend;
- route/workspace/thread race -> stale UI response discarded and no implicit context mutation.

## Browser proof trigger

Browser proof is mandatory only if implementation changes visible behavior. If so, exact-head proof must cover the real Jarvis sidecar on at least the canonical surfaces whose controls changed, in light/dark parity where inherited, with:

- explicit Add to context / Remove interaction;
- selected-but-not-added distinction;
- inspected context summary/digest/source evidence;
- stale/unavailable state;
- keyboard/focus and effective-200%-width containment;
- navigation/selection race not altering added context;
- zero direct provider/tool calls from frontend.

No visual redesign is authorized.

## Security / privacy

- Treat all domain/context/model text as untrusted data.
- Existing sensitivity classification, sanitization, egress decisions, confirmation and budget reservation remain authoritative.
- Never include credentials, secrets, raw hidden DOM, filesystem secrets, GitHub tokens or unbounded thread/page payloads in context.
- Exact refs/digests are identifiers/evidence, not proof that content is safe to egress.
- Any future external dispatch still requires the current egress policy path, including 059a approved-derivative authority for supplied manual context; 111 cannot turn an inspected preview into an egress approval.

## Migration and rollback

Expected migration is additive and store-free. Existing context-pack and thread contracts must keep working during rollout. If one current request model gains optional common Jarvis fields, omission must preserve pre-111 behavior.

Rollback removes the 111 common adapter/contracts/endpoints/UI hooks while preserving all existing domain data, 090 threads, context packs, proposals, AI flows/jobs, egress records, settings, providers and final operator UI.

## Non-goals

- 112 Project Basis canonical write/reconciliation/revalidation;
- 113 Models exact-version dossier;
- 114/115 Literature records/import/search/extraction;
- 116 Roadmap/Calendar and 117 Brainstorm persistence;
- 118/119 Coding remote/local observability;
- 120 Coding pipeline;
- domain-adapter registration or Jarvis-domain activation for any 112–120 foundation slice;
- 121–123 domain-specific Jarvis proposal actions;
- 124 provider settings expansion;
- 125 self-update;
- 126 PTY;
- 102–110 late engineering execution/evaluator work;
- 093 editable process workbench;
- Hermes 066–068/080 runtime.

## Readiness questions

A separate readiness decision from fresh exact master must answer:

1. Is the common added-context basket ephemeral request/UI state, thread-owned state, or does an existing workspace owner already fit the required lifetime? Prove why no new store is needed or justify the exception.
2. What exact ref model fields are mandatory vs optional for each initially supported owner kind?
3. Which existing context-pack owner kinds are activated first, and which remain adapter-deferred specifically to 121–123? Confirm that 112–120 cannot register/activate Jarvis domain adapters.
4. Can existing `ContextBundle` be safely extended without breaking 042/090, or should 111 wrap it in a new narrow service model?
5. Can existing `context_selection + expected_context_digest` bind the richer inspected exact-ref preview, or is one additive submit field required?
6. What exact backend/frontend file allow-list is minimum necessary?
7. Which tests prove zero provider dispatch on stale/digest mismatch and no COMMIT/EXECUTE authority?
8. Is any visible UI control necessary in 111, or can explicit-context presentation wait for the first domain adapter while still proving the common contract backend-first?
9. For an external provider route, what exact 059a-approved derivative/authorization bridge binds the inspected owner refs/digest to the effective dispatched context? If no safe minimum bridge is implemented in 111, how is ordinary exact-ref external context made explicitly unavailable before dispatch?

Until that readiness merges and the registry is reconciled to `ready`, no 111 runtime implementation is authorized.

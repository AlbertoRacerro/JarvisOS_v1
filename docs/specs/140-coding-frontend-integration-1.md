# 140 CODING-FRONTEND-INTEGRATION-1

Status: full specification / planning authority; implementation remains unauthorized until the canonical registry row is `ready`.

Definition authority merged through PR #549. Full-spec derivation basis: exact `master` `084c382451972081c23c4b05fd76cf1ba238b95c`.

## Purpose

Replace the remaining Coding operator placeholders with one bounded frontend integration over the already accepted Coding backend owners. The browser consumes server-owned repository, runtime, pipeline and Jarvis Coding contracts; it does not create a second truth layer or acquire new GitHub/provider/filesystem/execution authority.

The accepted owners remain:

- 118 — remote repository/ref/exact-SHA, bounded tree/file/literal-search, PR/check/review evidence and safe GitHub URL truth;
- 119 — actual local executed path/ref/SHA/dirty/build/runtime identity and deterministic relation to an exact remote target;
- 120 — inspectable Proposal → Plan → Implementation → Tests → Independent Review → Reconciliation → Merge state;
- 123 — bounded Jarvis Coding `READ` / `PROPOSE` actions with exact-base/context/path binding and stale refusal;
- 091/100f/100g — existing operator-workstation composition and Coding route/visual ownership;
- 111 — explicit context/action boundary; ordinary browsing remains context-neutral.

## Fresh implementation evidence

Fresh master already exposes the stable Coding routes `/coding/repository` and `/coding/runtime`. `frontend/src/App.tsx` still renders the Repository route through `FinalOperatorUnavailableSurface`, explicitly saying that no frontend-safe repository observer is wired. The Runtime route uses `FinalOperatorReadSurface`, which currently reads `/system/info` and truthfully leaves executed SHA, remote SHA and alignment `Unknown`.

The accepted server routes in `backend/app/modules/coding/runtime_routes.py` already expose:

- `GET /api/coding/runtime-truth` from 119;
- `GET /api/coding/pipeline-state` from 120;
- `POST /api/coding/actions/inspect` from 123;
- `POST /api/coding/actions/suggest-modification` from 123.

118 is presently implemented as the bounded `RepositoryTruthService` read-only authority rather than as a browser-facing GitHub client. Therefore 140 may add only the minimum FastAPI projection/adaptor required for the existing browser Coding surface to invoke accepted 118 operations through JarvisOS. That adaptor must delegate to 118 without reimplementing repository validation, network transport, bounds, freshness, URL validation, error taxonomy or credentials. It is an integration seam, not a new repository authority.

## Required product behavior

### Coding → Repository

The existing `/coding/repository` surface must consume 118 through JarvisOS server routes and show only server-proven facts for a configured repository/ref:

1. repository identity, requested ref and resolved exact 40-character SHA;
2. bounded repository tree/path listing;
3. bounded file preview for an explicitly selected path;
4. bounded literal search when requested by the operator;
5. available pull-request/check/review evidence when a PR is explicitly selected;
6. safe GitHub navigation URLs only when returned by the server-owned 118 contract.

No stale/ref-mismatch result may be relabelled as current. Provider timeout, unavailable, partial, oversized, malformed and authentication-required states remain explicit truthful error/partial states. No fixture/placeholder repository fact may remain visible as if live once a server request has resolved.

### Coding → Runtime

The existing `/coding/runtime` surface must use 119 `/api/coding/runtime-truth` for the selected configured repository and exact target ref. It must show the server-returned local executed path/ref/SHA, dirty/build/runtime identity, remote target identity, and only the deterministic relation returned by 119: `aligned`, `local_behind`, `divergent`, or `unknown`.

The frontend must not compare SHAs, infer ancestry, infer cleanliness, or derive alignment independently. A missing startup snapshot, unauthorized repository, stale target or other typed failure must remain visible rather than falling back to `/system/info` as proof of exact code identity. `/system/info` may remain supplementary non-authoritative system detail only if it is not presented as repository/runtime alignment truth.

### Development pipeline projection

The Coding operator surface must expose the relevant 120 pipeline-state projection for an explicitly selected repository/PR/spec identity. It must render server-owned stage state/evidence and stale invalidation; it must not create a second roadmap, queue, workflow state machine, merge decision or client-side stage progression.

A missing PR/spec selection is an explicit unselected/empty state, not a synthetic pipeline. A stale or invalidated server projection must not retain previously rendered green/complete state as current.

### Jarvis Coding READ / PROPOSE

The existing Jarvis sidecar may expose the accepted 123 Coding capabilities only:

- inspect/explain exact repository/runtime evidence via `coding.inspect`;
- explicitly insert accepted Coding evidence into context through the 111/123 context mechanism;
- `Suggest modification` through `coding.suggest-modification`, producing a bounded proposal/diff/plan only.

The Suggest modification request and result must preserve exact repository/base SHA, bounded target paths and context digest as defined by 123. Stale base, mismatched context/path evidence or missing evidence must remain a refusal. The UI must not imply that a proposal was committed, applied, executed, pushed, branched, opened as a PR, merged or dispatched.

Ordinary tree browsing, file preview, search and PR evidence inspection do not silently enter Jarvis context. Context insertion requires the explicit accepted 111/123 action.

## HTTP integration boundary for 118

If current 118 lacks the minimum browser-consumable HTTP projection, implementation may add one bounded route family under the existing `/api/coding` router. It must:

- accept only configured repository identities and validated operation-specific inputs;
- delegate operation semantics to `RepositoryTruthService` rather than duplicate its provider logic;
- preserve 118 hard bounds (`MAX_*` limits), exact-SHA/ref validation, partial/error semantics and safe URL validation;
- return no GitHub credential, request header, raw secret, filesystem path outside an already accepted safe runtime identity, or arbitrary provider URL;
- expose only read operations already in 118's allowlist;
- add no mutation, branch, commit-create, PR-create, review-create, merge, workflow-dispatch or secret API.

A broad generic RPC endpoint that accepts arbitrary operation names/paths is not required and should be avoided if typed bounded routes are smaller and safer.

## Frontend implementation boundary

Reuse the current route IDs, workspace shell, header, fusion styles and Jarvis sidecar. Expected touch points are a bounded subset of:

- `frontend/src/App.tsx` only to replace the existing Repository placeholder and/or compose the accepted Coding surface;
- `frontend/src/components/fusion/FinalOperatorReadSurface.tsx` only where the existing Runtime composition can remain the smallest owner;
- one focused Coding surface/component module if separating repository/runtime/pipeline behavior materially reduces accidental coupling;
- one focused frontend API client module for `/api/coding/*` rather than provider/GitHub clients;
- existing Jarvis sidecar/context integration points required to expose 123 capabilities;
- deterministic frontend/API contract tests;
- the minimum server router/tests needed only for the 118 HTTP projection described above.

Do not create a second app router, global store, Coding page hierarchy, design system, GitHub client, provider SDK or parallel context basket.

## Controlled-parallel boundary with 113

113 remains parked on its accepted exact-head real-browser `/memory/models` gate. Its active implementation branch owns model-dossier backend/read projection and `/memory/models` integration and currently also touches shared `frontend/src/App.tsx`.

140 owns Coding routes/surfaces and Coding API integration only. It must not modify model-dossier schemas/services/routes, `frontend/src/api/modelDossier.ts`, `frontend/src/pages/ModelDossier.tsx`, model evidence/run binding, or `/memory/models` behavior. Any unavoidable shared `App.tsx` edit is serialized by the global writer mutex and must be kept to the smallest Coding-only switch/composition change so later integration with 113 is mechanically reviewable. 140 must not consume unmerged 113 code or make 113's browser gate easier to bypass.

114 remains forbidden until both 113 and 140 are merged and mechanically reconciled.

## Deterministic acceptance matrix

| Case | Required result |
| --- | --- |
| configured repository/ref resolves through 118 | exact repository/ref/resolved SHA rendered from server response |
| stale/invalid ref or provider failure | explicit fail-closed/partial/error state; no previous fact retained as current |
| repository tree/file/search request | existing 118 bounds and path/ref validation preserved; browser never contacts GitHub |
| PR/check/review evidence selected | server-owned evidence rendered without client-derived mergeability/review truth |
| safe GitHub navigation link | only server-validated `github.com` URL is rendered as external navigation |
| runtime target selected | 119 local identity + exact remote target + server-returned relation shown |
| runtime snapshot unavailable/unknown | truthful unknown/error; `/system/info` is not promoted to exact Git identity |
| pipeline repository/PR/spec selected | 120 projection shown exactly; stale invalidation clears/marks prior current state |
| no pipeline selection | explicit empty/unselected state; no synthetic stages |
| ordinary browsing | Jarvis context unchanged |
| explicit accepted context action | 111/123-bound context evidence inserted with exact provenance/digest |
| valid Suggest modification | proposal/diff/plan shown with exact base SHA/target paths/context digest |
| stale/mismatched Suggest modification | visible refusal; no optimistic success |
| rendered actions | no Commit/Apply/Execute/Push/Create PR/Merge/STATUS mutation affordance |
| browser network surface | JarvisOS backend only; no GitHub/provider credential or direct provider request |

## Required tests and evidence

Implementation must include deterministic tests that materially prove:

1. frontend API requests target only JarvisOS `/api/coding/*` endpoints and propagate exact repository/ref/SHA/PR/spec/context identities;
2. the 118 HTTP projection, if added, delegates to 118 and preserves unauthorized-repository, invalid-ref/path, stale, partial/bounds and safe-URL behavior without exposing mutation operations;
3. Runtime renders 119 relation and does not independently infer alignment;
4. pipeline rendering follows 120 and invalidates stale prior state;
5. browsing is context-neutral and explicit context insertion remains the only path into Jarvis context;
6. Suggest modification success/refusal surfaces preserve 123 exact-base/context/path semantics and never claim apply/commit/execute authority;
7. no direct browser request targets `github.com`, `api.github.com`, a provider endpoint, filesystem API or execution tool;
8. current Coding placeholders are removed only where accepted server truth now exists, while truthful unknown/empty/error states remain;
9. focused frontend tests plus `npm run build` pass on exact implementation head;
10. focused backend route/service tests plus normal repository CI pass on exact implementation head.

Because this changes visible operator behavior and security/authority presentation across accepted Coding contracts, final acceptance also requires independent exact-head semantic review and exact-head real-browser proof of the accepted `/coding/repository` and `/coding/runtime` interaction. Browser proof must demonstrate real JarvisOS backend responses or deterministic accepted local fixtures at the server boundary; static screenshots or mocked React-only state are insufficient to prove wiring.

## Security / failure modes

The implementation must fail closed against:

- direct browser GitHub/provider access or credential leakage;
- arbitrary operation/path/provider RPC accidentally broadening 118;
- stale repository/ref/SHA remaining visually current after an error or target change;
- client-side SHA ancestry/alignment inference diverging from 119;
- client-side pipeline progression diverging from 120;
- implicit context capture during repository browsing;
- stale-base proposal presented as actionable/current;
- UI labels/buttons implying mutation/execute/merge authority;
- partial/provider-failure responses displayed as complete evidence;
- shared `App.tsx` edits accidentally changing parked 113 `/memory/models` behavior;
- duplicate API/store/context authorities introduced only for frontend convenience.

## Non-goals

- no repository/file mutation;
- no commit/apply/execute/push/branch/PR/merge/workflow-dispatch authority;
- no STATUS mutation from product runtime;
- no PTY or self-update authority;
- no GitHub/provider credential management;
- no generic repository/provider abstraction redesign;
- no second development queue, roadmap or workflow engine;
- no general frontend redesign or new design system;
- no Knowledge 113/114/115/121 implementation;
- no Hermes derivation;
- no Development 116/117/122 implementation;
- no Ruff-autofix or CI-digest work.

## Minimum-necessary test

Every implementation addition must be necessary to expose an already accepted 118/119/120/123 fact/action through the existing operator surface. If an existing server/client seam can carry the contract safely, reuse it. New repository/runtime/pipeline/context state ownership, generic RPC infrastructure or mutation authority fails this test and requires separate authority.

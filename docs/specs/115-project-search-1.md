# 115 PROJECT-SEARCH-1

Status: full specification candidate; implementation remains unauthorized while canonical `docs/specs/STATUS.md` is `planned`.

Exact derivation master: `4b539f5eae0d59af6f72df8b80c55e4c91571331`.

Governing planning authority: `docs/specs/100c-queue-rederivation-2026-08-28.md` and `docs/audits/100c-final-capability-interaction-ownership-f50eb0a.md`.

## Outcome

Provide one workspace-scoped, read-only Project search surface for the existing Memory / Project Knowledge area. A literal or structured query returns bounded results from the already-authoritative Project Basis/modeling, Model Dossier, and Literature owners with enough exact identity and provenance to open the owning surface safely.

115 is a projection, not a new knowledge owner. It must not create a search truth store, semantic/vector index, canonical record, Jarvis context mutation, proposal, provider call, filesystem authority, or model-generated ranking.

## Current-owner evidence

On the derivation master:

- 112 owns Project Knowledge writes/revisions/reconciliation in `backend/app/modules/project_knowledge/*`; its router has no unified search endpoint.
- 042 already provides deterministic workspace-scoped literal selection for decision/assumption/parameter/requirement/evidence records through `ContextSelectionSpec` and `select_context_records`, including the existing FTS5 capability probe / behaviorally-equivalent fallback. That selector is useful infrastructure but is not a complete Project search owner because it does not cover 113 or 114.
- 113 exposes exact Model Dossier index/detail reads through `/workspaces/{workspace_id}/model-dossiers` and exact model/version identities; no project-unified search route exists.
- 114 exposes workspace-scoped Literature source/detail/content reads, exact `source_ref`, entry `provenance_ref`, locator and used-by lineage; no project-unified search route exists.
- The canonical Memory routes are `/memory/project-basis`, `/memory/models`, and `/memory/literature`. 100c assigns the Project-search left pane to 115 while keeping presentation ownership with 100f/100g.

Therefore 115 must aggregate bounded read projections from existing owners rather than reinterpret 042 as a complete search system or add a parallel index.

## Scope

### Search domains

V0 searches these canonical owner families:

1. `requirement`
2. `parameter`
3. `assumption`
4. `decision`
5. `model`
6. `literature_source`
7. `literature_entry`

Evidence records remain reachable through their owning surfaces and exact source/use lineage, but are not a separate V0 result family. A later extension may add evidence only with a demonstrated operator search need and an exact owner contract.

### Backend API

Add one read endpoint under a dedicated projection owner:

`GET /workspaces/{workspace_id}/project-search`

Query parameters:

- `q`: required trimmed literal query, 2–200 UTF-8 characters.
- `kinds`: optional repeated/CSV closed-vocabulary filter over the seven V0 result kinds.
- `limit`: default 30, minimum 1, maximum 100.

No free-form SQL/FTS syntax, regex, JSONPath, arbitrary sort expression, provider query, or filesystem path is accepted.

Response:

```text
ProjectSearchResponse
  query: str
  items: ProjectSearchResult[]
  total_returned: int
  truncated: bool

ProjectSearchResult
  kind: closed V0 kind
  owner: "modeling" | "model-dossier" | "literature"
  stable_ref: str
  workspace_id: str
  title: str
  summary: str | null
  lifecycle_or_status: str | null
  version_or_revision: str | null
  provenance_refs: str[]
  source_refs: str[]
  route: canonical Memory route
  route_params: bounded string map
  match_fields: closed field-name list
  match_tier: "exact" | "prefix" | "contains"
```

The result contract intentionally does not pretend one shared revision scheme exists across owners. `version_or_revision` is populated only from an owner-backed version/revision identity; otherwise it is null. Raw database row IDs or digests may be carried only when they are the exact owner identity required to reopen/verify the item, never as a substitute for human title/summary.

### Owner adapters

The project-search service may call only bounded read helpers owned by the source domains:

- modeling/Project Basis: reuse or minimally extend the existing `select_context_records` literal-selection path. Parameter results must remain lifecycle-current under normal search; no superseded parameter is silently presented as current.
- Model Dossier: add a bounded literal search helper beside `model_dossier.py` that returns exact `model_spec_id` / `model_version_id` identities from the existing dossier owner. Do not create a second model index.
- Literature: add a bounded literal search helper beside `literature_service.py` over source title/citation/publisher and entry statement/value/context fields, returning existing `source_ref` / `provenance_ref` / locator identities. Do not duplicate Literature rows into another table.

Cross-domain raw SQL from the project-search aggregator is forbidden. Each owner remains responsible for workspace filtering, lifecycle/state semantics and exact identity.

### Matching and deterministic ordering

115 is literal/structured search, not semantic retrieval.

For every owner adapter:

- normalize query matching case-insensitively without changing stored content;
- treat the query as literal data, never as executable FTS grammar;
- FTS may be used only as an implementation optimization when escaped/parameterized and behaviorally equivalent to the literal fallback;
- rank each candidate by deterministic match tier: normalized exact field match, then field prefix, then contained literal;
- return deterministic owner-local candidates with stable tie breaking.

The aggregator sorts by:

1. `match_tier` (`exact`, `prefix`, `contains`),
2. fixed result-kind order matching the V0 list above,
3. casefolded `title`,
4. `stable_ref`.

No BM25 score from one owner is compared numerically with a score from another owner. No LLM reranking, embeddings, vector database, fuzzy model inference, or remote search is allowed.

### Frontend

Activate the existing canonical Project-search affordance within the Memory / Project Knowledge composition without changing the 100f/100g information architecture.

Required behavior:

- one debounced or explicit-submit text input scoped to the active workspace;
- empty query shows an inert prompt, not an expensive implicit full dump;
- loading, empty, truncated and failure states are explicit;
- each result shows human title, kind/owner, a concise truthful summary and available status/version/provenance cues before machine IDs;
- selecting a result navigates only to its canonical owner route:
  - Project Basis → `/memory/project-basis`
  - Model → `/memory/models`
  - Literature → `/memory/literature`
- exact IDs needed for selection may be encoded only as bounded route/query state understood by the target surface; they do not create a frontend truth store;
- browsing/searching is context-neutral: no implicit Jarvis-context addition, proposal, canonical write, provider call or execution.

Visible work must preserve the approved 100f/100g Memory composition and be proven at the canonical Memory / Project Basis route. The relevant final-product ownership artifact explicitly assigns the Project-search left pane to 115 and leaves overall presentation with 100f/100g.

## Failure-mode requirements

Implementation must fail safely for:

- unknown workspace → canonical workspace-not-found behavior;
- blank/too-short/too-long query → 422/closed validation, no search;
- unknown result kind → 422, no silent widening;
- FTS5 unavailable → deterministic literal fallback, same result semantics;
- malformed FTS-significant characters → treated as literal text, never parser/SQL failure;
- owner read failure → request fails with an explicit bounded error rather than returning a misleading partial "complete" result;
- duplicate logical identity from one owner → deduplicate by exact `stable_ref` before global limit;
- stale/deleted result between search and navigation → target owner handles not-found/stale state; search itself never recreates data;
- result count above bound → deterministic truncation with `truncated=true`;
- hostile Literature/context strings → rendered as text; no HTML/command execution;
- workspace switching during an in-flight frontend request → stale response must not replace results for the new workspace.

## Security and authority boundaries

115 is READ/PRESENTATION only.

It must not add:

- canonical COMMIT or EXECUTE authority;
- Jarvis context mutation (owned later by 121 over 111);
- external-provider/network egress;
- web research or source ingestion;
- repository/filesystem browsing;
- secret/token handling;
- semantic/vector retrieval or LIT-RAG-0;
- background indexing daemon;
- a second workspace/project/model/literature store.

All user-supplied query text is untrusted data and must be parameterized/escaped at the owner boundary.

## Deterministic tests

Backend acceptance must cover at minimum:

1. exact workspace scope across all V0 owner families;
2. exact/prefix/contains deterministic ordering and stable tie-breaks;
3. kind filtering and global limit/truncation;
4. FTS-capable and forced-fallback behavioral equivalence for modeling records;
5. literal handling of quotes, wildcard/FTS operators, Unicode and SQL-shaped input;
6. lifecycle-current Parameter behavior;
7. exact Model Dossier version identity and route projection;
8. exact Literature source/entry provenance/locator projection;
9. no duplicate `stable_ref` results;
10. owner failure is explicit rather than silently partial;
11. no writes to 112/113/114 canonical tables during search.

Frontend deterministic acceptance must cover:

- canonical Memory routes remain unchanged;
- query lifecycle: idle/loading/result/empty/error/truncated;
- stale response rejection on query/workspace change;
- result navigation to the correct owner route with bounded exact selection identity;
- no search result action that adds Jarvis context, mutates canonical state, calls a provider or exposes direct execution.

## Exact-head browser proof

Because 115 activates a visible canonical Memory control, implementation acceptance requires a trusted exact-head Chromium plan using the generic post-143 browser-proof executor.

The task-specific declarative plan must prove on `/memory/project-basis`:

1. search input is visible and context-neutral;
2. a fixture query returns at least one Project Basis, one Model and one Literature result from real backend fixture data;
3. human title/kind/provenance or version cues render before opaque IDs;
4. one result from each domain navigates to the existing canonical owner route and preserves the intended exact selection identity;
5. a no-match query shows truthful empty state;
6. no implicit mutating same-origin request occurs during search/result navigation;
7. no Add-to-Jarvis/proposal/commit/execute affordance is introduced by 115;
8. screenshot/manifest remains exact-head bound under the existing trusted controller.

No new executor branch, arbitrary fixture script path, candidate-authored privileged code or browser-proof authority is authorized. A new 115 proof is declarative task data over the existing generic trusted primitives; if a genuinely missing closed primitive is proven, extend the generic primitive rather than add `prove115` control logic.

## Non-goals / deferred owners

- semantic/vector/RAG retrieval: 064 only after measured literal-search insufficiency;
- Project Knowledge writes/reconciliation: 112;
- Model Dossier/model writes: 112/113 existing owners;
- Literature ingestion/extraction/promotion: 114 and later 121 proposal actions;
- explicit Add to Jarvis context / Project Knowledge Jarvis actions: 121 over 111;
- generic web search/research: not 115;
- cross-workspace/global account search: not 115;
- search analytics/history/personalization: not 115.

## Implementation shape

Expected bounded implementation footprint:

- `backend/app/modules/project_search/` models/service/routes for projection only;
- minimal read-helper additions in existing modeling/Model Dossier/Literature owners where required;
- router registration in `backend/app/main.py`;
- one frontend API module and one bounded Project-search component wired into the existing Memory composition;
- deterministic backend/frontend tests;
- one trusted declarative browser-proof plan/fixture addition through the generic post-143 stack only if existing fixture vocabulary cannot express the data preparation.

Schema migration is not expected. If implementation discovers that a new persistent index/table is required for acceptable correctness or bounded latency, stop and return the spec to planning rather than silently introducing a second truth/index store.

## Readiness gates before implementation

A separate readiness decision may move 115 to `ready` only after fresh `master` confirms:

- 112, 113 and 114 are all `merged`;
- no active duplicate 115 implementation/readiness PR exists;
- the exact owner helpers and frontend insertion point still match this specification;
- no new persistent search store/migration is required;
- deterministic test and trusted browser-proof paths remain available;
- any drift from this contract is reconciled explicitly before implementation.

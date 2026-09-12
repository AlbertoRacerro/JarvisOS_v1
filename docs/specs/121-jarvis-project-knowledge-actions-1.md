# 121 — JARVIS-PROJECT-KNOWLEDGE-ACTIONS-1

Status: planning/readiness contract; implementation authority begins only after the canonical `STATUS.md` row is truthfully moved to `ready`.

## Objective

Activate the accepted 111 Jarvis context/action foundation for the three Memory knowledge routes — Project Basis, Models and Literature — so an operator can explicitly add exact current knowledge references to Jarvis context and request bounded proposal-only knowledge actions without giving Jarvis domain `COMMIT`, execution, provider, filesystem or hidden write authority.

121 is an adapter/action slice over existing owners. It does not create a second knowledge store, a second search engine, a second proposal ledger or another orchestration framework.

## Existing owners and exact routes

121 reuses, and does not replace:

- `111 JARVIS-CONTEXT-ACTION-FOUNDATION-1` for exact refs, context preview/digest/source manifest, stale refusal and route-scoped `CONTEXT` / `PROPOSE` capabilities;
- `112 PROJECT-KNOWLEDGE-CORE-1` for canonical Project Basis change-set / working-revision / reconciliation authority;
- `113 MODEL-DOSSIER-1` for exact read-only model/version/revision dossier projection;
- `114 LITERATURE-KNOWLEDGE-1` for Literature source/document/claim/datum/citation/location/used-by provenance and bounded preview/open;
- `115 PROJECT-SEARCH-1` for literal/structured read-only search results and exact owner/type/version/provenance identity.

The accepted canonical route identities are:

- `memory-project-basis` → `/memory/project-basis`;
- `memory-models` → `/memory/models`;
- `memory-literature` → `/memory/literature`.

Browsing/searching remains context-neutral. Only explicit operator selection/addition produces Jarvis context.

## Accepted capability boundary

121 adds route-scoped capabilities sufficient for:

1. **Explicit context** — action class `CONTEXT`: add one or more exact accepted refs from Project Basis, Models or Literature to the existing 111 context basket/preview.
2. **Proposal** — action class `PROPOSE`: produce an inspectable proposal grounded in the inspected exact context. A proposal may describe a Project Basis change candidate, a model-related knowledge correction/question, or a Literature research/extraction/promotion candidate, but it is never an authoritative domain mutation.

The common Jarvis registries must continue to reject `COMMIT` and `EXECUTE`. 112/114 or later accepted domain owners retain every authoritative write/promotion transition. 113 remains read-only.

No capability response is an actuator token or permission grant.

## Exact-ref and stale-safety contract

A 121 context/proposal request must preserve 111 exact identity and fail closed when identity is unknown, partial, stale or conflicting.

Minimum rules:

- `workspace_id` must match the active request workspace;
- owner/kind/id plus any owner-required exact version/revision/source identity must resolve to the same current accepted object;
- the production adapter may return only bounded serializable content/provenance allowed by its domain owner;
- context preview is inspected before proposal dispatch and carries the deterministic 111 digest/source manifest;
- immediately before model-assisted proposal generation or returning a current proposal, exact refs used by the action are re-resolved and the inspected context digest is revalidated;
- any moved/deleted/replaced/stale ref yields a typed unavailable/stale outcome and no current proposal;
- there is no retry loop that chases moving truth.

Search result stable refs from 115 may be used only after resolution through the owning 112/113/114 projection. A search hit itself is not canonical truth.

## Proposal contract

A successful proposal is ephemeral advisory output and contains at minimum:

- `state = proposed`;
- `workspace_id` and originating canonical route;
- bounded operator intent;
- ordered exact context refs actually used;
- inspected `context_digest` and source/provenance manifest;
- proposal `target_domain` in the closed set `project_basis | models | literature`;
- concise summary plus bounded proposed changes/questions/research steps;
- assumptions/warnings and the owning authoritative next action when one exists;
- generation provenance identifying deterministic/template or normal Jarvis AI-task provenance without secrets/hidden prompts.

121 adds no durable proposal table, queue or background worker. If later domain work accepts/promotes a proposal, that owner must independently re-resolve current canonical truth and enforce its own CAS/confirmation rules.

## AI / egress boundary

Deterministic context resolution/preview does not require a provider call.

When semantic proposal generation is useful, it may run only through the existing `run_ai_task` execution spine and its current routing, egress, sensitivity, accounting and budget controls. `route_class="auto"` must remain non-external. No direct provider binding, model-scoped credential, arbitrary URL fetch, crawler, filesystem read or new egress path is authorized.

Model output remains advisory and must be parsed/validated against a closed response schema before presentation as a 121 proposal.

## Minimum implementation shape

Fresh master supports a thin implementation over existing owners. The coordinator may choose adjacent files when evidence requires it, but the expected minimum is:

- domain-owned context adapters for accepted 112/113/114 exact projections, registered through the 111 production registry;
- route-scoped 111 capability descriptors for the three Memory routes;
- one bounded server-side proposal service/route that consumes an inspected 111 context request/digest and revalidates exact refs before returning;
- the existing Jarvis sidecar/context affordance wired to the three Memory routes without changing ordinary browsing semantics;
- deterministic tests for resolver identity, stale/conflict/budget/authority boundaries and proposal parsing;
- a trusted declarative Chromium proof plan exercising explicit add-to-context and proposal presentation on the real Memory/Jarvis UI.

Do not add a second router root, second project/model/literature store, semantic/vector search, crawler, generic bibliography manager, new provider/credential layer, arbitrary tool execution, repository mutation, PTY/shell, or hidden background orchestration.

## Acceptance matrix

Implementation must prove at least:

1. each of the three canonical Memory routes advertises only the accepted 121 `CONTEXT` / `PROPOSE` capability set appropriate to that route;
2. an exact current Project Basis ref resolves through 112-owned truth and is included in an inspected 111 preview with provenance and digest;
3. an exact current model/version/revision ref resolves through the 113 projection without granting model mutation;
4. exact Literature source/entry/claim/datum refs resolve through 114 provenance with bounded content;
5. workspace mismatch, unknown kind/id, moved revision/version/source, deleted/replaced target or conflicting exact identity fails closed;
6. a 115 search hit cannot bypass owner resolution or become context implicitly;
7. duplicate/conflicting refs and over-budget evidence preserve existing deterministic 111 behavior;
8. semantic proposal generation, when used, goes only through `run_ai_task` and normal AI-job/accounting policy;
9. malformed/oversized/out-of-schema model output is refused without leaking raw provider errors or secrets;
10. a returned proposal is ephemeral and exposes no direct domain commit/promotion/apply/execute actuator;
11. no `COMMIT` or `EXECUTE` capability is registered by 121;
12. removing 121 leaves 111–115 authoritative behavior and stores unchanged;
13. frontend browsing/search remains context-neutral until the operator explicitly adds a ref;
14. trusted Chromium proof on the exact candidate head demonstrates, on at least Project Basis and one of Models/Literature, explicit add-to-context → inspected source/digest → proposal display, with no direct domain mutation affordance and no unexpected same-origin mutation during the proof journey.

## Non-goals

- no direct Project Basis, model or Literature `COMMIT`/promotion;
- no semantic/vector/RAG search or 064 activation;
- no autonomous literature crawler/research lane or arbitrary remote URL fetch;
- no OCR/LLM extraction requirement beyond existing 114 proposal boundaries;
- no second files, engineering-memory, project, model or literature store;
- no new provider, credential, budget, shell, filesystem, GitHub/repository or desktop authority;
- no redesign of Memory surfaces unrelated to the explicit Jarvis context/proposal affordance;
- no Hermes runtime/re-derivation.

## Readiness decision — 2026-09-12

Readiness was derived from exact fresh master `cb7f95af101a675911eed0803fe13192715514a5`.

Fresh evidence confirms:

- canonical `STATUS.md` has 121 `planned` with hard dependencies 111–115, and every one of those dependencies is `merged`;
- no existing open 121 PR or branch exists, so there is no implementation lane to recover instead;
- 111 already provides canonical route identities, exact refs, bounded context preview/digest/source manifest, stale/conflict refusal, a production adapter registry and a capability registry that rejects `COMMIT`/`EXECUTE`;
- the production 111 adapter/capability registries are intentionally still empty for these knowledge domains, which is the missing activation 121 is defined to own;
- 112/113/114/115 already own the required Project Basis, model dossier, Literature provenance and literal-search truth, so 121 needs adapters/actions rather than new storage;
- current project-search results already carry domain owner/kind/stable-ref identity (including Literature owner refs), allowing explicit search-to-context resolution without making search canonical authority;
- canonical frontend routes already include `memory-project-basis`, `memory-models` and `memory-literature`.

### Failure-mode disposition

- **Implicit context from browsing/search:** closed by explicit-add-only acceptance and browser proof.
- **Stale exact ref between preview and proposal:** closed by pre-dispatch re-resolution + digest revalidation.
- **Search projection mistaken for canonical truth:** closed by mandatory owner resolution.
- **Jarvis proposal launders write authority:** closed by proposal-only schema and no `COMMIT`/`EXECUTE` registration/actuator.
- **Provider/egress bypass:** closed by `run_ai_task` only and existing policy spine.
- **Secret/unbounded disclosure:** closed by owner-bounded projections, 111 evidence budgets and validated proposal output.
- **Shadow proposal store/queue:** closed by ephemeral response-only contract.
- **Need for semantic/RAG retrieval:** not demonstrated; PARK under the existing 064 trigger rather than widening 121.

### Minimum-necessary test

Criterion: make accepted Project Basis / Models / Literature truth explicitly usable by Jarvis for exact context and proposal-only actions.

- Is 121 necessary? **Yes.** Fresh production 111 registries deliberately contain no domain adapters/capabilities, so the accepted knowledge owners are not yet activated through the common Jarvis contract.
- Can the criterion be met without new stores/provider writers/orchestrators? **Yes.** Reuse 111–115 and add only thin adapters/actions/UI affordance plus deterministic/browser evidence.
- Concrete risk justifying new surface: without the bounded adapters/actions, Jarvis either cannot consume the accepted knowledge surfaces or a future implementation would be tempted to bypass exact refs/domain authority with ad-hoc page logic.

No unresolved destructive migration, credential, spend, repository-permission or security-boundary choice remains. Therefore the accepted contract is **ready for implementation once the canonical registry is truthfully transitioned from `planned` to `ready`**. This document alone does not perform that registry transition.
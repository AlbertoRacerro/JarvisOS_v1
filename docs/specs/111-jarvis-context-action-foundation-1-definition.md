# 111 JARVIS-CONTEXT-ACTION-FOUNDATION-1 — definition

Exact source master: `f0c80a901696144fe3b0f587c2dbaee3b7b4de2a`.

Authority: definition only. This document does not authorize runtime implementation and does not change the live `111` registry row from `planned`.

Governing planning authority:
- `docs/specs/100c-queue-rederivation-2026-08-28.md`;
- `docs/audits/100c-final-product-direction-overlap-audit-f50eb0a.md`;
- `docs/audits/100c-final-capability-interaction-ownership-f50eb0a.md`;
- merged 040/042 proposal/canonical-state boundaries;
- merged 059b/061a/061b AI policy/egress/budget foundations;
- merged 090 AI threads, 091 Jarvis sidecar, and 097 stale-safe engineering actions.

## Problem

Jarvis already has visible sidecar/thread/action pieces, but the final product queue now needs one stable cross-domain contract between operator pages and the current AI execution/policy spine. Without that contract, Project Knowledge, Development and Coding could each invent page-specific context shapes, implicit browsing-to-context behavior, duplicate orchestration state, or domain mutation authority inside Jarvis.

The foundation must therefore make Jarvis useful before any Hermes release while preserving the future replacement seam: `Pages -> stable Jarvis Context/Action contracts -> Jarvis service/policy -> current AI runtime now / Hermes adapter later`.

## Definition boundary

111 owns only the common context/action mechanics shared by later domain adapters.

It MUST define:

1. **Workspace identity** — every Jarvis request is bound to one exact workspace identity already owned by the server; no browser-owned workspace truth.
2. **Route descriptor** — a stable, bounded descriptor for the active operator surface/mode that carries presentation/context identity but no page-specific business logic.
3. **Exact selected references** — typed references to the currently selected domain object using its real owner identity and exact revision/version/ref where that owner exposes one. Unknown version identity remains Unknown rather than guessed.
4. **Explicit added-context basket** — removable references added only by an explicit operator CONTEXT action. Browsing, opening, focusing or selecting never adds them implicitly.
5. **Inspected preview + digest** — before context leaves its owner boundary, the operator can inspect the bounded material and its deterministic digest/identity. The preview is evidence for what will be sent, not a second canonical copy.
6. **Provenance/source manifest** — each context item records owner/type/id/version/ref plus source/provenance information available from its domain owner.
7. **Fail-closed stale references** — if owner identity/version/digest no longer matches, the item cannot silently refresh or execute as if current. It must surface stale/unavailable and require an explicit re-add/review flow.
8. **Generic capability/action registry** — typed declarations of what Jarvis may READ/CONTEXT/PROPOSE for the active surface and selected refs. Domain owners remain the source of truth for admissibility and COMMIT/EXECUTE.
9. **Jarvis service/policy adapter** — one backend-owned assembly/validation seam that consumes these contracts and delegates inference through the existing AI execution/policy/egress/provider spine. No provider call or orchestration logic is added to the frontend.

## Action-class ownership

The final interaction action classes remain binding:

- `PRESENTATION`: page/component only; no context or canonical mutation.
- `READ`: domain-owned read; inert with respect to Jarvis context.
- `CONTEXT`: explicit add/remove/inspect of bounded exact refs through 111.
- `PROPOSE`: Jarvis may return typed proposals through existing proposal/thread/action evidence boundaries; proposal is not canonical state.
- `COMMIT`: never owned by 111. The target domain validates and commits.
- `EXECUTE`: never owned by 111. The target domain/execution owner gates and executes.
- `NAVIGATE`: presentation/navigation only; no implicit context addition.

## Required invariants

- No second orchestration store, conversation truth store, project-memory store or generic domain database.
- No Hermes runtime, Hermes schema, MCP server, agent swarm, vector database or new provider path.
- No page-specific Project Basis, Literature, Roadmap, Brainstorm, Repository, Runtime, BLUECAD or Process business logic inside the common Jarvis service.
- No canonical domain mutation from model output. Model output remains proposal until domain-owned explicit/deterministic promotion.
- No frontend direct provider/GitHub/filesystem/shell/process access.
- No silent context mutation on route change, browser selection, opening a record, expanding a disclosure, previewing a file or navigating to another surface.
- No invented `current`, `aligned`, `valid`, `ready`, confidence, cost, provenance or version metadata.
- Existing safe provider defaults, budgets, egress controls, AI-job ledger and audit spine remain authoritative.

## Reuse / current-owner obligations for full-spec derivation

The next full-spec pass must resolve exact current code seams on the then-current master and prefer reuse over replacement, including:

- current AI task execution / `run_ai_task` path and `ai_jobs` ledger;
- current context-pack/context-builder structures and their sensitivity/egress handling;
- current AI thread persistence from 090;
- current Jarvis sidecar/frontend seam from 091/100f/100g;
- current structured proposal/action preview/apply boundaries from 054/097;
- workspace, engineering-record, modeling, file/source and selected-object identities already owned by their modules.

Where an existing structure cannot satisfy an 111 contract, the full spec must document the exact mismatch and choose the smallest additive/replaceable seam rather than creating a parallel owner.

## Acceptance criteria for the future full spec/readiness

Before 111 can become `ready`, the exact-master full spec/readiness must prove all of the following:

1. every proposed persistent field/state has exactly one owner and no second truth store is introduced;
2. route, selection and added-context are distinct states;
3. added-context refs carry exact owner identity and fail closed when stale;
4. preview/digest/source manifest are deterministic and inspectable before AI execution;
5. capability/action declarations cannot grant COMMIT/EXECUTE to Jarvis;
6. current AI execution, budget, provider, egress and ledger boundaries are reused;
7. frontend calls only typed Jarvis/domain backend endpoints, never providers/tools directly;
8. deterministic tests cover implicit-browsing rejection, explicit add/remove, stale refs, digest mismatch, missing owner/version, unauthorized action class, proposal-vs-commit separation and safe-default provider behavior;
9. any visible activation on the eleven canonical surfaces preserves 100f/100g composition and uses exact-head browser proof; purely backend/common-contract work must not redesign those surfaces;
10. every canonical control not activated by 111 is explicitly deferred to its 112–126 or late engineering owner.

## Non-goals

- Project Basis CRUD/reconciliation/revalidation (`112`).
- Model dossiers (`113`).
- Literature ingestion/claims/preview/search (`114/115`).
- Roadmap/Calendar/Brainstorm persistence (`116/117`).
- Repository/Runtime/development pipeline truth (`118–120`).
- Provider-settings expansion (`124`).
- Domain-specific Jarvis actions (`121–123`).
- Self-update or PTY (`125/126`).
- Process topology/solver semantics or BLUECAD reimplementation.
- Hermes 066–068/080 release.

## Minimum-necessary test

Criterion: establish one stable, stale-safe, inspectable common Jarvis context/action contract before later domains expose Jarvis actions.

This definition is necessary because later domain slices otherwise need to invent the same context/action semantics independently. It remains documentation-only and deliberately stops before choosing exact runtime files, schemas or endpoints; those must be derived from fresh code in the full-spec/readiness steps.

# 100c final product direction overlap/ownership audit — exact master `f50eb0a`

Audited source SHA: `f50eb0a1f5b246d5e6f6eabab3a033e9a8c5a5c5`.

This is the exact-master authority audit required by `100c FINAL-PRODUCT-DIRECTION-AUTHORITY-0`. It is planning/queue authority only. It changes no runtime behavior and grants no implementation authority by itself.

## 1. Governing conclusions

1. **Jarvis common context/action contracts come before Hermes.** The stable boundary is `Pages -> Jarvis Context/Action contracts -> Jarvis service/policy -> current AI execution spine today / Hermes adapter later`. Existing `run_ai_task`, AI threads, context-pack, egress/policy/budget/provider gateway, proposal/promotion and audit boundaries remain canonical. No second orchestration store is authorized.
2. **Domain owners keep COMMIT/EXECUTE.** Jarvis may READ/CONTEXT/PROPOSE; Project Knowledge, Development, Coding and engineering domains own canonical data, deterministic validation and mutation/execution.
3. **Opening/browsing never adds Jarvis context.** Added context is explicit, removable, exact-identity bound, previewable and stale-fail-closed.
4. **The eleven 100f/100g surfaces remain composition authority.** Later slices activate truthful data/actions inside them; they do not redesign navigation or recreate peer pages.
5. **Project Knowledge precedes Development, which precedes Coding, then domain-specific Jarvis action extensions. Design/Process remains last.** BLUECAD merged capability is preserved throughout.
6. **No current consumer is not deletion authority.** Desired-but-unwired capability is retained, merged into a later owner, or trigger-deferred.
7. **No new generic evidence/search/vector/provider state is introduced unless a later full spec proves minimum necessity.** Existing SQLite, MemoryStore, modeling, events, files, FTS/search, AI execution, provider/security and BLUECAD owners are reused first.

## 2. Exact-master ownership observations

The exact tree continues to expose the accepted ownership families already recorded by merged specs and `AGENTS.md`: FastAPI + SQLite backend authority; `backend/app/modules/ai` for the AI execution/policy spine; merged MemoryStore/context-pack/engineering-record lifecycle for canonical/proposed engineering records; modeling/runs/evidence/flowsheet dependencies for exact model/run/evidence identity; events/files for event and file boundaries; BLUECAD for CAD artifacts/validation; and the React/Vite frontend as operator interface only.

The audit does **not** infer that a candidate module is sufficient merely because a path exists. Each promoted slice must re-read exact code and prove the concrete service/table/API owner during its own definition/readiness.

## 3. FV backend/domain draft disposition

| Draft | Disposition | Canonical owner after 100c | Reason |
| --- | --- | --- | --- |
| FV-B01 PROJECT-BASIS-1 | `MERGE_WITH_DRAFT` | 112 PROJECT-KNOWLEDGE-CORE-1 | Same canonical record/write/revalidation owner as B03/B04/B05; avoid a second project-basis store. |
| FV-B02 MODEL-DOSSIER-1 | `PROMOTE_SEPARATE` | 113 MODEL-DOSSIER-1 | Read aggregation is independently removable and must not own canonical model writes. |
| FV-B03 MODEL-CHANGESET-1 | `MERGE_WITH_DRAFT` | 112 | Working revisions are part of the same canonical project/model write boundary. |
| FV-B04 DETERMINISTIC-IMPACT-REVALIDATION-1 | `MERGE_WITH_DRAFT` | 112 | Revalidation is a write/change-state invariant, not a separate truth store. |
| FV-B05 MODEL-RECONCILIATION-1 | `MERGE_WITH_DRAFT` | 112 | Promotion/reconciliation must be atomic with the same revision owner. |
| FV-B06 LITERATURE-SOURCE-1 | `PROMOTE_SEPARATE` | 114 LITERATURE-KNOWLEDGE-1 | Structured provenance/import/claim usage is independently removable while bridging existing source/file owners. |
| FV-B07 PROJECT-SEARCH-1 | `PROMOTE_SEPARATE` | 115 PROJECT-SEARCH-1 | Search is a read projection and must remain non-authoritative. |
| FV-B08 ROADMAP-1 | `MERGE_WITH_DRAFT` | 116 ROADMAP-CALENDAR-1 | Roadmap and Calendar need one work-item owner with separate time-allocation entities. |
| FV-B09 CALENDAR-SCHEDULING-1 | `MERGE_WITH_DRAFT` | 116 | Separate Calendar blocks, same project-planning ownership boundary. |
| FV-B10 BRAINSTORM-RECONCILIATION-1 | `PROMOTE_SEPARATE` | 117 BRAINSTORM-1 | RAW/reconciled lineage and explicit promotion form a distinct domain. |
| FV-B11 DEVELOPMENT-JARVIS-CONTEXT-ACTIONS-1 | `MERGE_INTO_EXISTING` | 122 JARVIS-DEVELOPMENT-ACTIONS-1 | Generic contract belongs to 111; Development-specific actions wait for 116/117. |
| FV-B12 PROVIDER-SETTINGS-GENERIC-1 | `PROMOTE_SEPARATE` | 124 PROVIDER-SETTINGS-GENERIC-1 | Reuse 015/018/082/094/policy owners; no model-scoped credentials. |
| FV-B13 REPOSITORY-OBSERVABILITY-1 | `MERGE_WITH_DRAFT` | 118 CODING-REPOSITORY-TRUTH-1 | Remote repo facts and inspector reads share one server-side GitHub truth boundary. |
| FV-B14 REPOSITORY-INSPECTOR-1 | `MERGE_WITH_DRAFT` | 118 | Search/preview is a bounded read projection over exact ref/path/blob identity. |
| FV-B15 DEV-PIPELINE-STATE-1 | `PROMOTE_SEPARATE` | 120 DEVELOPMENT-PIPELINE-STATE-1 | Software-development lifecycle state is distinct from GitHub read truth. |
| FV-B16 JARVIS-CODING-ACTIONS-1 | `PROMOTE_SEPARATE` | 123 JARVIS-CODING-ACTIONS-1 | Domain-specific PROPOSE/actions wait for Coding truth owners. |
| FV-B17 CODING-KNOWLEDGE-1 | `MERGE_WITH_DRAFT` | 118 | Specs/ADR/architecture remain repository artifacts; no separate magical memory store. |
| FV-B18 LOCAL-RUNTIME-IDENTITY-1 | `MERGE_WITH_DRAFT` | 119 CODING-RUNTIME-TRUTH-1 | Local executed identity and divergence require one observer/read boundary. |
| FV-B19 RUNTIME-DIVERGENCE-SUMMARY-1 | `MERGE_WITH_DRAFT` | 119 | Delta is evidence derived from the same local/remote exact identities. |
| FV-B20 SAFE-SELF-UPDATE-1 | `PROMOTE_SEPARATE` | 125 SAFE-SELF-UPDATE-1 | Mutation/restart/rollback authority must remain separate from observation. |
| FV-B21 LOCAL-TERMINAL-PTY-1 | `PROMOTE_SEPARATE` + security-gated | 126 LOCAL-TERMINAL-PTY-1 | Separate typed PTY/session authority; readiness forbidden until secret-safe local security boundary is proven. |
| FV-B22 BRAINSTORM-SPEECH-CAPTURE-1 | `DEFER_TRIGGERED` | no live implementation row yet | Reopen only after 117 is merged and a bounded media path + canonical `run_ai_task` transcription contract is justified. |
| FV-B23 ARCHITECTURE-SEMANTIC-ARTIFACT-1 | `REFERENCE_ONLY` / future trigger | 118 inspection for current SVG/Markdown; semantic graph later | Existing architecture artifacts remain inspectable; no semantic graph store without demonstrated need. |

## 4. FV frontend draft disposition

100f/100g already own final composition. No FV-F draft becomes an independent visual-redesign slice.

| Draft | Disposition / owner |
| --- | --- |
| FV-F01 FINAL-APP-SHELL-RECONCILIATION-1 | `REFERENCE_ONLY`; already delivered by 100f/100g. |
| FV-F02 DESIGN-FINAL-COMPOSITION-1 | `REFERENCE_ONLY` until late engineering owners activate currently unavailable Process actions; BLUECAD remains existing authority. |
| FV-F03 MEMORY-PROJECT-BASIS-UI-1 | activation obligations merge into 112; Jarvis actions into 121. |
| FV-F04 MEMORY-MODELS-UI-1 | activation obligations merge into 113; write/revision actions remain 112. |
| FV-F05 MEMORY-LITERATURE-UI-1 | activation obligations merge into 114/115; context actions into 121. |
| FV-F06 ROADMAP-TIMELINE-UI-1 | activation obligations merge into 116. |
| FV-F07 ROADMAP-CALENDAR-UI-1 | activation obligations merge into 116. |
| FV-F08 BRAINSTORM-UI-1 | activation obligations merge into 117; Jarvis actions into 122. |
| FV-F09 SETTINGS-FINAL-UI-1 | composition stays 100f/100g; truthful provider/system activation merges into 124. |
| FV-F10 CODING-REPOSITORY-UI-1 | activation obligations merge into 118/120/123. |
| FV-F11 CODING-RUNTIME-UI-1 | read activation merges into 119; update action into 125. |
| FV-F12 INTEGRATED-TERMINAL-UI-1 | deferred until 126 backend/security readiness; no mock terminal. |
| FV-F13 REPOSITORY-SUGGEST-MODIFICATION-UI-1 | merges into 123, using exact artifact identity from 118. |
| FV-F14 RUNTIME-UPDATE-UI-1 | merges into 125 after 119. |
| FV-F15 ARCHITECTURE-INSPECTION-UI-1 | merges into 118 read/preview; semantic editing remains deferred. |

## 5. Overlapping live/planned STATUS rows

| Existing row | Disposition | 100c result |
| --- | --- | --- |
| 011 Core Team review panel | `DEFER_TRIGGERED` | Advisory personas are not a prerequisite for useful Jarvis. |
| 012 L2 ephemeral scripts | `DEFER_TRIGGERED` | Keep existing non-loopback/remote-runner trigger. |
| 013 validator plugin | `DEFER_TRIGGERED` | Reopen only for a concrete domain validator not expressible in accepted evaluator boundaries. |
| 014 OpenFOAM CFD | `DEFER/REORDER` | Preserve as a possible later 110 multifidelity adapter, not an early queue front. |
| 023 adversarial proposal corpus | `RETAIN/REORDER` | Useful hardening evidence; not a prerequisite to 111. |
| 025 routing evaluation | `DEFER_TRIGGERED` | Requires representative graded dogfood; no routing authority expansion now. |
| 026 BoardSession | `DEFER_TRIGGERED` | No early multi-persona state owner. |
| 027 modal/thermal | `DEFER_TRIGGERED` | Reopen only for a concrete engineering decision. |
| 028 additive migration discipline | `RETAIN AS CROSS-CUTTING REQUIREMENT` | Schema-growing specs must satisfy additive migration tests; no separate urgent front. |
| 031 design vocabulary | `MERGE` | Bounded capability/action registry obligations merge into 111. |
| 032 Core Team critique | `DEFER_TRIGGERED` | Wait for 011. |
| 033 reusable part-kind proposal | `DEFER_TRIGGERED` | Remains downstream of real BLUECAD/design need. |
| 034 persona policy metadata | `MERGE/DEFER` | Generic capability/advisory metadata needed by 111; multi-persona expansion deferred. |
| 036 orchestrator status UI | `MERGE` | Honest current policy/capability projection belongs to 111/124; no Hermes claim. |
| 039 frontier provider route | `DEFER_TRIGGERED` | Existing provider/egress policy remains sufficient until an explicit provider need. |
| 046 alternative design loop | `DEFER/REORDER` | Design/process work is last. |
| 053 decision dossier export | `RETAIN/DEFER` | Reopen after Project Knowledge has stable canonical dossier/evidence identities. |
| 055 project view | `CANCEL/SUPERSEDE` as standalone | 100f/100g composition + 112/113/114/115 own the required projections without a second project store. |
| 059 IP-EGRESS umbrella | `RETAIN` definition-only | Existing 059a/059b remain runtime authority. |
| 060 Hermes umbrella | `DEFER_TRIGGERED` | Jarvis service/contracts land first; Hermes later only behind adapter. |
| 061 TOKEN-FLOW umbrella | `RETAIN` definition-only | Existing 061a/061b remain runtime authority. |
| 063 CAPTURE-VAULT | `DEFER_TRIGGERED` | Do not create markdown/vector parallel memory before literal/project search proves insufficient. |
| 064 LIT-RAG | `MERGE/DEFER_TRIGGERED` | Future semantic retrieval belongs behind 115/114 after evidence; cancel standalone early implementation intent. |
| 065 provider-family hook | `DEFER_TRIGGERED` | Not needed by 124 baseline settings/provider truth. |
| 066–068 Hermes slices | `FROZEN` | Explicitly remain frozen. |
| 069 memory consolidate | `DEFER_TRIGGERED` | Reopen only after Hermes is explicitly unfrozen; must reuse canonical MemoryStore/proposal semantics. |
| 080 autonomous review-repair | `FROZEN` | No change. |
| 081/095 authority definitions | `RETAIN HISTORICAL AUTHORITY` | No implementation PR. |
| 093 serial topology | `RETAIN/REORDER` | Late Design/Process work after 103 and 109; no early topology authority. |
| 101 CANONICAL-STATE-WRITE-1 | `REDERIVE/MERGE` | Superseded as a standalone by 112, which preserves 040/042/071b/098 ownership and adds final Project Knowledge revision/revalidation obligations. |
| 102 ENGINEERING-EVIDENCE-CONTRACT-1 | `REDERIVE/REORDER` | Keep as later cross-engineering evidence generalization after operator-domain foundations; existing 044/077 remain valid. |
| 103–110 | `RETAIN/REORDER` | Preserve zero-sunk-cost upstream bakeoff/evaluator/study/CAD/multifidelity sequence, but move the whole engineering/process block after Jarvis, Project Knowledge, Development and Coding foundations. |

## 6. Capability-matrix final ownership

The capability matrix is consumed by section, with no dropped row:

- **Global shell/truth:** existing 100f/100g composition; 111 owns explicit Jarvis context/capability contract; existing proposal/promotion owners remain authoritative.
- **Design Process/BLUECAD:** existing BLUECAD owners stay live; Process editing/validation/solve remain unavailable until late 103–110/093 re-derivation supplies real authority. 111 supplies only context/action contracts, never topology.
- **Memory Project Basis:** 112 owns canonical basis/change/revision/revalidation/reconciliation; 115 owns search; 121 owns explicit Jarvis context/proposal actions.
- **Memory Models:** 113 owns exact-version read dossier; 112 owns working/reconciled revision mutation; 121 owns Jarvis actions.
- **Memory Literature:** 114 owns structured source/import/claim/provenance and bounded preview reads; 115 search; 121 context/proposals.
- **Development Roadmap/Calendar:** 116 owns work items, deterministic status gates and separate real time blocks; 122 Jarvis scheduling/proposals.
- **Development Brainstorm:** 117 owns RAW/reconciled lineage and explicit promotions; 122 owns Jarvis context/proposals; speech remains trigger-deferred.
- **Settings:** existing appearance/security/provider spine remains; 124 owns provider/integration-generic read/write/test/catalogue/budget/system projections where supported.
- **Coding Repository:** 118 owns server-side remote truth, safe search/preview and architecture/code/spec inspection; 120 owns development lifecycle projection; 123 owns modification proposals/context actions.
- **Coding Runtime:** 119 owns local executed identity/alignment/delta; 125 owns update/restart/rollback; 126 owns terminal only after explicit security readiness.

Every capability stays either implemented by a merged owner, assigned above, or explicitly trigger-deferred; fixture-only canonical HTML values remain non-authoritative.

## 7. Interaction-contract ownership

The seven action classes remain unchanged:

- `PRESENTATION`: 100f/100g and local UI state only.
- `READ`: owning domain read services (112–120/124, existing BLUECAD/modeling owners).
- `CONTEXT`: generic exact-ref mechanics in 111; domain-specific admissible refs/actions in 121–123. Browsing is never CONTEXT implicitly.
- `PROPOSE`: existing proposal/AI execution spine through 111 service contracts plus 121–123 domain adapters; model output never mutates canonical state.
- `COMMIT`: domain owners only — 112, 116, 117, 124 and later engineering owners as explicitly defined by their full specs.
- `EXECUTE`: existing approved execution owners, 125 update authority, 126 PTY authority, and late engineering evaluators; never browser-owned.
- `NAVIGATE`: existing router/safe URL owners; exact repository URLs in 118.

## 8. Eleven-surface conformance map

| Canonical surface | Default render | READ owner | CONTEXT/PROPOSE owner | COMMIT/EXECUTE activation |
| --- | --- | --- | --- | --- |
| Design / Process | 100f/100g | existing truthful projections; late engineering specs | 111 then late engineering Jarvis adapter | late 103–110/093 only |
| Design / BLUECAD | 100f/100g + merged BLUECAD | existing BLUECAD/model/run owners | 111 + existing/late engineering Jarvis adapter | existing accepted BLUECAD actions only; no fake new CAD action |
| Memory / Project Basis | 100f/100g | 112/115 | 121 | 112 |
| Memory / Models | 100f/100g | 113 | 121 | 112 for revision/reconciliation |
| Memory / Literature | 100f/100g | 114/115 | 121 | 114 where import/record mutation is explicitly specified |
| Development / Roadmap | 100f/100g | 116 | 122 | 116 |
| Development / Calendar | 100f/100g | 116 | 122 | 116 |
| Development / Brainstorm | 100f/100g | 117 | 122 | 117 |
| Coding / Repository | 100f/100g | 118/120 | 123 | no direct file commit; modification enters development lifecycle |
| Coding / Runtime | 100f/100g | 119 | 123 context/explain | 125 update; 126 terminal EXECUTE only after security proof |
| Settings | 100f/100g | existing + 124 | existing Jarvis only where policy allows | 124 backend-mediated provider/settings actions |

Exact canonical HTML path/hash/browser proof obligations remain those in the 2026-08-27 manifest and promotion contract for every later user-facing mutation.

## 9. Rejected architecture shortcuts

- No page-specific Jarvis business logic or second Jarvis store.
- No Hermes-first orchestration rewrite.
- No project-basis/model/literature duplicate canonical databases solely to match the HTML.
- No vector database by default for 115.
- No frontend GitHub token, filesystem, shell or provider access.
- No browser-owned Roadmap/Calendar/Brainstorm canonical state.
- No self-update mixed into runtime observation.
- No terminal mixed into self-update or exposed without the no-secret PTY boundary.
- No Process topology/solver semantics inferred from visual affordances.

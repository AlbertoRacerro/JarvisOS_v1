# Final operator capability matrix — 2026-08-27

Status: maintainer-approved capability preservation map; planning evidence only; not a parallel queue and not implementation authority.

## Purpose

Ensure that every capability approved during the final operator-workstation inspection survives implementation planning even when the current backend cannot yet support it. This matrix links the visible product behavior to candidate backend/domain ownership and the pseudo-spec families in `FINAL_VISUAL_IMPLEMENTATION_PACK_2026-08-27.md`.

`100c FINAL-PRODUCT-DIRECTION-AUTHORITY-0` must audit exact post-100a/100b master, replace candidate ownership with the minimum real canonical ownership, merge overlapping pseudo-specs where appropriate, and allocate the binding spec queue. It may not silently drop a capability merely because current code does not expose it.

Legend:

- **Existing candidate to audit** means current JarvisOS appears to have relevant records/modules, but 100c must prove the exact canonical owner before promotion.
- **New/rederived owner** means no current owner should be assumed from this planning file.
- FV identifiers are pseudo-spec references only.

## Global shell and truth rules

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft / reference | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| Primary workspace rail | Exactly `Design | Memory | Development | Coding | Settings`; workspace selection persists through normal routing/history | existing frontend router/shell | none independent | FV-F01 | no Home or legacy peer destination may be reintroduced as a shortcut |
| Shared appearance language | Warm limestone/light-first shell; Inter regular/medium; IBM Plex Mono for code/log/path/hash; Phosphor generic icons | appearance/settings + frontend tokens | existing appearance owners / FV-B12 only where settings data required | FV-F01, FV-F09 | styling is not a reason to invent domain state |
| Jarvis context/actions | Visible context is explicit, removable and bound to real records/refs | existing AI/context/proposal spine to audit | FV-B11/FV-B16 where domain-specific | F03/F05/F08/F10/F11 as applicable | browsing alone never silently expands authority/context |
| Proposal vs canonical state | Jarvis/model output remains proposal until explicit user/deterministic policy promotion | existing AI jobs/proposal/events/decision boundaries | reused/rederived by owning slices | all action UIs | `agent/model proposal != canonical state mutation` |

## Design — Process / BLUECAD

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| Design peer modes | Only `Process | BLUECAD` as peer modes | existing frontend Design shell | existing Process/BLUECAD capability owners + 100c overlap audit | FV-F02 | Models/Results/Runs/Evidence/Review/Lineage stay contextual, not peer pages |
| Design context strip | Current model/version, current state, last run, proposal count, source count where available | modeling/runs/proposals/source records | existing owners; 100c rederive read projection | FV-F02 | counts/status must derive from exact records, never demo fixture |
| Process editing surface | Aspen-like engineering workbench composition represented by approved Process HTML, with equipment/library/canvas and right Jarvis/Properties language | existing Process/modeling/engineering modules; planned 101–110 | 100c must map to retained engineering specs rather than invent duplicate model store | FV-F02 | visual reference does not itself authorize solver/topology semantics absent from active specs |
| Process Properties | Selected object exposes editable truthful property fields and units where backend supports them | modeling/engineering parameter owners | existing/rederived | FV-F02 | property edits follow canonical proposal/write authority; no frontend-only values |
| BLUECAD editing surface | Approved BLUECAD technical/CAD composition, with shared shell/right interaction language and CAD-specific tools | existing BLUECAD/CAD bridge/tool owners | existing/rederived; 100c overlap with 103–110 | FV-F02 | no fake CAD operation/artifact/validation |
| Design proposals | Jarvis may propose bounded engineering changes; operator inspects/accepts under owner policy | existing proposal/event/modeling owners | overlap with FV-B03/B04/B05 where model changes apply | FV-F02/F03 | proposed change is not current model until promotion |

## Memory — Project Basis

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| Project search left pane | Search project memory without creating a second truth store | existing FTS/index/search infrastructure | FV-B07 | FV-F03/F05 | search result must return exact owner/type/version/provenance |
| Project Basis dossier | Objective/question, requirements, acceptance criteria, stable constraints, global decisions, boundary conditions, standards/regulations, resources/capabilities | requirements/assumptions/parameters/decisions/workspace records | FV-B01 | FV-F03 | no per-model duplicate basis records solely for UI |
| Value / rule / threshold display | Compact item exposes exact value/rule/threshold and item state where record supports it | canonical requirement/parameter/criterion records | FV-B01 | FV-F03 | labels/state derive from backend records |
| Proposed basis change | Jarvis may propose one or a bounded batch of changes; diff remains inspectable before approval | proposal/event/change-set owners | FV-B03 plus FV-B01 | FV-F03 | no direct overwrite from chat response |
| Deterministic immediate re-evaluation | Criterion/rule-only change checks exact stored outputs immediately when sufficient | modeling/results/validation evidence | FV-B04 | FV-F03/F04 | no generic `Validate` and no LLM confidence when deterministic evidence is sufficient |
| Recalculation required | UI states exact affected domain and contextual `Validate in Process/BLUECAD` when recomputation is genuinely required | dependency/freshness/validation owners | FV-B04 | FV-F03/F04 | `STALE` reserved for actual recomputation requirement |
| Working revisions | Accepted changes create inspectable `v13.01`, `v13.02`-style working revisions from exact parent | model-version/change-set owner | FV-B03 | FV-F03/F04 | no floating-point identity or in-place overwrite |
| Reconciliation | Validated working revision can become current reconciled model while history remains immutable | model version/promotion owner | FV-B05 | FV-F04 | known FAIL only via explicit acknowledgement/policy where allowed |

## Memory — Models

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| Exact model/version dossier | One selected version owns Definition, Assumptions, Methods & Equations, Parameters & Inputs, Process, BLUECAD, Results & Validation, Criticalities, Sources, Artifacts, Runs, Changelog/Lineage | modeling versions/runs/artifacts/requirements/sources | FV-B02 | FV-F04 | every result/run/artifact remains bound to exact version |
| Overview-first disclosure | Compact truthful section count/status/summary; bounded expand/collapse; `Collapse all` | read projection over canonical owners | FV-B02 | FV-F04 | collapsed summary is derived, not generated filler |
| Large-section scaling | pagination/filter/internal scrolling/virtualization as needed | existing query/read APIs | FV-B02 | FV-F04 | one expanded section must not make entire workspace unbounded |
| Current vs working revision identity | reconciled and working revision visibly distinct | model/change-set owner | FV-B03/B05 | FV-F04 | no ambiguous “current” when a working revision is selected |

## Memory — Literature

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| Compact source/file list | User sees source title/file with compact state and can expand inline | files/source_ref/current source metadata to audit | FV-B06 | FV-F05 | backend taxonomy need not be forced into compact row |
| Inline multi-expand | Multiple records can remain open while vertical list continues | frontend presentation over source read model | FV-B06 | FV-F05 | opening one record does not replace Memory route |
| Extracted knowledge | Claim/datum/value/unit/context/status/exact source location and used-by links | source/document/claim/citation model to rederive around existing `source_ref` | FV-B06 | FV-F05 | extracted values require provenance |
| Bounded preview | PDF relevant page, image, Markdown/text or supported file preview on right | file/source read boundary | FV-B06 plus existing files | FV-F05 | no invented preview; unsupported file is truthful unavailable |
| Open full source | Browser/native viewer opens original/imported source without losing Memory state | files/source URL owner | FV-B06 | FV-F05 | direct URL/path must be safe and real |
| Web finding promotion | web finding is non-authoritative until extracted/proposed/reviewed/promoted | source/proposal owners | FV-B06 | FV-F05 | browsing result alone is not canonical project fact |

## Development — Roadmap / Timeline / Execution status

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| Canonical Roadmap work item | title/type/start/end/status/priority/description/domain/links/dependencies/scheduling constraints/done-when/tags/owner/effort/progress/subtasks/resources/cost/notes/attachments/provenance | events/decisions/workspace records may provide parts; exact owner to rederive | FV-B08 | FV-F06 | one item identity across all views; no separate Board store |
| Timeline | project window, workstreams, dependency/milestone planning, zoom and filters | Roadmap owner | FV-B08 | FV-F06 | Timeline means project schedule, not actual occupied hours |
| Execution status under Timeline | collapsible `Ready | In progress | Blocked`, Planned/Completed secondary/filterable | same Roadmap status field | FV-B08 | FV-F06 | standalone Board page forbidden |
| Ready state | Ready means genuinely actionable according to deterministically known dependencies | Roadmap dependency owner | FV-B08 | FV-F06 | Jarvis suggestion cannot manufacture Ready state |
| Drag/status transition | status can be changed through same item identity; deterministic done-when may block Done | Roadmap owner + validation criteria | FV-B08 | FV-F06 | Done cannot silently bypass deterministic acceptance condition |
| Manual work item | operator-created item may commit directly under operator authority | Roadmap owner | FV-B08 | FV-F06 | Jarvis-generated work stays proposal until accepted |
| Work item details | same item opens description, acceptance, dependencies, linked model/requirement/idea, calendar blocks, progress/provenance | Roadmap read model | FV-B08/B09/B10 links | FV-F06 | details are projections of canonical linked records |

## Development — Calendar

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| Day / Week / Month / Agenda | Week default for hour-by-hour planning; Day detailed; Month overview; Agenda chronological | scheduling/event records to rederive | FV-B09 | FV-F07 | same underlying Calendar event data |
| Actual time block | exact date/start/end/time zone; types work session, meeting/call, experiment/lab, review, reminder, deadline, unavailable/personal | event/scheduling owner | FV-B09 | FV-F07 | Roadmap date range must not become continuous Calendar occupancy |
| Roadmap link | one Roadmap item may link to zero/one/many actual Calendar blocks | Roadmap + Calendar link owner | FV-B08/B09 | FV-F07 | link preserves both identities, no duplication |
| Schedule work from Roadmap | prefilled time block linked to selected Roadmap item | scheduling owner | FV-B09 | FV-F06/F07 | user/Jarvis proposal does not mutate until accepted |
| Create from time cell | selected day/time pre-fills add-event form | Calendar owner | FV-B09 | FV-F07 | persisted only through real backend action |
| Effort metrics | planned/completed/remaining effort shown only when derivable from real Calendar/work data | Roadmap/Calendar read projection | FV-B08/B09 | FV-F06/F07 | no guessed hours |
| Jarvis scheduling | query free time/deadlines/dependencies and propose exact slots | Calendar/Roadmap reads + proposal owner | FV-B09/B11 | FV-F07 | no silent schedule insertion |

## Development — Brainstorm

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| RAW capture | preserve original free text and attachments | files/events/decision/proposal infrastructure to audit | FV-B10 | FV-F08 | Jarvis does not rewrite source Raw |
| Raw state | truthful `NEW / DISCUSSED / RECONCILED / SUPERSEDED` lineage | Brainstorm domain owner | FV-B10 | FV-F08 | Discussed is not automatically Superseded |
| Reconciled idea | maintained synthesis, conclusions/trade-offs/open questions/structured content/diagrams/provenance | Brainstorm domain owner | FV-B10 | FV-F08 | revisions preserve lineage rather than duplicate concept silently |
| Inline multi-expand | compact list at rest, multiple reconciled ideas open simultaneously | frontend presentation | FV-B10 | FV-F08 | reading does not alter authority/context |
| Explicit Jarvis context basket | add/remove multiple IDEA/raw/model/literature/project/Coding refs | context/action owner | FV-B11 | FV-F08 | opening record != add to context |
| Reconciliation proposal | Jarvis proposes create/update/source-state changes with diff before approval | proposal/change owner | FV-B10/B11 | FV-F08 | no silent rewrite/promotion |
| Add to Roadmap | mature idea creates/proposes project work | Brainstorm→Roadmap bridge | FV-B10 + FV-B08 | FV-F08/F06 | promotion is explicit |
| Promote to Design | enters Design proposal/change path | Brainstorm→Design proposal bridge | FV-B10 | FV-F08/F02 | does not directly mutate model |
| Promote to Coding | enters Coding development proposal | Brainstorm→Coding bridge | FV-B10/B15/B16 | FV-F08/F10 | does not directly edit code |
| Record speech | future local speech-to-text capture into Raw | media/local AI/egress policy owner to rederive | FV-B22 | FV-F08 | no always-on/background recording; truthful unavailable before backend exists |

## Settings — Appearance / AI / System

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| Appearance | system/light/dark, accent and stable display preferences | existing settings/appearance storage | existing owner | FV-F09 | semantic engineering colors independent of accent |
| Provider identity | provider/integration rows, credential status, endpoint/config, capability/model catalogue where supported | existing provider gateway/config/secure storage | FV-B12 | FV-F09 | credentials belong to provider/integration, not individual models |
| Credential update/test | secure backend-mediated save/test | secure storage/provider boundary | FV-B12 | FV-F09 | no secret returned to UI/logs; no frontend storage |
| Local AI | local runtime/provider status without external credential assumption | existing local_ai/provider abstraction | FV-B12 overlap | FV-F09 | truthful detected/available state only |
| Orchestration policy | generic routing/fallback/sensitive-context policy, Hermes only when backend authority actually exists | existing routing/egress/budget owners; frozen Hermes specs must be respected | FV-B12 | FV-F09 | UI cannot create Hermes authority by label |
| Budget/usage | real configured limits/usage where backend supports it | budget/AI job/provider accounting | FV-B12 | FV-F09 | no fixture spend/token counters in production |
| System diagnostics | app/runtime/data/services/version/schema/status | existing health/system/config/database routes | reuse existing owner + minimal additions through 100c | FV-F09 | every status observed; no synthetic Healthy/Ready |

## Coding — Repository

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| Remote repository identity | repo/default/current branch/exact SHA/clean remote facts/open PRs/check/review state as applicable | GitHub connector/integration + repository modules to audit | FV-B13 | FV-F10 | GitHub remote is source of truth; frontend no token/API direct call |
| Active development lifecycle | inspect `Proposal → Plan → Implementation → Tests → Independent Review → Reconciliation → Merge` with exact-head evidence | current builder/checkpoint/PR process + future projected state owner | FV-B15 | FV-F10 | stale gate/review invalidated after head changes |
| Current work | truthful active/planned development fronts from canonical queue/PR state | STATUS/spec/PR projections | FV-B13/B15 | FV-F10 | UI must not invent authorization |
| Repository Inspector search | path/literal/ID search across Markdown/spec/code/test/config/workflow/architecture/SVG/image safe artifacts | GitHub/file search/read adapter | FV-B14 | FV-F10 | search/read projection only, no duplicate repo truth store |
| Artifact preview | Markdown rendered/raw, source text/code/config, SVG/image safe preview with exact ref/path/blob | repository read facade | FV-B14 | FV-F10/F15 | bounded allow-list/size and truthful unsupported state |
| Architecture inspection | architecture Markdown/SVG/semantic artifact searchable like any other result; bounded preview/expand | repository read facade; optional semantic model later | FV-B14/B23 | FV-F15 | no permanent architecture graph; rendering does not make diagram authoritative |
| Open on GitHub | direct exact repository URL for selected artifact/ref | repository observability facade | FV-B13/B14 | FV-F10/F15 | URL corresponds to selected real ref/path |
| Add to Jarvis context | selected exact artifact/PR/spec/ref becomes explicit removable context | Coding context owner | FV-B16/B17 | FV-F10 | selection alone does not silently add context |
| Suggest modification | user instruction against selected artifact produces proposed diff/plan/reason/affected files | Coding action/proposal owner | FV-B16 | FV-F13 | no direct save-to-file; proposal must enter isolated lifecycle |
| Coding knowledge | explain architecture/decisions/specs/invariants with exact provenance | repository documents/read index | FV-B17 | FV-F10 | generated explanation is not source authority |
| Branch/worktree implementation | authorized development writes only to isolated branch/worktree then tests/review/PR | Git/GitHub development control plane | FV-B15/B16 | F10 actions where exposed | live running code is never mutation target |

## Coding — Runtime

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| Local actually executed identity | exact local installation/worktree, running commit/version/branch and dirty/clean state | local system/runtime observer to rederive | FV-B18 | FV-F11 | GREEN treatment also has explicit `Local / actually executed` text; never infer from GitHub latest |
| Latest approved GitHub identity | selected approved remote target exact SHA/version | repository observability + update policy | FV-B13/B18 | FV-F11 | ORANGE newer state also has explicit text; color alone insufficient |
| Alignment state | explicit aligned/local-behind/divergent/unknown based on exact histories | local runtime + repository compare | FV-B18/B19 | FV-F11 | unknown/divergent must fail honestly |
| Semantic delta | concise `What GitHub added after local version`, tied to actual commits/files/specs; docs-only/runtime-affecting classification where supportable | exact Git compare/read + bounded summarization | FV-B19 | FV-F11 | LLM-only feature claims cannot be presented as fact |
| Inspect delta evidence | open underlying commits/files in inspector-style detail | repository facade | FV-B13/B19 | FV-F11/F10 | summary always traceable to evidence |
| Service health | backend/frontend/local AI/runner etc. subordinate health/status where observed | existing health/system APIs + runtime observer | FV-B18 | FV-F11 | no hard-coded Healthy |
| Safe update preparation | current/target SHA, dirty-state guard, state backup, migration/build/smoke plan, rollback point | future local update supervisor | FV-B20 | FV-F14 | detailed phases stay compact until requested |
| Safe update execution | preserve state → fetch exact target → migrations/build → deterministic smoke → restart → health → automatic rollback on failure | future update supervisor | FV-B20 | FV-F14 | no blind pull/hot swap; explicit authority required |

## Coding — future integrated terminal

| Capability | Required operator behavior | Candidate owner to audit | Backend draft | Frontend draft | No-fake / authority rule |
| --- | --- | --- | --- | --- | --- |
| Real terminal session | real local PTY/session, PowerShell default on Windows | new security-bounded local PTY/session service | FV-B21 | FV-F12 | browser does not execute shell directly; no fake terminal pretending execution |
| Terminal / Logs tabs | lower Runtime area can switch between terminal and logs | Runtime UI + PTY/log readers | FV-B21 | FV-F12 | log availability preserved |
| Session cwd/history/scroll | active cwd, session-scoped scroll/history, stdin/stdout/stderr | PTY session owner | FV-B21 | FV-F12 | terminal history is not canonical project Memory |
| Ctrl+C / interrupt | real interrupt/control handling | PTY owner | FV-B21 | FV-F12 | backend-mediated |
| Open terminal here | Repository Inspector/worktree/path action opens validated allowed cwd | repository inspector → PTY bridge | FV-B14/B21 | FV-F10/F12 | backend validates path; no arbitrary frontend filesystem authority |
| Send output to Jarvis | selected/bounded terminal output becomes explicit context | PTY/context/AI egress boundary | FV-B21/B16 | FV-F12 | secret scrubbing/policy required |
| Jarvis command proposal | Jarvis returns command text with Insert/Copy | proposal/context owner | FV-B21/B16 | FV-F12 | command is not executed automatically |
| High-risk command confirmation | backend classifies high-risk/destructive command families and UI requires explicit confirmation/policy | PTY security/policy owner | FV-B21 | FV-F12 | cannot be bypassed by prompt text |
| Offline CI | fake/replaceable PTY adapter exercises lifecycle without Windows PowerShell | PTY service tests | FV-B21 | FV-F12 integration tests | no live shell/network/provider dependency in CI |

## Cross-surface completion obligations

100c must ensure that the final canonical spec map preserves the following cross-surface links:

- Project Basis changes can affect model working revisions and deterministic revalidation;
- Literature/project search records can be explicitly added to Jarvis context and linked to exact model/project usage;
- Brainstorm promotion reaches Roadmap, Design proposal or Coding proposal without direct authority mutation;
- Roadmap and Calendar share item links but retain distinct project-window versus actual-time semantics;
- Repository and Runtime remain distinct remote-versus-local truth sources;
- Repository Inspector can open architecture artifacts without making architecture a permanent first-screen surface;
- Runtime divergence uses Repository evidence but never equates remote latest with local execution;
- integrated terminal is a separate security authority from self-update and cannot bypass Coding/Git/spec lifecycle.

## 100c disposition requirement

For every row above, 100c must record one of:

- canonical owning spec ID(s);
- `REFERENCE_ONLY` with explanation of why no backend/runtime work is required;
- `DEFER_TRIGGERED` with concrete prerequisite/trigger;
- explicit maintainer-authorized supersession/rejection.

A blank owner, absence of current code or implementation inconvenience is not a valid disposition.

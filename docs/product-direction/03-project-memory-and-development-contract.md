# PD-03 — Project Memory and Development contract

Status: future product direction; not implementation authority. Reconciled to PD-08 on 2026-08-27; where earlier revisions differed, the final semantics below are authoritative for this packet.

## Purpose

Keep authoritative project knowledge separate from future work, brainstorming and JarvisOS software self-knowledge.

# Memory

`Memory` is the inspectable authoritative memory of the active engineering project. It is also the knowledge base that Jarvis should use when reasoning about that project.

Normal Memory sections are exactly:

- `Project Basis`
- `Models`
- `Literature`

Do not add `Evidence`, `Files`, `History`, `Runs`, `Review`, or `Lineage` as peer Memory sections.

A global/project Memory search is required conceptually and should search structured records and attached/indexed content without forcing the user to know the underlying storage schema. Search is a read projection, never a second truth store.

## Project Basis

Project Basis owns authoritative project-level truths that should not be duplicated into every model version, for example:

- project objective/engineering question;
- global requirements and acceptance criteria;
- stable physical/economic constraints;
- global boundary conditions;
- project-level decisions;
- applicable standards/regulations;
- resources/capabilities that constrain the project.

A model version references the applicable Project Basis rather than copying it wholesale.

The final UI composition is `Project search | Project Basis | Jarvis`. Compact dossier items expose exact value/rule-or-threshold and truthful state when canonical records support them. Jarvis may propose one or a bounded batch of changes, but approval uses the model-change/change-set authority defined by PD-07 rather than frontend-only mutation.

PD-07 is binding for Project Basis/model-change impact: criterion/rule-only changes must be re-evaluated deterministically against exact stored outputs when sufficient; recomputation is requested only when genuinely required. Working revisions remain explicit and reconciled history immutable.

## Models

A Model entry is versioned. Each version is a coherent engineering dossier, not just a source-code model or a simulation-run pointer.

For each version the UI/data model should be able to expose, when applicable:

- Definition/scope;
- Assumptions;
- Methods & Equations;
- Parameters & Inputs;
- Process configuration;
- BLUECAD configuration/geometry;
- Results & Validation;
- Criticalities/known limitations;
- Sources;
- Artifacts;
- Runs;
- Changelog/Lineage.

Validation/evidence is version-scoped. Example: if Process passes for v12 and fails for v13, both facts remain attached to the exact versions/runs that produced them; there is no global `Process PASS` evidence record presented as permanently true.

Historical runs should be inspectable from the model/version that owns them. A run can expose input snapshot, output snapshot, status, logs and artifacts without creating a peer `Runs` application destination.

### Scalable dossier disclosure

Model dossiers must remain compact and scannable even when a project accumulates many assumptions, parameters, runs, sources, artifacts or validation records.

The normal Models view must therefore use bounded section summaries rather than allowing every section to grow vertically without limit. Each major dossier section header is an interactive disclosure control.

Required interaction semantics:

- collapsed state shows section title plus a compact truthful summary/count/status sufficient for whole-dossier scanning;
- clicking the section header expands that section in place to reveal its full bounded content;
- clicking again collapses it;
- expansion must not navigate away from the selected model/version;
- a large section may use internal scrolling, pagination, filtering or virtualization rather than forcing the whole page to grow indefinitely;
- one expanded section must not cause unrelated sections to scale or visually dominate the page;
- `Collapse all` restores the overview quickly;
- disclosure state is presentation state only and must not change canonical engineering records;
- keyboard/focus/ARIA behavior must provide equivalent access.

The default density favors overview first, detail on demand. Do not solve scale by turning every subsection into a primary page or by hiding exact model-version ownership.

## Literature

Literature owns externally sourced project knowledge and the external files that support it.

The future model should distinguish at least conceptually:

- source/publication/document identity;
- URL/DOI/original provenance;
- imported file where applicable;
- extracted claim/value;
- context/conditions under which the claim/value applies;
- location in the source (page/table/section when available);
- review/status;
- project records/models that use the source.

A bare `source_ref` string on a parameter is insufficient as the long-term product model for literature provenance. Existing `source_ref` fields may be migrated/bridged rather than duplicated.

Final UI behavior is compact-list-first: project search on the left, Literature center, Jarvis right; a source expands inline rather than navigating to a separate page; multiple sources may remain open; detail text is left and bounded preview right; PDF/image/source preview is truthful and the full source can open in browser/native viewer where supported.

External PDFs, datasets, datasheets and similar files appear through Literature when they represent sources. There is no normal standalone Files workspace.

## Files and artifacts rule

Files are implementation/storage objects, not a primary user category.

- external source files belong to Literature;
- internally generated model artifacts belong to the exact Model/version/run that generated them;
- generic file discovery remains possible through search.

Do not make users classify information by storage mechanism.

## History rule

A full project activity/history view is useful only when readable as an event story/timeline, not as an undifferentiated database table. If implemented, history is contextual or globally searchable, not a peer Memory section.

# Development

`Development` owns future project work and non-authoritative ideas. Its normal peer tabs are exactly:

- `Roadmap`
- `Brainstorm`

JarvisOS software self-development has additional behavior in `Coding`, while Roadmap/Brainstorm may still contain software-development ideas/work when they are being evaluated as project work.

## Roadmap

Roadmap represents committed/planned work. It has exactly two normal projections over the same underlying Roadmap item identities:

- `Timeline`
- `Calendar`

There is **no standalone Board page** in the final product direction.

### Timeline

Timeline answers: what work must happen, in what project window, in what dependency/sequence, and around what milestones.

It may show workstream bars, dependencies, milestones, zoom and presentation filters. The approved condensed/tall/light type treatment is reserved for colored workstream bars; ordinary UI and status cards use normal app typography.

Below the Timeline sits a collapsible operational snapshot, `Execution status`, emphasizing exactly:

`Ready | In progress | Blocked`

`Planned` and `Completed` are secondary/filterable. The embedded snapshot can expand/collapse but does not become a separate route/store.

Roadmap items may include title, type, start/end, status, priority, description, domain, links, dependencies/blocks, scheduling constraints, done-when/acceptance, tags, owner, effort, progress/subtasks, resources/cost, notes/attachments and provenance.

`Ready` means genuinely actionable according to known deterministic dependency gates where available. A transition to `Done` cannot silently bypass a deterministic acceptance/done-when condition.

Manual operator-created items may commit directly under operator authority. Jarvis-generated items remain proposals until explicitly accepted.

### Calendar

Calendar answers: **when work actually happens in the operator's day/week**. It must not duplicate Roadmap windows as occupied time.

Supported projections:

- `Day`
- `Week` — default, because hour-by-hour planning is central;
- `Month` — compact overview of deadlines/milestones/meetings/occupied days;
- `Agenda` — chronological list.

Calendar events include work sessions, calls/meetings, experiments/lab sessions, reviews, deadlines, reminders and optional unavailable/personal blocks.

One Roadmap item may have zero, one or many linked Calendar blocks. Roadmap duration/window is not the same concept as scheduled effort. `Schedule work` may create a linked prefilled block; create-from-time-cell may prefill exact day/time. Jarvis may propose slots using availability/deadlines/dependencies, but schedule mutation requires explicit approval.

## Brainstorm

Brainstorm is explicitly non-authoritative. The final product model is:

`RAW -> discussion/reconciliation with Jarvis -> RECONCILED -> explicit promotion`

This supersedes the older proposal-inbox/Kanban lifecycle.

### Raw

Raw capture preserves the original user material. It may include:

- free text;
- attachments/files;
- future speech capture;
- hypotheses/features/opportunities/problems/notes.

Jarvis does not rewrite the original Raw source in place.

Truthful Raw lineage states include:

`NEW | DISCUSSED | RECONCILED | SUPERSEDED`

`DISCUSSED` does not imply `SUPERSEDED`. Reconciled/superseded records retain links to the resulting idea/revision.

Future microphone/speech-to-text remains bounded/local-first in product intent, but any retained implementation must use the canonical AI execution spine/audit ledger and privacy/egress authority rather than a parallel inference path.

### Reconciled

The normal Reconciled view is compact at rest: idea ID, title, one-line takeaway, domain/state and updated date. Clicking expands inline; multiple ideas can remain open simultaneously.

Expanded content may include:

- variable-length discussion synthesis;
- conclusions/open questions/trade-offs/rationale;
- structured bullets/tables/matrices/decision trees/inline SVG where useful;
- compact/collapsible provenance back to Raw notes, discussions, attachments and project context;
- revisions/diffs rather than duplicate concepts.

### Jarvis context

Opening/browsing an idea **does not** silently add it to Jarvis context.

The UI provides explicit `Add to Jarvis context` / `Discuss with Jarvis` actions and a removable multi-item context basket. It may combine multiple idea IDs plus Raw/model/requirement/Literature/Process/BLUECAD/Coding references. Jarvis may propose reconciliation updates, derived ideas or source-state changes with a diff before approval.

### Promotion boundary

Explicit actions may include:

- `Add to Roadmap`;
- `Promote -> Design` — enters the Design proposal/change path, not direct model mutation;
- `Promote -> Coding` — enters the Coding development-proposal/lifecycle path, not direct file/code mutation.

Brainstorm content never becomes authoritative project Memory merely because Jarvis stored or discussed it.

## Priority semantics

Where Roadmap/Development priority is exposed, priority must not rely on color alone:

- `Critical`;
- `High`;
- `Normal`;
- `Opportunity`.

Do not relabel Opportunity as merely `Low`.

## Jarvis panel

Both Roadmap and Brainstorm support right-side Jarvis interaction where useful. Jarvis may inspect, discuss, research and prepare bounded proposals, but must not silently cross Memory/Design/Coding/scheduling authority boundaries.

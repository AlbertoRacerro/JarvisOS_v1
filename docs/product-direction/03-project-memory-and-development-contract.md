# PD-03 — Project Memory and Development contract

Status: future product direction; not implementation authority.

## Purpose

Keep authoritative project knowledge separate from future work, brainstorming and JarvisOS software self-knowledge.

# Memory

`Memory` is the inspectable authoritative memory of the active engineering project. It is also the knowledge base that Jarvis should use when reasoning about that project.

Normal Memory sections are:

- `Project Basis`
- `Models`
- `Literature`

Do not add `Evidence`, `Files`, `History`, `Runs`, `Review`, or `Lineage` as peer Memory sections in this product direction.

A global Memory search is required conceptually and should search structured records and attached/indexed content without forcing the user to know the underlying storage schema.

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

## Models

A Model entry is versioned. Each version is a coherent engineering dossier, not just a source-code model or a simulation-run pointer.

For each version the UI/data model should be able to expose, when applicable:

- definition/scope;
- assumptions;
- equations/methods;
- parameters/inputs;
- Process configuration;
- BLUECAD configuration/geometry;
- results and validation outcomes;
- criticalities/known limitations;
- notes and version-specific future work;
- sources used;
- generated artifacts/files;
- runs/logical analyses associated with that version;
- changelog and parent/supersession lineage.

Validation/evidence is version-scoped. Example: if Process passes for v12 and fails for v13, both facts remain attached to the exact versions/runs that produced them; there is no global `Process PASS` evidence record presented as permanently true.

Historical runs should be inspectable from the model/version that owns them. A run can expose input snapshot, output snapshot, status, logs and artifacts without creating a peer `Runs` application destination.

## Literature

Literature owns externally sourced project knowledge and the external files that support it.

The future model should distinguish at least conceptually:

- source/publication/document identity;
- URL/DOI/original provenance;
- imported file where applicable;
- extracted claim/value;
- context/conditions under which the claim/value applies;
- location in the source (page/table/section when available);
- confidence/status;
- project records/models that use the source.

A bare `source_ref` string on a parameter is insufficient as the long-term product model for literature provenance. Existing source_ref fields may be migrated/bridged rather than duplicated.

External PDFs, datasets, datasheets and similar files appear through Literature when they represent sources. There is no normal standalone Files workspace.

## Files and artifacts rule

Files are implementation/storage objects, not a primary user category.

- external source files belong to Literature;
- internally generated model artifacts belong to the exact Model/version/run that generated them;
- generic file discovery remains possible through global search.

Do not make users classify information by storage mechanism.

## History rule

A full project activity/history view is useful only when visually readable as an event story/timeline, not as an undifferentiated database table.

If implemented, history should be contextual or globally accessible as an activity drawer/search result, with clear time ordering and causal relationships where known. Example event families include parameter changes, model-version creation, run start/result, proposal creation/acceptance and invalidation/staleness events.

History is not a peer Memory section.

# Development

`Development` owns future project work and non-authoritative ideas. Its normal peer tabs are exactly:

- `Roadmap`
- `Brainstorm`

This area applies to the engineering/project development workflow. JarvisOS software self-development has additional behavior in `Coding`, but Brainstorm/Roadmap may still contain software-development proposals when they are being evaluated as future work.

## Roadmap

Roadmap represents committed/planned work rather than general notes. It should support multiple views over the same underlying items rather than separate stores:

- timeline;
- calendar;
- board/status view.

Roadmap items may include milestones, tasks, deadlines, dependencies, blocked state and links to the project/model/Brainstorm proposal that motivated them.

## Brainstorm

Brainstorm is explicitly non-authoritative. It accepts:

- raw ideas;
- hypotheses to investigate;
- possible features;
- Jarvis suggestions;
- opportunities discovered from research/web/provider availability;
- problems that need discussion;
- future-development notes.

Brainstorm content does not become authoritative project Memory merely because Jarvis stored it.

## Brainstorm proposal inbox

Brainstorm contains a persistent proposal/reminder inbox for items that require later attention. Opening the page does not clear them.

Required conceptual record types:

- `Note`: stored, no persistent attention badge required;
- `Proposal`: requires a decision/discussion and remains unresolved until disposition;
- `Warning`: current risk/problem that deserves elevated priority;
- `Reminder`: intentionally resurfaces at a date or condition.

Required lifecycle for attention-bearing proposals:

`NEW -> ACKNOWLEDGED -> DISCUSSING -> {PROMOTED_TO_ROADMAP | IMPLEMENT_NOW | PARKED | REJECTED}`

Equivalent implementation names are acceptable only if semantics remain exact.

Items may be snoozed/reminded until a date or meaningful project condition. Snooze must not silently reject/delete the proposal.

## Priority semantics

Priority must not rely on color alone. Use text/icon plus color.

- `Critical` — red — blocking/current risk requiring intervention;
- `High` — orange — important and relatively urgent;
- `Normal` — yellow — should be addressed but does not block current work;
- `Opportunity` — blue/green — potentially valuable opportunity, not an obligation or failure.

Do not call Opportunity merely `Low`; an opportunity can be strategically valuable without being urgent.

## Promotion boundary

A Brainstorm item reaches authoritative Memory only through an explicit promotion/reconciliation action with provenance. A Brainstorm item reaches committed work through explicit Roadmap promotion or an authorized implementation action.

Jarvis may propose these transitions but must not silently rewrite authoritative Memory.

## Jarvis panel

Both Roadmap and Brainstorm should support right-side Jarvis interaction where useful. In Brainstorm, Jarvis should be able to research/discuss an idea, create/update a proposal, recommend disposition, and prepare promotion without bypassing the authoritative boundary.

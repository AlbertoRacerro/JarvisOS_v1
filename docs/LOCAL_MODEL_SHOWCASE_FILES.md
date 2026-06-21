# Local-Model-Facing Showcase Files

## Executive Summary

Showcase files are synthetic, non-authoritative, regenerable views over
canonical sources.

They help a local model orient itself before it requests source files, context
packs, or bounded forms. They do not replace canonical docs, source files,
database records, runtime policy, or human-reviewed decisions.

Showcase files and micro-context are separate orientation surfaces. Showcase
files are small model-readable files and indexes. Micro-context is a future
bounded snapshot regenerated from canonical sources and accepted state, designed
in `docs/MICRO_CONTEXT_DESIGN.md`. Neither surface is authoritative runtime
memory or retrieval.

V0 designs a small documentation-facing showcase set:

- `GEMMA_START_HERE.md`
- `CURRENT_STATE.md`
- `SYSTEM_MAP.md`
- `PROJECT_INDEX.md`
- `FILE_CATALOG.md`
- `DECISION_INDEX.md`
- `OPEN_CLARIFICATIONS.md`
- `SAFETY_POLICY.md`

This milestone designs those files only. It does not create runtime behavior,
generator scripts, routes, memory runtime, retrieval runtime, Context Pack
Broker runtime, provider routing, tool execution, model calls, frontend UI, or
BlueRev modeling.

## Design Goals

- Give local models a small first-read orientation surface.
- Preserve canonical source authority in `README.md`, `docs/ARCHITECTURE.md`,
  `docs/DECISIONS.md`, `docs/LOCAL_AI_EVALUATION_EVIDENCE.md`, source files,
  schemas, tests, and future audited stores.
- Help a model request the right source files instead of guessing from partial
  summaries.
- Make under-fetch visible as a failure mode on important tasks.
- Allow moderate over-fetch when the model cannot safely decide which source is
  enough.
- Keep local-model context cheap before full context-pack design exists.
- Use simple Markdown files before any graph, viewer, database index, or
  Context Pack Broker runtime exists.
- Make staleness and canonical-source links explicit.

## Non-Goals And Boundaries

Showcase files are not:

- canonical memory;
- source of truth;
- runtime retrieval;
- Context Pack Broker runtime;
- memory runtime;
- route behavior;
- UI behavior;
- model authority;
- automatic provider routing;
- automatic tool routing;
- automatic tool execution;
- automatic memory writing;
- memory promotion;
- safety approval;
- semantic validation;
- BlueRev modeling;
- authorization to call local or external models.

Showcase files must not claim to control Gemma or validate semantic truth. They
orient the model. JarvisOS validates structure and policy. Semantic correctness
remains a reliability, source-grounding, and review problem.

## Canonical-Source Rule

Canonical docs and source files remain authoritative.

If a showcase file conflicts with canonical docs or source code, the canonical
source wins. The stale showcase file must be updated or regenerated. A model
must not infer canonical truth from a showcase summary alone.

Each showcase file should include:

- source document links or source file paths;
- an update timestamp when generated later;
- a short stale-data warning;
- a clear statement that the file is non-authoritative.

Manual V0 showcase drafts may omit machine timestamps if they are maintained by
hand, but they must still point back to canonical sources.

## File List And Purpose

| Showcase file | Purpose | V0 status |
| --- | --- | --- |
| `GEMMA_START_HERE.md` | First file read by a local model. Explains showcase rules, non-authority, and when to ask for more context. | Designed now. |
| `CURRENT_STATE.md` | Compact current system status: active milestone, current boundary, approved next step, and non-approved behaviors. | Designed now. |
| `SYSTEM_MAP.md` | High-level map of backend, frontend, docs, and major modules. | Designed now. |
| `PROJECT_INDEX.md` | Active projects and their status. Initial projects are JarvisOS and BlueRev. | Designed now. |
| `FILE_CATALOG.md` | Important files and what they contain, so a model can request the right sources. | Designed now. |
| `DECISION_INDEX.md` | Compact index of durable decisions and ADRs, pointing to `docs/DECISIONS.md` as canonical. | Designed now. |
| `OPEN_CLARIFICATIONS.md` | Unresolved high-value questions, clearly separated from decided facts. | Designed now. |
| `SAFETY_POLICY.md` | Model authority limits, local-first policy, secret handling, provider/tool/retrieval restrictions, and non-approved behaviors. | Designed now. |

## V0 Showcase File Contracts

### `GEMMA_START_HERE.md`

Purpose:

- Provide the first local-model orientation file.
- Tell the model how to use showcase files.
- Tell the model what not to assume.
- Tell the model when to request bounded source files or context packs.

Intended reader:

- Local Gemma or another local model operating inside future bounded JarvisOS
  protocols.
- Human reviewers checking model-facing orientation.

Allowed content:

- One-paragraph description of JarvisOS as local-first, form-driven AI
  co-engineering infrastructure.
- The canonical-source rule.
- A compact reading order for showcase files.
- Rules for requesting more context.
- Required `not_decided` behavior when context is insufficient.
- Explicit forbidden assumptions.
- Links to canonical docs.

Forbidden content:

- Claims that the model controls JarvisOS.
- Claims that summaries are canonical truth.
- Tool execution instructions.
- Provider routing instructions.
- Secret-handling bypasses.
- Memory write or retrieval commands.
- BlueRev modeling assumptions.

Canonical sources it may summarize:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/FORM_DRIVEN_LOCAL_INTELLIGENCE.md`
- `docs/STAGED_MEMORY_INTAKE.md`
- `docs/HYBRID_INTAKE_FIELD_OWNERSHIP.md`
- `docs/LOCAL_AI_EVALUATION_EVIDENCE.md`
- `docs/DECISIONS.md`

Stale-data risk:

- High for current milestone, approved next step, active project status, and
  newly accepted decisions.

Update/generation rule:

- Update whenever current milestone, canonical docs, file catalog, authority
  boundaries, or model-use protocol changes.
- Future generator must preserve source links and timestamp metadata.

Example section skeleton:

```text
# Gemma Start Here

## Read This First
## Canonical Sources Win
## How To Use Showcase Files
## When To Request Source Files
## Required `not_decided` Behavior
## Forbidden Assumptions
## Canonical Links
```

### `CURRENT_STATE.md`

Purpose:

- Provide a compact current system status.
- Identify the active milestone.
- Identify the current architectural boundary.
- Identify the approved next step.
- List non-approved behaviors.

Intended reader:

- Local model deciding what context to request before a task.
- Human reviewer checking whether model orientation matches current project
  state.

Allowed content:

- Current milestone ID and title.
- Current HEAD or documentation snapshot identifier when generated.
- Current accepted local-AI position.
- Current docs-only or runtime boundary.
- Approved next milestone.
- Non-approved behaviors.
- Links to canonical current-status sources.

Forbidden content:

- Runtime readiness claims not backed by implemented and tested behavior.
- New approvals for Gemma orchestration, local gatekeeping, chat, memory
  runtime, retrieval runtime, Context Pack Broker runtime, provider routing,
  tool execution, frontend UI, or BlueRev modeling.
- Implicit permission to change source code.

Canonical sources it may summarize:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/LOCAL_AI_EVALUATION_EVIDENCE.md`
- `docs/CAVEMEM_CAVEMAN_REFERENCE_AUDIT.md`
- `docs/DECISIONS.md`

Stale-data risk:

- Very high. Current state changes after each accepted milestone.

Update/generation rule:

- Update on every milestone completion.
- Generated version must include timestamp, source commit, and source links.
- If stale, the model must request current canonical sources.

Example section skeleton:

```text
# Current State

## Snapshot
## Active Milestone
## Current Boundary
## Approved Next Step
## Non-Approved Behaviors
## Canonical Sources
```

### `SYSTEM_MAP.md`

Purpose:

- Orient the model to the repository without full ingestion.
- Map backend, frontend, docs, scripts, and major modules.
- Help the model request the right source paths.

Intended reader:

- Local model preparing a bounded context request.
- Human reviewer checking repository orientation.

Allowed content:

- High-level repository tree.
- Major backend module roles.
- Frontend role and current boundary.
- Docs role and canonical hierarchy.
- Runtime data root versus repository source distinction.
- Warnings about areas not approved for model control.

Forbidden content:

- Full source-file copies.
- Generated dependency inventories.
- Secret paths or secret values.
- Claims that the model can retrieve arbitrary files.
- Claims that the map is exhaustive.

Canonical sources it may summarize:

- `README.md`
- `docs/ARCHITECTURE.md`
- Repository tree from tracked files.
- Major source paths under `backend/`, `frontend/`, `scripts/`, and `docs/`.

Stale-data risk:

- Medium to high. Module paths and docs evolve with milestones.

Update/generation rule:

- Update when modules, route boundaries, frontend areas, scripts, or canonical
  docs move.
- Future generator should read tracked file paths, not generated dependencies.

Example section skeleton:

```text
# System Map

## Repository Root
## Backend Areas
## Frontend Areas
## Docs Areas
## Scripts
## Runtime Data Root
## Boundaries
## Canonical Sources
```

### `PROJECT_INDEX.md`

Purpose:

- List active projects and their status.
- Keep JarvisOS and BlueRev distinct.
- Prevent a model from treating BlueRev as currently approved modeling work.

Intended reader:

- Local model deciding project context.
- Human reviewer checking project-state summaries.

Allowed content:

- Project names.
- Project status.
- Current approved work focus.
- Explicit `not_decided` fields.
- Links to canonical decisions and architecture docs.

Forbidden content:

- New BlueRev material choices.
- New BlueRev equations, assumptions, geometry, parameters, or modeling
  behavior.
- Claims that BlueRev modeling has started.
- Promotion of tentative assumptions to accepted facts.

Canonical sources it may summarize:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/STAGED_MEMORY_INTAKE.md`
- `docs/HYBRID_INTAKE_FIELD_OWNERSHIP.md`
- `docs/DECISIONS.md`

Stale-data risk:

- High for status and approved next work.
- Very high for any future project-specific assumptions.

Update/generation rule:

- Update when project status changes or a new canonical project decision is
  accepted.
- Leave fields as `not_decided` unless canonical sources decide them.

Example section skeleton:

```text
# Project Index

## JarvisOS
## BlueRev
## Other Projects
## Not Decided
## Canonical Sources
```

### `FILE_CATALOG.md`

Purpose:

- Describe important files and what they contain.
- Help a model request the right source files.
- Reduce blind repository ingestion.

Intended reader:

- Local model creating bounded context requests.
- Human reviewer checking whether file summaries are source-grounded.

Allowed content:

- Canonical docs and their authority.
- Major backend module descriptions.
- Major frontend area descriptions.
- Script descriptions.
- Historical evidence docs.
- Staleness warnings and source links.

Forbidden content:

- Claims that file summaries replace file contents.
- Raw secret values.
- Untracked generated dependency catalogs.
- Large pasted source excerpts.
- Runtime retrieval instructions.

Canonical sources it may summarize:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- Tracked repository paths.
- File headers or top-level declarations when a future generator exists.

Stale-data risk:

- High when source files move or new modules are added.

Update/generation rule:

- Update when important docs or source modules are added, moved, renamed, or
  re-scoped.
- Future generator should include path, role, authority level, last source
  snapshot, and links to canonical docs where applicable.

Example section skeleton:

```text
# File Catalog

## Canonical Docs
## Backend
## Frontend
## Scripts
## Historical Evidence
## Generated Or Ignored Areas
## Request Guidance
```

### `DECISION_INDEX.md`

Purpose:

- Provide a compact index of durable decisions.
- Point to `docs/DECISIONS.md` as the canonical ADR source.
- Help a model request exact ADRs before reasoning from decisions.

Intended reader:

- Local model checking decision status.
- Human reviewer checking ADR discoverability.

Allowed content:

- ADR number.
- ADR title.
- Status.
- One-line summary.
- Link to canonical ADR section.
- Refinement or supersession notes copied from the canonical ADR.

Forbidden content:

- New decisions.
- Changed decision status.
- Reworded authority that exceeds the ADR.
- Omitting important "not approved" constraints from safety-related ADRs.

Canonical sources it may summarize:

- `docs/DECISIONS.md`
- `docs/ARCHITECTURE.md` only for cross-reference context.

Stale-data risk:

- High when ADRs are added or refined.

Update/generation rule:

- Update whenever `docs/DECISIONS.md` changes.
- Future generator should derive entries directly from ADR headings and status
  lines.

Example section skeleton:

```text
# Decision Index

## Rule
## Recent Accepted ADRs
## Local AI ADRs
## Memory And Showcase ADRs
## Provider And Tool ADRs
## Canonical Source
```

### `OPEN_CLARIFICATIONS.md`

Purpose:

- List unresolved high-value questions.
- Distinguish open questions from decided facts.
- Prevent a model from filling gaps with invented assumptions.

Intended reader:

- Local model deciding whether to ask a clarification question.
- Human reviewer checking unresolved design state.

Allowed content:

- Open questions.
- Why each question matters.
- Owning milestone if known.
- Decided facts that constrain the question.
- Source links.
- `not_decided` markers.

Forbidden content:

- Treating open questions as decisions.
- Converting tentative BlueRev assumptions into accepted facts.
- Hiding unresolved safety or authority questions.
- Asking questions already answered by canonical docs.

Canonical sources it may summarize:

- `docs/ARCHITECTURE.md`
- `docs/FORM_DRIVEN_LOCAL_INTELLIGENCE.md`
- `docs/STAGED_MEMORY_INTAKE.md`
- `docs/HYBRID_INTAKE_FIELD_OWNERSHIP.md`
- `docs/CAVEMEM_CAVEMAN_REFERENCE_AUDIT.md`
- `docs/DECISIONS.md`

Stale-data risk:

- High. Clarifications should disappear or change after decisions are accepted.

Update/generation rule:

- Update when a decision accepts, rejects, or defers an open question.
- Future generator should not infer open questions from TODO text alone without
  review.

Example section skeleton:

```text
# Open Clarifications

## Rule
## Open Questions
## Deferred Questions
## Decided Facts That Constrain Open Work
## Canonical Sources
```

### `SAFETY_POLICY.md`

Purpose:

- Summarize local model authority limits.
- Summarize local-first policy.
- Summarize secret handling, provider/tool/retrieval restrictions, and
  non-approved behaviors.

Intended reader:

- Local model before it proposes any action, context request, provider intent,
  tool intent, sensitivity assessment, or memory object.
- Human reviewer checking whether model-facing safety summaries match canon.

Allowed content:

- JarvisOS authority boundaries.
- Local-first policy summary.
- Secret-handling hard rules.
- Provider and tool restrictions.
- Retrieval and memory restrictions.
- BlueRev modeling restrictions.
- Link to canonical safety and architecture sources.

Forbidden content:

- New safety policy.
- Model-owned risk decisions.
- Sensitivity downgrade authority.
- Permission for direct file/database retrieval.
- Permission for provider calls.
- Permission for tool execution.
- Permission for memory promotion.

Canonical sources it may summarize:

- `docs/ARCHITECTURE.md`
- `docs/FORM_DRIVEN_LOCAL_INTELLIGENCE.md`
- `docs/HYBRID_INTAKE_FIELD_OWNERSHIP.md`
- `docs/STAGED_MEMORY_INTAKE.md`
- `docs/LOCAL_AI_EVALUATION_EVIDENCE.md`
- `docs/CAVEMEM_CAVEMAN_REFERENCE_AUDIT.md`
- `docs/DECISIONS.md`

Stale-data risk:

- Very high for authority and safety policy. Any stale safety summary must lose
  to canonical docs.

Update/generation rule:

- Update whenever authority, provider, tool, memory, retrieval, secret, or
  BlueRev policy changes.
- Future generator must preserve source links, timestamps, and explicit
  non-authority language.

Example section skeleton:

```text
# Safety Policy

## Rule
## Model Authority Limits
## Local-First Policy
## Secret Handling
## Provider Restrictions
## Tool Restrictions
## Retrieval And Memory Restrictions
## BlueRev Restrictions
## Non-Approved Behaviors
## Canonical Sources
```

## Deferred Showcase Files

### `MEMORY_INDEX.md`

Deferred because MemoryStore, memory runtime, retrieval runtime, promotion
policy, and memory indexing are not designed yet.

A memory index would be too easy to mistake for canonical memory. Until
JarvisOS has explicit memory storage, source IDs, promotion policy, retrieval
contracts, and freshness metadata, this file must not exist as an operational
showcase file.

### `TOOL_AND_PROVIDER_CATALOG.md`

Deferred because provider/tool intent forms, provider routing, and tool
execution policy are not ready yet.

A tool/provider catalog could be misread as permission to call tools or route
provider requests. Until JarvisOS has explicit intent forms, authority policy,
allowed targets, budget rules, confirmation rules, and audited execution
boundaries, this file must not exist as an operational showcase file.

## Update Policy

V0 update policy is manual.

Manual maintainers must:

- update showcase design references when canonical docs change;
- preserve canonical source links;
- avoid adding runtime authority language;
- leave undecided fields as `not_decided`;
- mark stale or uncertain summaries explicitly;
- prefer source requests over inference when context is insufficient.

Future generator policy:

- The generator is a later milestone, not part of this design milestone.
- The generator must preserve source links and timestamps.
- The generator must identify the source commit or snapshot.
- The generator must not override canonical docs.
- The generator must not silently invent facts absent from canonical sources.
- The generator must not read ignored dependency trees as canonical source.
- The generator must fail closed when source links are missing or contradictory.

Generated showcase files remain non-authoritative even when generated
successfully.

## Model-Use Protocol

1. Read `GEMMA_START_HERE.md` first.
2. Inspect relevant showcase files for orientation.
3. Request bounded source files or context packs when the task needs canonical
   detail.
4. Use canonical docs and source files for final grounding.
5. Leave fields as `not_decided` when context is insufficient.
6. Ask a clarification when a substantial missing choice blocks safe progress.
7. Never infer canonical truth from showcase summaries alone.
8. Never treat showcase files as permission for runtime action, provider calls,
   tool calls, retrieval, memory writes, or BlueRev modeling.

## Failure Modes

Stale showcase file:

- A showcase file can lag behind canonical docs, code, or ADRs.
- Mitigation: include source links, timestamps when generated, and explicit
  stale-data warnings.

Contradiction with canonical docs:

- A showcase summary can conflict with `docs/ARCHITECTURE.md`,
  `docs/DECISIONS.md`, source code, or evidence docs.
- Mitigation: canonical sources win and the showcase file is updated.

Model over-trusts summary:

- A model may treat a short summary as sufficient proof.
- Mitigation: require bounded source requests for important tasks and forbid
  canonical inference from summaries alone.

Under-fetch on important task:

- A model may fail to request enough source context.
- Mitigation: treat under-fetch as a serious failure mode and prefer moderate
  over-fetch when unsure.

Accidental runtime authority language:

- A showcase file may use wording that sounds like permission, approval,
  control, execution, validation, routing, or memory promotion.
- Mitigation: use orientation language only and preserve explicit
  non-authority rules.

## Acceptance Criteria For Future Implementation

Future implementation of actual showcase files is acceptable only when:

- the V0 file set is created outside runtime source directories;
- each file contains a non-authoritative warning;
- each file links to canonical sources;
- current-state content includes a source commit or timestamp when generated;
- `MEMORY_INDEX.md` remains absent until memory runtime, retrieval runtime,
  promotion policy, and memory indexing are designed;
- `TOOL_AND_PROVIDER_CATALOG.md` remains absent until provider/tool intent
  forms, provider routing, and tool execution policy are designed;
- no backend code, frontend code, routes, database schema, generator scripts,
  model calls, MCP, hooks, workers, viewers, retrieval, memory runtime,
  compression runtime, Context Pack Broker runtime, provider routing, tool
  execution, or BlueRev modeling is added by the showcase-file milestone;
- tests or reviews confirm that file wording does not authorize runtime action;
- stale summaries are detectable through source links and timestamps;
- canonical docs remain the source of truth.

## Milestone Boundary Confirmation

1D-A is a docs-only design milestone.

It does not add:

- backend code;
- frontend code;
- routes or APIs;
- database schema or migrations;
- generator scripts;
- local or external model calls;
- MCP;
- hooks;
- worker processes;
- viewers;
- retrieval runtime;
- memory runtime;
- compression runtime;
- Context Pack Broker runtime;
- provider routing;
- tool execution;
- BlueRev modeling;
- vendored Cavemem or Caveman code;
- runtime-approved model status.

Showcase files orient local models. They do not control local models, validate
semantic truth, authorize runtime behavior, or replace canonical sources.

# PD-08 — Final visual product contract after maintainer inspection

Status: future product direction; not runtime implementation authority.
Date: 2026-08-27

## Purpose

Freeze the final operator-facing product semantics reached after the maintainer completed the visual-identity inspection across Design, Memory, Development, Coding, and Settings.

This document is a product-direction reconciliation layer over PD-02 through PD-07. Where this document and the approved references under `docs/design-references/` are more specific than earlier product-direction prose, this document wins for future product composition. It does not change `docs/specs/STATUS.md` by itself and it does not authorize runtime implementation.

The final preservation packet is intentionally split by role: the approved UI manifest and byte-identified HTMLs own visual/composition identity; `docs/design-references/FINAL_OPERATOR_INTERACTION_CONTRACT_2026-08-27.md` owns the frozen user-visible interaction/state-transition semantics; the capability matrix and pseudo-spec pack preserve future backend/frontend obligations. Builders must not infer omitted behavior from current runtime convenience or chat memory.

## Global shell

Normal primary navigation is exactly:

`Design | Memory | Development | Coding | Settings`

There is no normal `Home` destination.

The visual shell is light-first warm limestone/near-white, with nearly square controls/surfaces, restrained structural depth, regular/medium Inter/Inter Display typography, IBM Plex Mono for code/log/path/hash content, and Phosphor for generic icons. Semantic engineering colors remain independent of appearance accent.

## Design

Normal peer modes remain exactly:

`Process | BLUECAD`

Model, Results, Runs, Evidence, Review, Lineage, Files, and History remain contextual/owned information rather than peer Design destinations.

The approved Process/BLUECAD compositions under `docs/design-references/` remain the visual reference. Process and BLUECAD share the right-side Jarvis/Properties interaction language while retaining different editing semantics. Visible engineering/CAD affordances that are not yet backed by accepted runtime authority remain preserved as truthful unavailable/future behavior; missing backend support is not permission to redesign the approved workbench away.

## Memory

Normal peer sections remain exactly:

`Project Basis | Models | Literature`

### Project Basis

The final composition is:

`Project search | Project Basis | Jarvis`

Project Basis owns authoritative project-level objective/question, requirements, acceptance criteria, stable constraints, architectural/global decisions, boundary conditions, standards/regulations, and resource/capability constraints.

Change/validation semantics follow PD-07. Criterion-only changes that can be checked from exact existing outputs should be re-evaluated deterministically without a solver rerun; recalculation-required changes expose a truthful contextual validation action. Accepted proposal batches create inspectable working revisions rather than silently overwriting the reconciled model. The approved `Approve all` interaction applies only to the exact displayed bounded batch; acceptance creates/advances the working revision, clears the proposal surface and updates visible values from that exact revision.

### Models

A selected model/version is an overview-first engineering dossier. Major dossier sections are disclosure controls with compact truthful summaries and bounded expansion. The dossier owns version-scoped Process/BLUECAD configuration, results, validation, artifacts, runs, sources, criticalities and lineage.

### Literature

The final composition is:

`Project search | Literature | Jarvis`

Literature normally shows a compact source/file list. Selecting a source expands it inline; multiple sources may remain expanded simultaneously. Expanded detail places extracted source knowledge on the left and a bounded file preview on the right. Full files open in the browser/native viewer without replacing Memory navigation state.

The backend may preserve `Source -> Document -> Claim/Datum -> Citation` semantics, but the ordinary user interface must not force that taxonomy into every compact row.

## Development

Normal peer sections remain exactly:

`Roadmap | Brainstorm`

### Roadmap

Roadmap exposes exactly:

`Timeline | Calendar`

A standalone `Board` destination is removed. Its useful state-management capability is preserved as a collapsible `Execution status` section under Timeline, normally emphasizing `Ready | In progress | Blocked`; Planned/Completed remain secondary/filterable states.

Timeline is project scheduling/dependency planning. Calendar is actual time allocation. One Roadmap item may have zero, one, or many Calendar blocks. Roadmap duration does not imply continuously occupied calendar time.

Calendar supports `Day | Week | Month | Agenda`; Week is the normal hour-by-hour planning view. Calendar supports work sessions, calls/meetings, experiments/lab sessions, reviews, reminders, deadlines and unavailable/personal blocks where useful.

Manual operator Add/Edit/Delete actions commit through the owning Roadmap/Calendar backend authority. Jarvis scheduling/work-item generation remains proposal-only until explicit acceptance. These action classes must not be collapsed merely because the same form/component can serve both paths.

### Brainstorm

The final Brainstorm model is:

`RAW -> discussion/reconciliation with Jarvis -> RECONCILED -> explicit promotion`

This supersedes the earlier proposal-inbox/Kanban-style UI assumption in PD-03.

RAW is intentionally unstructured capture. Original raw text/files remain preserved. Future local speech-to-text is a first-class direction; the UI may expose paperclip/microphone capture affordances before the backend speech path exists, provided the unavailable/future state is truthful.

RECONCILED is compact at rest and expands inline. A reconciled idea contains the discussion synthesis, accepted/rejected trade-offs, open questions, structured content/diagrams where useful, and compact provenance back to raw notes, files, relevant discussion and project/Coding context.

Opening an idea for reading does not silently add it to Jarvis context. Context accumulation is explicit through `Add to Jarvis context`/`Discuss with Jarvis`, supports multiple records simultaneously, and is visibly removable.

Promotion is explicit:

- `Add to Roadmap` creates/plans project work;
- `Promote -> Design` enters the Design proposal/change path;
- `Promote -> Coding` enters the Coding development-proposal path.

No Brainstorm action silently crosses an authority boundary.

## Coding

Normal peer sections remain exactly:

`Repository | Runtime`

### Repository

Repository represents GitHub remote/future JarvisOS state, not the currently executed local runtime.

The primary read/inspection surface is a `Repository Inspector`, not a permanently visible architecture graph.

Repository Inspector should progressively search/inspect repository-readable artifacts including:

- specs and Markdown;
- architecture documents and SVGs;
- code;
- tests;
- workflows/configuration;
- images and other safe previewable repository artifacts;
- PR/commit/review/check context where useful.

A selected artifact exposes a bounded preview appropriate to its type and, when available:

- `Add to Jarvis context`;
- `Suggest modification`;
- `Open on GitHub`.

These actions retain distinct semantics: Add-to-context is explicit context mutation, Suggest-modification is proposal-only, and Open-on-GitHub is navigation. Selection/browsing alone does none of them.

`Suggest modification` is proposal-only. It may produce a proposed diff/plan, but accepted mutation still follows the isolated Coding lifecycle:

`Proposal -> Plan -> Implementation -> Tests -> Independent Review -> Reconciliation -> Merge`

Architecture remains supported as an inspectable artifact family and may later gain a semantic graph/editor contract, but it is not permanently pinned to the normal Repository view.

### Runtime

Runtime represents the JarvisOS files/build actually executed on the maintainer workstation.

Local-vs-GitHub divergence is a first-screen concept:

- local actually executed version: green visual treatment plus explicit text such as `Local current` / `actually executed`;
- latest approved GitHub version: orange visual treatment plus explicit text such as `Latest GitHub` / `not yet executed locally` when newer;
- alignment state must be explicit and must not rely on color alone.

When GitHub is ahead, Runtime exposes a semantic delta summarizing what changed after the local SHA, derived from actual commit/file differences. The user can inspect the underlying commits/files and distinguish runtime-affecting changes from docs/reference-only changes where evidence permits.

The safe update path remains guarded and reversible, but the migration/build/restart phase list does not permanently dominate the screen. It is compact until the operator requests update preparation.

### Integrated terminal direction

Coding Runtime should eventually include a real integrated local terminal, with PowerShell as the Windows default shell, rather than requiring the user to leave JarvisOS and open a separate PowerShell window.

The terminal is not a frontend shell escape. Required direction:

- real PTY/session execution behind a typed local backend/runtime boundary;
- session-scoped working directory, persistent scroll/history for the active session, `Ctrl+C`/interrupt support and correct stdout/stderr streaming;
- repository/worktree-aware `Open terminal here` actions;
- optional multiple terminal tabs only if the first implementation demonstrates need;
- terminal/log presentation may share the lower Runtime area via `Terminal | Logs` tabs;
- `Send output to Jarvis` / selected-output context is allowed through a bounded context action;
- Jarvis may propose commands and offer `Insert in terminal`/copy, but commands are not silently executed by default;
- destructive/high-authority commands require explicit confirmation/policy and must never gain secret access through prompt leakage;
- frontend has no arbitrary filesystem/process authority; all execution is backend-mediated and policy/audit bounded;
- Windows is the maintainer runtime, but CI/tests must use a replaceable/fake PTY boundary rather than requiring PowerShell on Linux CI.

The terminal must preserve the self-improvement rule: terminal access does not authorize live code mutation to bypass Git/spec/review/update boundaries.

## Settings

Normal tabs remain exactly:

`Appearance | AI | System`

Settings remains compact and provider-agnostic. Credentials belong to provider/integration identity, not individual model rows. Generic provider management, orchestration policy, budget/limits and System diagnostics should reuse canonical backend boundaries rather than create frontend-owned state. Provider API identities and coding-tool integrations such as Codex/Claude Code remain separately representable where semantically distinct.

## Implementation promotion rule

The final visual/product direction is broader than spec 100, which implemented a bounded visual pass over the then-existing runtime. Future runtime work must therefore be decomposed into independent backend/read-model/frontend slices rather than treated as one giant `visual identity` follow-up.

`docs/spec-drafts/FINAL_VISUAL_IMPLEMENTATION_PACK_2026-08-27.md` contains draft candidate slices. `docs/design-references/FINAL_OPERATOR_INTERACTION_CONTRACT_2026-08-27.md` preserves the user-visible action/state semantics those slices must collectively implement. Those drafts are not implementation authority.

Before implementing them, the repository should promote a definition-only authority/queue-rederivation slice that:

1. audits exact post-100a/100b master;
2. compares the draft slices with existing planned specs 101–110 and all merged capability owners;
3. eliminates overlap and second truth stores;
4. allocates final spec IDs/dependencies/order;
5. preserves one implementation front at a time;
6. requires the normal definition/full-spec/readiness lifecycle for each runtime slice;
7. assigns every capability-matrix row and interaction-contract family to a final owner or explicit reference/defer/supersession disposition.

## Hard lines

- No frontend direct provider, filesystem, shell, Git or execution-tool authority.
- No generic stale/validation claims invented by UI.
- No duplicate repository/project truth store solely to support search/preview.
- No architecture diagram treated as authoritative merely because it is rendered.
- No Brainstorm content silently promoted to Memory/Design/Coding authority.
- No Roadmap/Calendar duplicate stores.
- No claim that GitHub latest is already the locally executed runtime.
- No terminal command auto-execution by Jarvis as the default interaction.
- No self-update without exact target identity, dirty-state guard, deterministic preparation, health verification and rollback semantics.
- No replacement of an approved action class/state transition with a simpler behavior solely because implementation is easier or backend support is incomplete.

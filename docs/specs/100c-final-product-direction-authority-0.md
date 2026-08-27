# 100c FINAL-PRODUCT-DIRECTION-AUTHORITY-0

Status: definition-only authority kernel; not implementation-ready; no runtime authority.

## Purpose

Re-derive the post-cleanup JarvisOS implementation queue from exact current `master` after the maintainer-completed final visual/product inspection, using the final product contract and draft implementation pack as planning inputs while preserving all merged authority and eliminating overlap with every semantically overlapping live/planned registry row.

This slice exists because spec 100 implemented a bounded visual pass over the then-current operator workstation, while the completed maintainer inspection subsequently froze broader product behavior for Memory, Development, Coding, Settings and the future integrated terminal. Those decisions must not be implemented ad hoc from design references or chat context.

## Trigger / intended queue position

This authority slice is intended to be inserted **after 100b CODEBASE-LEAN-CLEANUP-1 and before 101 CANONICAL-STATE-WRITE-1**.

The reason for the position is deliberate:

1. 100a first audits exact post-visual code for real ownership, dead/superseded residue, desired-but-unwired capabilities, duplication and upstream candidates;
2. 100b then performs only the evidence-backed cleanup/no-action disposition;
3. 100c re-derives future product/domain/frontend ownership from the simpler exact master rather than designing new contracts around code that 100a/100b may remove or consolidate;
4. only then should the remaining overlapping planned queue and the newly frozen operator-product capabilities be promoted/reordered.

Until `docs/specs/STATUS.md` explicitly contains/activates this row, this document is recorded maintainer direction only and grants no queue authority.

## Governing inputs

At execution, resolve exact current versions of:

- `AGENTS.md`;
- `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`;
- `docs/specs/STATUS.md`;
- `docs/ARCHITECTURE.md` and `docs/DECISIONS.md`;
- PD-01 through PD-08, especially PD-02, PD-03, PD-04, PD-05, PD-07 and PD-08;
- all approved visual/product references under `docs/design-references/`;
- `docs/spec-drafts/FINAL_VISUAL_IMPLEMENTATION_PACK_2026-08-27.md`;
- `docs/spec-drafts/FINAL_OPERATOR_CAPABILITY_MATRIX_2026-08-27.md`;
- exact merged outputs/reports from 100a and 100b;
- exact current code/read/write owners for project memory, modeling, events, files, search/FTS, AI/providers, GitHub/repository integration, local runtime, runners/tools, frontend routes/components and security boundaries;
- **every non-merged `STATUS.md` row whose scope semantically overlaps the final product direction**, including but not limited to 053/055, 063/064, 069, 101–110 and any row added before 100c executes.

## Authority task

100c is a **definition/queue-rederivation** slice. It must produce repository-authoritative planning, not runtime code.

Required output:

1. Audit each pseudo-spec FV-B01..FV-B23 and FV-F01..FV-F15 against exact current code and accepted specs.
2. Classify every draft as one of:
   - `PROMOTE_SEPARATE` — deserves an independently removable canonical spec;
   - `MERGE_INTO_EXISTING` — behavior belongs inside an existing planned slice after explicit re-derivation;
   - `MERGE_WITH_DRAFT` — multiple draft slices share one real owner and should become one canonical spec;
   - `DEFER_TRIGGERED` — retain only behind a concrete future trigger/prerequisite;
   - `REFERENCE_ONLY` — product/reference behavior, no independent runtime slice;
   - `REJECT` — unnecessary, duplicative or unsafe after exact-master audit.
3. For each retained behavior, identify the single canonical backend/state owner and the single frontend read/action contract. No second truth stores.
4. Classify **every semantically overlapping non-merged live `STATUS.md` row** with an explicit disposition such as `RETAIN`, `REDERIVE`, `MERGE`, `REORDER`, `DEFER` or `CANCEL/SUPERSEDE`. The audit must not stop at 101–110. Rows such as 053/055, 063/064 and 069 are examples that must be inspected if still live/overlapping at execution time; the exact registry at 100c start is authoritative.
5. State exactly which of 101–110 remain valid unchanged, which require re-derivation, which are reordered, and which are superseded/merged, as a subset of the broader live-row disposition required above.
6. Allocate final canonical spec IDs/names/dependencies for retained new slices.
7. Update the binding order in `STATUS.md` once, preserving already merged work and one implementation front at a time.
8. Preserve frontend/backend separation: frontend visual references never authorize fake backend state; backend capability is not deleted merely because it lacks a current frontend consumer.
9. Preserve 066–068 and 080 freeze unless a separate explicit maintainer decision changes it.
10. Preserve 093/Aspen-like editable process topology exclusion unless later engineering-domain authority explicitly reopens it.
11. Record migration/compatibility obligations for removing old peer destinations while preserving direct links/backend capabilities where required.
12. For every capability row in `FINAL_OPERATOR_CAPABILITY_MATRIX_2026-08-27.md`, record a final owning spec, reference-only disposition, concrete deferral trigger, or explicit maintainer-authorized rejection/supersession.

## Product decisions that must survive re-derivation

### Global shell

Normal primary navigation:

`Design | Memory | Development | Coding | Settings`

No normal Home.

### Design

`Process | BLUECAD` only as peer modes. Model/Results/Runs/Evidence/Lineage remain contextual/owned information.

### Memory

`Project Basis | Models | Literature` only.

- Project Basis supports PD-07 deterministic impact/revalidation/working-revision semantics.
- Models use overview-first bounded disclosures and exact version ownership.
- Literature uses compact list + inline multi-expand + bounded preview/full-file open.
- Search is a read projection, not another truth store.

### Development

`Roadmap | Brainstorm` only.

- Roadmap exposes `Timeline | Calendar`; standalone Board is removed and execution status is embedded under Timeline.
- Calendar is actual hour/minute scheduling and may link multiple blocks to one Roadmap item.
- Brainstorm is `RAW -> discussion/reconciliation -> RECONCILED -> explicit promotion`, not the older proposal-inbox/Kanban UI assumption.
- explicit Jarvis context basket; opening an idea does not silently add context.

### Coding

`Repository | Runtime` only.

Repository:
- remote GitHub/future state;
- Repository Inspector is the main general search/preview surface;
- specs/Markdown/SVG architecture/code/tests/config/workflows/images may be inspected safely;
- `Add to Jarvis context`, `Suggest modification`, `Open on GitHub`;
- architecture is searchable/inspectable, not permanently pinned;
- modification remains proposal -> isolated development lifecycle.

Runtime:
- local actually executed SHA and latest approved GitHub SHA are independently truthful;
- explicit aligned/local-behind/divergent state;
- semantic delta is evidence-backed by real commits/files;
- safe update remains guarded/reversible but phases need not dominate the first screen;
- future integrated real terminal uses a separate typed backend PTY/session boundary, PowerShell-default on Windows, never frontend shell authority;
- PTY promotion must preserve the repository-wide no-secret frontend-response invariant through a proven backend secret-safe display/isolation boundary.

### Settings

`Appearance | AI | System` only. Provider/integration credentials are provider-scoped, not model-scoped; reuse canonical secure storage/policy/provider gateway.

## Mandatory overlap questions

The re-derivation must explicitly answer:

- Can 101/102 own Project Basis/model changeset/revalidation/reconciliation, or are independently removable additions needed?
- Which existing modeling/version/run/event/file/search owners can project MODEL-DOSSIER/LITERATURE/PROJECT-SEARCH without new canonical tables?
- Which pre-101 planned rows overlap the same product behavior, and should each be retained, rederived, merged, reordered, deferred or cancelled?
- Should Roadmap and Calendar share one store with separate event/time-allocation entities, or is another minimum structure required?
- Can Brainstorm reuse existing proposal/decision/event infrastructure without inheriting obsolete inbox semantics?
- Is there already sufficient GitHub connector/backend capability for repository observability/preview, or must a narrow local service be introduced?
- What is the minimum backend boundary for local runtime identity without building the self-update supervisor prematurely?
- What security/auth/process/secret-display boundary is required before any PTY/PowerShell terminal can be safe?
- Which frontend route/component migrations can occur before backend work using truthful unavailable/readonly states, and which must wait?
- Which engineering-domain dependencies remain valid after 100a/100b and final operator-product needs?

## Deliverables

100c completion requires:

- one exact-master overlap/ownership audit covering the pseudo-spec pack **and every overlapping non-merged live registry row**;
- one canonical queue re-derivation document;
- one `STATUS.md` registry patch allocating/reordering retained slices and resolving duplicate/overlapping planned ownership;
- per-retained-slice kernel links or explicitly queued kernel-drafting steps;
- explicit rejected/deferred draft list with reasons so later agents do not resurrect discarded architecture by chat memory.

## Acceptance criteria

- Every FV draft has a documented disposition.
- Every semantically overlapping non-merged `STATUS.md` row has an explicit retain/rederive/merge/reorder/defer/cancel disposition; no duplicate live owner remains merely because it predates 100c.
- No retained behavior depends on a parallel truth store without explicit minimum-necessary proof.
- Existing 101–110 have explicit retain/rederive/merge/reorder dispositions.
- Final queue is acyclic and preserves one implementation front.
- Final queue contains the required backend authority before any frontend that would otherwise fabricate state.
- Safe self-update and integrated terminal are distinct authority slices unless exact-master evidence proves one minimal boundary can safely own both without broadening command/process authority.
- The terminal cannot be promoted without an explicit security/failure-mode spec covering local-only access, PTY lifecycle, process/environment secret isolation, secret-safe frontend output/redaction, protected path/cwd validation, command confirmation policy, Jarvis-context secret handling and offline CI fakes.
- Brainstorm speech capture cannot be promoted as a parallel inference path; every transcription inference must use the canonical AI execution spine and ledger/audit semantics.
- No runtime file changes occur in 100c.

## Non-goals

- no backend/frontend/schema/runtime implementation;
- no codebase cleanup already owned by 100a/100b;
- no automatic promotion of every draft into a spec;
- no new provider/Hermes authority;
- no terminal implementation;
- no editable semantic architecture graph implementation;
- no Process/PBR/multifidelity implementation;
- no removal of desired-but-unwired capability merely because the current frontend does not expose it.

## Test del minimo necessario

Criterio di accettazione della spec:
Produce one exact-master authority map and binding queue that can implement the final maintainer-approved product without duplicate stores, duplicate live planned owners, fake frontend state or ad-hoc queue changes.

Questo lavoro serve a soddisfarlo? **sì** — the final product decisions cross multiple existing/future owners and PD-06 already requires an authority re-derivation before implementation.

Il criterio è raggiungibile senza di esso? **no** — directly implementing the draft pack would create a parallel queue and could duplicate or pre-empt existing planned work.

Se sì: perché lo aggiungo comunque: N/A.

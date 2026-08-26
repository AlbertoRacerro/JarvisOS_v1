# PD-06 — Future specification decomposition

Status: planning map only; not implementation authority and not a parallel queue.

## Purpose

Provide an explicit translation path from the 2026-08-26 maintainer-approved product direction into future real specifications without prematurely changing `docs/specs/STATUS.md`.

The current `STATUS.md` queue and post-100 visual-inspection hold remain authoritative until a dedicated definition/authority spec re-derives them.

## Required first promotion step

Before runtime implementation of this packet, create one definition-only authority specification whose job is to:

1. cite PD-01 through PD-05;
2. reconcile the new primary navigation with merged operator-workstation authority (081/095 and merged frontend slices);
3. explicitly retire/supersede the old user-facing assumption that `Runs`, `Engineering Data`, `Review`, `Model`, `Results` or `Lineage` remain normal peer destinations where this packet says otherwise;
4. preserve reusable merged backend capabilities even when their old frontend destination is removed;
5. re-derive the remaining post-100 implementation order;
6. state which existing planned specs 101–110 remain valid unchanged, which require re-derivation, and which new slices are required;
7. retain one-implementation-front repository rules unless separately amended.

Do not silently edit an existing implementation spec to absorb this product-direction change.

## Candidate backend/domain slices

The names below are descriptive placeholders, not allocated spec IDs.

### A. Project Memory foundation

Potential independently reviewable slices:

- `PROJECT-BASIS-1`: canonical project-level requirements/constraints/decisions and read APIs;
- `MODEL-DOSSIER-1`: aggregate exact model-version definition, assumptions, equations/methods, parameters, Process/BLUECAD references, results, validation, criticalities, artifacts, runs and lineage without duplicating canonical records;
- `LITERATURE-SOURCE-1`: structured Source/Document/Claim-or-Datum/Citation provenance, contextual conditions and links to records/models;
- `PROJECT-SEARCH-1`: unified project-memory search across structured records and indexed attached content, extending existing FTS/search infrastructure rather than building a second index unnecessarily;
- `ACTIVITY-TIMELINE-1`: event/read-model projection for readable project history, only if needed after canonical event ownership is clear.

Existing 101/102 or other planned canonical-state/evidence work may provide prerequisites or overlap. A future authority spec must inspect them and decide whether to rederive, depend on, or keep them separate; do not rename/reinterpret them by chat convention.

### B. Development foundation

Potential slices:

- `ROADMAP-1`: milestone/task/dependency/deadline canonical model with Timeline/Calendar/Board projections over one store;
- `BRAINSTORM-1`: non-authoritative notes/proposals/warnings/reminders with provenance;
- `PROPOSAL-INBOX-1`: persistent lifecycle, priority, snooze/reminder semantics and explicit promotion to Roadmap/Memory;
- `DEVELOPMENT-JARVIS-ACTIONS-1`: bounded Jarvis actions that create/update proposals and prepare promotion without silently crossing authority boundaries.

Priority semantics must preserve `Critical`, `High`, `Normal`, and `Opportunity`; color is supplemental only.

### C. Coding/repository foundation

Potential slices:

- `REPOSITORY-OBSERVABILITY-1`: canonical read-only repository/branch/head/PR/check/review state for the Coding workspace;
- `DEV-PIPELINE-STATE-1`: persistent `Proposal -> Plan -> Implementation -> Tests -> Independent Review -> Reconciliation -> Merge` state model with exact-head invalidation;
- `HERMES-DEV-ORCHESTRATION-1`: later candidate integration of Hermes as 24/7 orchestrator behind JarvisOS authority/policy, after a concrete runtime boundary and evaluation prove it superior to current automation patterns;
- `CODING-KNOWLEDGE-1`: searchable JarvisOS architecture/decision/invariant/known-limitation knowledge tied to code/PR provenance;
- `ARCHITECTURE-GRAPH-1`: semantic typed block/edge architecture model and read/write contract;
- `ARCHITECTURE-EDITOR-1`: frontend/editor interaction over the accepted graph contract;
- `JARVIS-CODING-ACTIONS-1`: contextual inspect/plan/implement/check/reconcile proposals behind repository authority.

Do not combine the semantic architecture store with arbitrary drawing coordinates. Semantic graph changes and layout-only changes require distinguishable provenance.

### D. Local Runtime/self-update foundation

Potential slices:

- `LOCAL-RUNTIME-IDENTITY-1`: running commit/version/worktree/branch/health versus remote master;
- `SAFE-SELF-UPDATE-1`: exact-target update contract, dirty-worktree guard, migration/build/smoke/health gates, restart and automatic rollback;
- `RUNTIME-CODING-BRIDGE-1`: safe deep links between remote repository objects and the local running installation.

The frontend must never directly gain unrestricted filesystem/shell/Git authority. Local operations belong behind a typed backend boundary and policy.

### E. Generic AI provider/settings foundation

Potential slices:

- `PROVIDER-CREDENTIALS-GENERIC-1`: generalize accepted secure credential storage to multiple provider/integration identities without parallel secret stores;
- `PROVIDER-CATALOG-1`: discover/refresh available provider models/capabilities where supported;
- `ORCHESTRATION-POLICY-VIEW-1`: expose canonical permission/routing/fallback/sensitivity/budget state to Settings;
- `HERMES-PRODUCT-ORCHESTRATION-1`: only after a separately proven Hermes boundary defines what Hermes owns and what JarvisOS policy/deterministic code continues to own.

Existing provider gateway specs 015/018, secure credential storage 082, Scaleway spine 094 and current policy/egress infrastructure are prerequisites/evidence, not disposable sunk cost and not automatic final architecture.

## Candidate frontend slices

Frontend specs should be created after each owning backend/read contract is sufficiently stable, except for visual-reference/prototype work that is explicitly non-runtime.

Likely slices:

- shell/nav replacement to `Design / Memory / Development / Coding / Settings` and removal of normal Home;
- Design `Process | BLUECAD` navigation/context-strip reconciliation;
- Memory `Project Basis | Models | Literature`;
- Development `Roadmap | Brainstorm`;
- Coding `Repository | Runtime`;
- Settings `Appearance | AI | System` reconciliation to the approved HTML/product contract.

Do not couple all five workspaces into one giant frontend implementation spec.

## Parallel-work recommendation while visual HTML is still being designed

Parallel **specification drafting/research** is useful; parallel uncoordinated runtime implementation is not yet recommended.

Once this product-direction packet is merged, builders may productively work on docs-only activities such as:

- audit current backend ownership against the candidate slices above;
- draft definition kernels/full specs for backend slices whose product semantics are already frozen;
- identify overlap with 101–110 and propose an exact queue re-derivation;
- prepare deterministic acceptance criteria and migration evidence.

Keep those drafts `planned`/non-authoritative until the normal lifecycle promotes them.

Do **not** use this planning packet itself as permission to start backend runtime implementation while the current post-100 hold remains active.

## Suggested promotion order after the maintainer finishes the current visual/product inspection

The future authority spec should decide exact IDs, but the least-churn dependency shape is likely:

1. authority/queue re-derivation;
2. canonical state foundations that existing 101/102 still legitimately own;
3. Project Memory backend/read models;
4. Development proposal/roadmap backend;
5. generic provider/settings backend generalization;
6. Coding repository observability and development-pipeline state;
7. Hermes development orchestration evaluation/integration;
8. local runtime identity and safe self-update;
9. semantic architecture graph, then editor;
10. workspace frontends over the accepted contracts;
11. later engineering-domain/process/CAD evaluator work in the dependency order revalidated against existing 103–110.

This order is a recommendation for the future authority spec, not a change to `STATUS.md`.

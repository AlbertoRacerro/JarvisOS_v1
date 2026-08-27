# PD-06 — Future specification decomposition

Status: planning map only; not implementation authority and not a parallel queue.

## Purpose

Provide an explicit translation path from the maintainer-approved product direction into future real specifications without prematurely changing `docs/specs/STATUS.md`.

PD-08 is the final 2026-08-27 product/visual reconciliation layer. Where the older decomposition below would conflict with PD-08, the approved UI manifest or frontend conformance contract, the newer final layer wins. This file must not be used to resurrect superseded Board/proposal-inbox/permanent-architecture assumptions.

`docs/specs/STATUS.md` remains the sole live queue authority. The post-100 visual-inspection hold was released and registry-reconciled on 2026-08-27; current queue state must always be re-read from exact `STATUS.md`.

## Required first promotion step

Before runtime implementation of the final product-direction packet, execute a definition-only authority/queue-rederivation slice when and only when `STATUS.md` authorizes it. That authority work must:

1. cite PD-01 through PD-08, with PD-08 as the final product-composition reconciliation; PD-06 remains the planning/decomposition map;
2. cite `docs/design-references/APPROVED_OPERATOR_UI_MANIFEST_2026-08-27.md`, `docs/design-references/FRONTEND_CONFORMANCE_CONTRACT_2026-08-27.md`, the most-specific canonical HTML/reference, and `docs/spec-drafts/FINAL_OPERATOR_CAPABILITY_MATRIX_2026-08-27.md` for any frontend/product-facing slice;
3. reconcile the new primary navigation with merged operator-workstation authority (081/095 and merged frontend slices);
4. explicitly retire/supersede old user-facing peer-page assumptions where final product direction says otherwise, while preserving reusable backend capability and compatible deep links where required;
5. audit exact post-100a/100b master and re-derive the remaining implementation order;
6. classify every semantically overlapping non-merged `STATUS.md` row — not only 101–110 — as retained, rederived, merged, reordered, deferred or cancelled/superseded;
7. audit every FV-B/FV-F pseudo-spec and every capability-matrix row, allocate one canonical owner for each retained behavior, and eliminate second truth stores;
8. retain one-implementation-front repository rules unless separately amended;
9. preserve backend-before-frontend authority whenever a frontend would otherwise have to fabricate state;
10. keep self-update, interactive terminal authority and AI/model execution as separate security/egress responsibilities unless exact-master evidence proves a smaller safe boundary.

Do not silently edit an existing implementation spec to absorb this product-direction change and do not implement directly from this planning map.

## Candidate capability families

The names below remain descriptive planning families, not allocated live spec IDs. `docs/spec-drafts/FINAL_VISUAL_IMPLEMENTATION_PACK_2026-08-27.md` is the complete 2026-08-27 pseudo-spec inventory and supersedes the older partial candidate lists previously carried in this file.

### A. Project Memory / model authority

Required future capability families include:

- project-level basis: objective/question, requirements, acceptance criteria, stable constraints, boundary conditions, standards/regulations, decisions and resource/capability constraints;
- exact model/version dossier read projection over canonical records;
- bounded model change sets and inspectable working revisions;
- deterministic impact/revalidation that re-evaluates stored exact outputs when sufficient and requests recomputation only where genuinely required;
- model reconciliation/promotion preserving immutable prior snapshots;
- Literature source/document/claim-or-datum/citation provenance and bounded preview;
- project search as a read projection over existing canonical records/indexes.

PD-07 remains binding for change-set/revalidation/reconciliation semantics. Do not implement a generic indefinite `stale` state when deterministic evaluation against exact stored outputs can resolve the condition immediately.

### B. Development

Final Development semantics are exactly those reconciled in PD-08:

- peer sections: `Roadmap | Brainstorm`;
- Roadmap views: `Timeline | Calendar` only;
- no standalone Board page; operational state is a collapsible Timeline `Execution status` emphasizing `Ready | In progress | Blocked`;
- Roadmap stores project work/window/dependency intent; Calendar stores actual date/time allocation and one Roadmap item may link to zero/one/many Calendar blocks;
- Brainstorm is `RAW -> discussion/reconciliation -> RECONCILED -> explicit promotion`, not the older Inbox/Exploring/Candidate/Proposal-Inbox Kanban model;
- Jarvis context accumulation is explicit and removable;
- promotion to Roadmap, Design or Coding is explicit and never silently crosses authority boundaries;
- future speech capture is local-first in product intent but every transcription inference must use the canonical AI execution spine/ledger and privacy/egress policy.

### C. Coding / Repository

Required capability families include:

- remote repository observability with exact repo/branch/SHA/PR/check/review identity;
- Repository Inspector search/preview across safe repository artifacts such as Markdown/specs/code/tests/config/workflows/architecture SVG/images;
- `Add to Jarvis context`, proposal-only `Suggest modification`, and `Open on GitHub`;
- persistent inspectable Coding lifecycle `Proposal -> Plan -> Implementation -> Tests -> Independent Review -> Reconciliation -> Merge` with exact-head invalidation;
- searchable Coding knowledge tied to accepted specs/ADRs/architecture/invariants/provenance;
- optional semantic architecture artifacts only after separate need/readiness proof.

Architecture is **not** permanently pinned to the normal Repository first screen. It is an inspectable artifact family inside Repository Inspector.

Frontend never receives direct GitHub credentials or mutation authority. `Suggest modification` is not a save-to-file shortcut.

### D. Local Runtime / divergence / self-update

Required capability families include:

- actual local runtime identity: running commit/version/worktree/branch/dirty state/services/health;
- separately observed approved/latest GitHub target identity;
- explicit aligned/local-behind/divergent state;
- evidence-backed semantic delta between exact local and remote SHAs with underlying commits/files inspectable;
- safe exact-target self-update with state preservation, dirty-state guard, migration/build/smoke evidence, explicit restart, post-restart health and rollback.

The normal Runtime first screen should prioritize local-vs-GitHub identity/divergence. Update phases stay compact until update preparation is requested.

### E. Integrated local terminal

The final product direction includes a future real `Terminal | Logs` surface in Coding Runtime, with PowerShell default on Windows, but only behind a separately specified PTY/session security boundary.

Any retained terminal slice must prove all of the following before promotion:

- backend-owned PTY/session lifecycle, cwd validation, stdin/stdout/stderr/interrupt support;
- no frontend-direct process/filesystem/shell authority;
- scrubbed/minimum child environment with no inherited provider/API/repository credentials by default;
- a backend secret-safe display/redaction/isolation boundary before terminal output becomes a frontend response;
- protected-path/credential-store handling and local-only/auth policy;
- high-risk command confirmation/policy;
- explicit Jarvis command proposal/insert/copy semantics with no default auto-execution;
- bounded `Send output to Jarvis` with secret policy;
- fake/replaceable PTY adapter for CI rather than requiring live Windows PowerShell.

If adequate secret isolation/redaction cannot be proven on the target OS/runtime, arbitrary PTY streaming remains deferred/unavailable rather than weakening the repository no-secret invariant.

### F. Generic AI provider/settings

Required capability families include:

- provider/integration-scoped secure credentials, not API keys attached to individual model rows;
- provider connectivity/capability/model catalogue where supported;
- orchestration/routing/fallback/privacy/egress/budget policy projections over accepted backend authority;
- local AI as a provider/runtime capability without assuming external credentials;
- System diagnostics from observed backend/runtime/database/service state.

Existing provider gateway specs 015/018, secure credential storage 082, Scaleway spine 094 and policy/egress infrastructure are prerequisites/evidence, not disposable sunk cost and not automatic final architecture. Hermes labels must not create Hermes authority before a separately accepted backend contract exists.

## Candidate frontend families

Frontend specifications should normally follow sufficiently stable owning backend/read contracts, except for clearly non-functional visual/reference work that preserves truthful unavailable states.

Final required workspace composition is:

- shell rail `Design | Memory | Development | Coding | Settings`, no normal Home;
- Design `Process | BLUECAD`;
- Memory `Project Basis | Models | Literature`;
- Development `Roadmap | Brainstorm`, Roadmap `Timeline | Calendar`, no Board peer page;
- Coding `Repository | Runtime`, with Repository Inspector and local-vs-GitHub Runtime divergence;
- Settings `Appearance | AI | System`;
- future Runtime `Terminal | Logs` only after terminal backend/security authority exists.

Every surface listed in the canonical UI manifest must be implemented against its exact HTML/reference viewport and the frontend conformance contract. Missing backend capability is implementation work, not permission to redesign the approved frontend away.

Do not couple all workspaces into one giant frontend implementation spec.

## Parallel-work recommendation

Parallel specification drafting/research may be useful; parallel uncoordinated runtime implementation is not authorized by this file.

Builders/coordinators may only work on whichever definition/spec/readiness/implementation front live `STATUS.md` authorizes. Planning documents may support audits and future kernel drafting, but they do not create a second queue.

## Suggested promotion shape after exact post-cleanup re-derivation

The future authority spec must derive exact IDs/order from current evidence, but a likely dependency shape is:

1. canonical authority/evidence foundations retained from overlapping live rows;
2. Project Memory/model read and PD-07 change/revalidation/reconciliation capability;
3. Development Roadmap/Calendar/Brainstorm domain;
4. generic provider/settings backend projection;
5. Repository observability/Inspector and Coding lifecycle;
6. local Runtime identity/divergence;
7. safe self-update;
8. integrated terminal PTY as a separate security-bounded slice;
9. frontend workspace migrations over stable truthful contracts;
10. optional speech capture/semantic architecture only when prerequisites and value remain valid;
11. engineering Process/PBR/multifidelity work in the dependency order revalidated against exact current engineering specs.

This order is a recommendation for the future authority spec, not a change to `STATUS.md`.

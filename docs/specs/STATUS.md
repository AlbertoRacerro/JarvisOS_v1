# Spec status and roadmap

This file is the single live source of truth for JarvisOS spec state and near-term
roadmap. Individual spec files define scope, acceptance criteria, tests, and
non-goals; their legacy `Status:` lines are not authoritative.

Update this table whenever work starts, a PR opens, a dependency changes, a PR
merges, or a spec is cancelled. GitHub PR diffs are the authoritative list of
files created or modified by a spec; this registry intentionally does not copy
those file lists into a second place.

The `Implementation PR` column records implementation PRs only. A PR that merely
creates or revises a spec does not occupy that column and does not move the spec
to `in_review`; link such planning evidence in the description only when useful.

Rows marked `planned` are roadmap outlines, not implementation contracts. They
must pass the normal backlog row → kernel → full spec → implementation ladder
before Codex or another coding agent may act on them.

## Status values

- `planned`: the work is identified, but the spec is not ready to implement.
- `blocked`: the spec exists but a dependency or decision prevents work.
- `ready`: the spec is complete and may be started.
- `in_progress`: implementation is active and no PR is open yet.
- `in_review`: an implementation PR is open; CI/review/maintainer decision is pending.
- `merged`: the implementation PR is merged into `master`.
- `cancelled`: the work will not be implemented or has been superseded.

## Update rules

1. Before starting work, confirm the row is `ready` and all hard dependencies are
   `merged`.
2. Set the row to `in_progress` when a branch or implementation session starts.
3. Set it to `in_review` and add the implementation PR number as soon as that PR
   exists.
4. The merge owner sets it to `merged` immediately after merge.
5. Use `blocked` with an explicit dependency or blocker; do not hide blockers in
   prose elsewhere.
6. Do not duplicate live spec state in `README.md`, individual spec files,
   `docs/JARVISOS_CURRENT_CONTEXT.md`, chat handoffs, or strategy documents.
7. CI runs `python scripts/check_spec_status.py --event "$GITHUB_EVENT_PATH"` on
   pull requests. A spec implementation PR fails if its row is absent, not
   `in_review`, missing the current PR number, or has an unmerged hard dependency.
## Repository operating regime — effective 2026-08-03

- One implementation front at a time.
- The assigned agent merges with an exact-head guard when deterministic gates are green and no current blocking review finding remains.
- Work proceeds through the authorized queue without per-step maintainer confirmation.
- The maintainer is contacted only for real spending/budget risk, genuinely missing credentials/accounts/repositories/organizations, security/secret risk, or an obstacle without two practicable routes.
- New infrastructure, credentials, state stores, or scope must pass the mandatory minimum-necessary test in the PR body.
- Independently removable specifications remain separate.

The frontend-beta direction and binding delivery queue are defined by spec 081.

The queue remains sequential and every implementation slice must still pass the normal
backlog row → kernel or definition → full spec → readiness → implementation → exact-head
gates → review → merge → registry-reconciliation lifecycle. A `planned` row is not
implementation authority.

The binding order is:

1. 081 FRONTEND-BETA-AUTHORITY-0 definition and registry reconciliation;
2. 082 SECURE-CREDENTIAL-STORAGE-0;
3. 094 SCALEWAY-NORMAL-SPINE-0;
4. 070 UI-FOUNDATION-1, freshly re-derived from current `master`;
5. 083 APP-SHELL-1;
6. 084 BLUECAD-READ-MODEL-1;
7. 085 BLUECAD-WORKBENCH-2;
8. 086 MODEL-INSPECTION-A0;
9. 087 LINEAGE-OVERVIEW-1;
10. 088 RUNS-WORKBENCH-1;
11. 035 ENGINEERING-DATA-1, freshly re-derived;
12. 089 ANALYTICS-DOCK-1;
13. 054 PROPOSAL-REVIEW-1, freshly re-derived;
14. request and complete the 062 operator-design session when the operator is available;
15. 090 AI-THREADS-0;
16. 091 JARVIS-SIDECAR-1;
17. 029 SETTINGS-1, freshly re-derived;
18. 092 SCENE-BINDING-0;
19. 058c SCENE-SEMANTICS-A1, freshly re-derived;
20. 006b PARAMETRIC-VARIANTS-1, freshly re-derived;
21. 058b VARIANT-COMPARISON-1, freshly re-derived.

The 062 design session is not an implementation front and may remain pending while Phase 5
proceeds. No Phase-5 slice may add, imitate, consume, or redesign the grade surface, and all
062-dependent work remains blocked until the operator design is complete.

Specs 066, 067, 068, and 080 remain frozen for the duration of this queue. Spec 078 remains
planned without implementation authority. Spec 093 and any Aspen-like editable flowsheet are
outside the binding queue.

The queue is binding but not immutable. If a slice proves non-implementable within its
accepted boundary, or a prerequisite proves insufficient, the active front stops and a later
definition-only authority spec may re-derive the remaining queue. Re-derivation must preserve
already merged slices, record the stop reason and reached state, retain the 066–068 freeze,
and explicitly identify any product decision from spec 081 that it changes. Silent
abandonment or substitution is not authorized.

## Current priority and drafting order

1. Preserve merged 059a/059b, 061a/061b, 075, 076, 077, and 079 authority boundaries.
2. Treat the merged 082/094 checkpoint as complete and use [the 2026-08-04 Windows evidence](082-094-windows-checkpoint-2026-08-04.md) as the transition record.
3. Specs 070 UI-FOUNDATION-1, 083 APP-SHELL-1, 084 BLUECAD-READ-MODEL-1, 085 BLUECAD-WORKBENCH-2, 086 MODEL-INSPECTION-A0, 087 LINEAGE-OVERVIEW-1, 088 RUNS-WORKBENCH-1, and 035 ENGINEERING-DATA-1 are merged and reconciled; 089 ANALYTICS-DOCK-1 is ready under [the 2026-08-15 readiness decision](089-readiness-2026-08-15.md) as the next canonical implementation slice. The maintainer-approved workstation reference continues to guide local information hierarchy, while global visual identity remains a separate independently removable lane.
4. Preserve the merged documentation contract for 078 without treating it as implementation authorization.
5. Keep 066–068 and 080 frozen, and keep 062 blocked until its operator-design decision.

## Registry

| Spec | Status | Implementation PR | Name | Depends on | Description |
| --- | --- | --- | --- | --- | --- |
| 001 | merged | [#4](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/4) | Parameter/Assumption schema freeze + Requirement record | — | Freeze engineering-record units, provenance, uncertainty fields, and requirement CRUD with additive migration behavior. |
| 002 | merged | [#7](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/7) | Local route smoke matrix + routing eval set | 001 | Add repeatable local-route measurements and an offline routing evaluation set without making live model calls in CI. |
| 003 | merged | [#8](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/8) | ESCALATE-CONFIRM-0 | 002 | Add a non-executing external escalation proposal and explicit user-confirmed execution path with cost, context-exclusion, and ledger controls. |
| 004 | merged | [#10](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/10) | Tiered PR review | — | Historical automated review foundation; external model reviews are now optional, manually triggered, and advisory only. |
| 005 | merged | [#12](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/12) | BLUECAD CAD adapter MVP | — | Define GeometrySpec v0, deterministic CAD construction/export, and Tier 0–1 validation foundations. |
| 005b | merged | [#19](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/19) | BLUECAD remaining part-kind builders | 005 | Add deterministic manifold, float, anchor-mount, and harvest-module builders plus interface-aware ports. |
| 006 | merged | [#23](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/23) | BLUECAD workbench + 3D viewer | 005, 010 | Add the operator workbench, secure BLUECAD artifact serving, candidate detail, validation reports, attempt history, and GLB viewing. |
| 006b | blocked | — | BLUECAD parametric variants | 006, 083, 085, 092, 058c | Remains blocked through Phases 1–5. Phase 6 may freshly re-derive deterministic child variants only after the new shell, migrated BLUECAD workbench, verified scene binding, and A1 scene semantics exist. |
| 006c | merged | [#30](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/30) | BLUECAD workbench UX pass | 006 | Add archive, malformed-detail inspection, promotion, retry/duplicate-brief flows, and safer validation rendering. |
| 007 | merged | [#17](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/17) | BLUECAD tool registry | 005 | Add fail-closed tool registration, health/hash checks, subprocess execution boundaries, and CI license-boundary enforcement. |
| 008 | merged | [#32](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/32) | BLUECAD Gmsh mesh adapter | 005, 007 | Generate deterministic Gmsh inputs and physical groups, invoke Gmsh through the registry, and return structured mesh-quality outcomes. |
| 009 | merged | [#35](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/35) | BLUECAD CalculiX FEM adapter | 008 | Assemble deterministic static CalculiX decks, run the registered solver, parse result summaries, and evaluate Tier 3 criteria. |
| 010 | merged | [#20](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/20), [#26](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/26), [#28](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/28) | BLUECAD AI loop v0 | 005 | Add the bounded candidate/attempt loop, safe-default parking, prompt/schema flow, validation, repair attempts, and traceable prompt versions. |
| 011 | planned | — | Core Team review panel | 034 | Add advisory persona reviews over artifacts and evidence; personas are bounded configurations, not autonomous authorities or a fake swarm. |
| 012 | planned | — | L2 ephemeral free-script proposals | 010, 016 | Trigger-gated only: reopen after non-loopback access, a second user, remote-agent/Hermes/MCP runner reachability, or a demonstrated need for non-bundled execution, and only behind a separate proven OS-isolation specification. |
| 013 | planned | — | Tier 2 domain-validator plugin interface | 005, 010 | Define a narrow plugin boundary for BlueRev-specific engineering checks that emit deterministic validation evidence without letting plugins own routing, memory, or promotion. |
| 014 | planned | — | OpenFOAM CFD case-bundle adapter v0 | 007, 008, 049 | Produce inspectable OpenFOAM case bundles and evidence only when process/light proxies leave a concrete decision unresolved; no generic CFD platform or automatic solver authority. |
| 015 | merged | [#33](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/33), [#43](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/43) | PROVIDER-GW-1 | 003 | Replace hardcoded bindings with a validated provider registry and generic OpenAI-compatible adapter while preserving safe defaults. |
| 016 | merged | [#39](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/39) | RUNNER-EXT-1: BLUECAD L2 | 005, 007 | Historical hashed/AST-checked `bluecad_l2_v0` contract; normal instantiation is disabled by the bundled-only runner cleanup, and hostile-code execution was never proven. |
| 017 | merged | [#37](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/37) | Autonomous three-tier review | 004 | Historical automatic chain; Cheap, Senior, and Expert reviews are now explicit maintainer actions with no automatic Codex or label actuation. |
| 018 | merged | [#33](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/33), [#43](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/43) | PROVIDER-GW-2 | 015 | Complete provider-cap/fallback enforcement and correct provider usage accounting while preserving explicit routing and audit controls. |
| 019 | merged | [#40](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/40), [#41](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/41), [#44](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/44) | Senior review hardening | 017 | Retain bounded requests, streaming, parsing, staleness, and diagnostics for manually dispatched reviews only. |
| 020 | cancelled | — | Pipeline doctor | 017, 019 | Cancelled because the automatic review/fix pipeline was removed; deterministic CI and explicit maintainer review remain authoritative. |
| 021 | merged | [#70](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/70) | ALPHA-GATE hardening | — | Enforce the server-owned external-provider decision at the shared execution spine for every concrete network binding and fallback; PR #70 supersedes stale PR #66. |
| 021b | merged | [#72](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/72), [#75](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/75) | ALPHA-GATE completion: real-tool proof + recoverable data root | 021, 038, 044 | Strict hash-verified real-tool proof merged in [#72](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/72), and atomic path-rebased backup/restore merged in [#75](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/75). |
| 022 | merged | [#49](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/49) | Codex PR autopush without automerge | 017, 019 | Retain the bounded same-branch actuator for explicit maintainer-requested Codex work; no workflow dispatches it automatically. |
| 023 | planned | — | Adversarial proposal corpus | 010 | Add bounded hostile and degenerate model-output fixtures; the loop must reject or park them without crashes, unbounded work, provider calls, or authority bypass. |
| 024 | merged | [#77](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/77), [#79](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/79), [#84](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/84), [#85](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/85) | FEM verification battery | 008, 009, 021b | 024-A, 024-B, 024-C1, and 024-C2 are merged; the registry-bound C3D10 analytic verification battery and deterministic report are complete. |
| 025 | planned | — | Semantic routing evaluation and promotion policy | 002, 010, 062 | After enough representative graded dogfood, choose a deterministic route-per-task-kind table on cost per useful outcome with holdout/promotion/reversion thresholds; the local classifier remains advisory and never owns provider permission. |
| 026 | planned | — | BoardSession stateful multi-persona sessions | 011, 034, 040 | Deferred post-alpha: add shared-state multi-persona sessions only after the advisory panel and memory/context spine prove useful in real work. |
| 027 | planned | — | Modal and thermal analysis types | 009, 024 | Extend the verified static-FEM boundary only when a real BlueRev decision requires modal or thermal analysis; do not pre-build a broad solver matrix. |
| 028 | planned | — | Additive migration discipline | — | Document and test the existing versioned, additive migration policy before schema growth makes drift costly; no migration framework rewrite. |
| 029 | planned | — | Settings and secrets operator page | 015, 018, 061a, 082, 083, 090 | Re-derive as SETTINGS-1 after secure persistence, the application shell, and thread provenance exist; expose provider, budget, usage, storage and diagnostic state without placing keys in localStorage, logs, repository files, or normal frontend state. |
| 030 | cancelled | — | Conversation-to-proposal handoff | 042 | Cancelled as a standalone conversation slice. Its valid workspace-scoped proposal handoff is absorbed by 090 and 091 and must continue to use existing MemoryStore and deterministic execution boundaries. |
| 031 | planned | — | Policy-owned design vocabulary surface | 005, 067, 090, 091 | Retain the JarvisOS-owned bounded capability and vocabulary contract so any future interaction surface reports what is expressible, approximate, or unsupported; no second conversation engine or authority. |
| 032 | planned | — | Core Team critique inside design conversation | 011, 034, 091 | Add advisory persona critiques to the approved Jarvis sidecar flow without pretending independent agents or bypassing validation and promotion gates. |
| 033 | planned | — | Human-gated reusable part-kind proposal | 011, 012, 031, 056 | Promote exploration into reusable typed builders only through explicit human code promotion, protected property/conformance tests, parameter-schema review, and golden fixtures; no autonomous trusted-vocabulary mutation. |
| 034 | planned | — | Persona policy and capability metadata | 060, 068 | Superseded in part by Hermes personas/subagents. Retain only versioned JarvisOS policy metadata, capability labels, context profiles, and advisory/authority constraints; no independent memory, permissions, route ownership, or promotion. |
| 035 | merged | [#261](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/261) | Domain Foundation navigator | 040, 050, 051, 083, 087, 088 | Re-derive as ENGINEERING-DATA-1: searchable engineering-record navigation integrated with the shell, lineage/freshness overview, and run surfaces rather than a flat database list. |
| 036 | planned | — | Honest orchestrator status and authority UI | 029, 034, 060, 068, 083, 091 | Retain only thin JarvisOS UI contracts needed to show advisory identity, route and policy state, proposal status, and human authority; no claim that personas or Hermes are independent authorities. |
| 037 | cancelled | — | Chat entry point to BLUECAD workbench | 010, 042 | Cancelled as a standalone chat surface. Its valid candidate-drafting on-ramp is absorbed by 090 and 091 inside the single application shell. |
| 038 | merged | [#65](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/65) | SIM-WIRE | 044 | Wire the existing mesh and static-FEM adapters into the BLUECAD attempt loop as an opt-in advisory stage with evidence records and no auto-promotion. |
| 039 | planned | — | FRONTIER-1 provider route | 015, 018, 059b | Add the frontier provider adapter/route only behind the same server-owned egress, projected-budget, sensitivity, sanitization, provenance, trigger, and audit boundaries as every other external call. |
| 040 | merged | [#38](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/38) | MEMORYSTORE-0 | — | Add the single proposal/promotion boundary for AI- and calculation-originated engineering records with provenance and additive migration support. |
| 041 | merged | [#50](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/50) | DECISION-CAPTURE-0 | 040 | Parse bounded `jarvis-records` blocks from approved AI task responses and create proposed records through MemoryStore without extra model calls. |
| 042 | merged | [#56](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/56) | CONTEXT-PACK-1 | 040 | Add deterministic, budgeted, inspectable record selection with FTS/LIKE fallback and a side-effect-free preview endpoint. |
| 043 | merged | [#52](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/52) | CALC-1 | 016, 040 | Add a narrow `calc_v0` runner contract with AST policy, unit-bearing JSON outputs, deterministic artifacts, and parameter proposals. |
| 044 | merged | [#62](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/62) | EVIDENCE-BRIDGE-1 | 042 | Add typed validation/mesh/FEM evidence records and deterministic bounded evidence lines for context packs. |
| 045 | cancelled | — | Runner hardening boundary | 043 | Retired as a standalone isolation program for the current single-user loopback product. The bounded bundled-only cleanup is unnumbered. Reopen only for non-loopback access, a second user, remote-agent/Hermes/MCP runner reachability, or demonstrated non-bundled execution need. |
| 046 | planned | — | Alternative design loop | 006b, 011, 038 | Trigger only after the review panel proves useful: explain a failed FEM result, propose a bounded alternative, build it, and compare variants without auto-promotion. |
| 047 | merged | [#143](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/143) | BLUEREV-PROCESS-0: geometry, hydraulics, and pumping | 043 | Ship the caller-parameterized forward `calc_v0` model for geometry, hydraulics, residence/turnover, and pumping; formulas, units, correlations, and validity domains are versioned, while all nine project/operating values remain editable bindings and numerical fixtures validate equations only. |
| 048 | merged | [#150](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/150) | BLUEREV-PROCESS-1: biomass, nutrients, gas, harvest, and energy/cost KPIs | 043, 047 | Port ranks 8–18 while correcting productive-volume, recovery-balance, and pump-only-vs-total KPI errors; include a `preliminary_economic_evaluation_v0` output family (`variable_opex_rate`, `specific_variable_cost`, `gross_margin_proxy`) with explicit `economic_boundary` and `economic_basis` fields and per-input uncertainty/provenance, so design alternatives are economically comparable without implying a full TEA; `gross_margin_proxy` must support an explicit `not_computable` outcome when price, recovery, or time basis is unavailable rather than silently substituting zero or emitting a partial value; every claim carries units, assumptions, provenance, and verification cases. |
| 049 | merged | [#153](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/153) | BLUEREV-PROCESS-2: buoyancy and light/transmittance proxies | 043, 047 | Add hardware mass and safety factor to buoyancy; require explicit optical path length; label proxies honestly and expose the measurements that would promote real light models. |
| 050 | merged | [#156](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/156) | FLOWSHEET-1 dependency DAG | 047, 048, 049 | Materialize an inspectable graph from existing provenance without a recompute engine; normalize legacy FK/source forms at read time and own the shared `<kind>:<id>` resolver. |
| 051 | merged | [#159](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/159) | FLOWSHEET-RECALC stale propagation | 050 | When an accepted input changes, deterministically mark dependent outputs stale and explain the dependency path; no automatic recomputation or silent promotion. |
| 052 | merged | [#170](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/170) | CAD-LINK-0: 047 M0 cylinder proxy to BLUECAD | 005, 038, 050, 051, 071 | Convert one fresh successful bundled-047 run with accepted parameter-backed geometry inputs into an idempotent one-`tube_run` BLUECAD candidate, reconcile CAD geometry against 047 volume/area outputs, and return dependency/evidence lineage; full-reactor topology and tube-count semantics remain deferred. |
| 053 | planned | — | Decision packet and dossier export | 041, 044, 048 | Export recommendations, alternatives, evidence, assumptions, uncertainty, and provenance as a readable decision-to-evidence dossier for thesis, advisor, investor, or later IP/grant workflows. |
| 054 | planned | — | Proposal-review UI | 040, 041, 083, 035, 087 | Re-derive as PROPOSAL-REVIEW-1 over the application shell, engineering-data navigation, and lineage overview; preserve explicit promote/reject authority and do not implement the blocked 062 grade surface. |
| 055 | planned | — | Project view: Mark-1 as one navigable object | 035, 044, 050, 092 | Assemble decisions, calculations, CAD, evidence, and lineage for one workspace without a second store; semantic 3D identity requires the verified 092 binding contract and stores no engineering truth in the view. |
| 056 | merged | [#88](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/88) | BLUECAD property-based geometry testing + determinism canary | 005 | Valid-domain property coverage, same-environment repeatability, and the canonical Linux full-manifest digest canary are merged. |
| 057 | cancelled | — | SPEC-LEDGER-0 | — | Cancelled after [planning PR #64](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/64): a generated ledger script and parallel handoff file are unnecessary while this canonical registry is sufficient. |
| 058 | cancelled | — | Unified workspace home layout | — | Cancelled as a monolithic implementation slice. Its product objective is redistributed across 070 UI foundation, 083 application shell, 091 Jarvis sidecar, and 029 Settings. |
| 058b | planned | — | Workbench UX pass 2: variant comparison and design history | 006b, 083, 085, 089 | Re-derive as VARIANT-COMPARISON-1 after deterministic variants, the application shell, the migrated BLUECAD workbench, and unit-aware analytics exist. |
| 058c | planned | — | Report-to-3D linking | 044, 085, 092 | Re-derive as SCENE-SEMANTICS-A1 only after the migrated BLUECAD workbench and verified scene-binding manifest exist; no mesh-index or exporter-order identity. |
| 059 | planned | — | IP-EGRESS-1 umbrella definition | 003, 015, 018, 021, 040, 042 | Definition amended through PR #95 and reconciled with ADR-059 for external policy autopilot, automatic sanitization, sampled audit, and explicit maintainer residual-risk acceptance; this row remains definition-only. |
| 059a | merged | [#90](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/90) | IP-EGRESS-1A: sensitivity and context foundation | 003, 015, 018, 021, 040, 042 | Digest-bound labels/derivatives, deterministic floors, stale handling, coherent read-snapshot selection, and S0/S1-only external preview merged in #90. |
| 059b | merged | [#119](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/119) | IP-EGRESS-1B: policy autopilot and execution enforcement | 059a | Prompt/manual-context authority, automatic sanitizer provenance, exact per-binding packets and decisions, ticket-ID confirmation, atomic projected-budget reservation, sampled audit, fallback enforcement, and usage-source-bound accounting are merged. |
| 060 | planned | — | AGENT-ORCH: Hermes integration umbrella | 040, 042, 059b | Definition-only umbrella for adopting pinned Hermes through standards-only boundaries; implementation is owned by slices 066–068, while JarvisOS retains state, policy, sensitivity, budget, egress, ledger, services, and promotion authority. |
| 061 | planned | — | TOKEN-FLOW-0 umbrella definition | 021, 059b | Definition-only umbrella for complete flow economics and bounded completion; implementation is owned by 061a core and 061b continuation slices. |
| 061a | merged | [#134](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/134) | TOKEN-FLOW-CORE-0 | 021, 059b | Correlate no-execution, synthetic, local-compute, and external-provider attempts in one canonical flow; separate adapter invocation from external dispatch, preserve 059b accounting authority, aggregate only external provider spend in USD, and expose local compute as unpriced. Continuation execution remains deferred to 061b. |
| 061b | merged | [#145](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/145) | TOKEN-FLOW-CONTINUATION-0 | 061a | Add exact-length continuation, protected accumulated segments, restart-safe 059b confirmation resume, assembled-output digests, single final record capture, and safe continuation status after 061a is merged. |
| 062 | blocked | — | GRADE-0 | 021, 059b, 061a, 061b | Backend PRs #166 and #167 are merged. The four-choice operator surface remains blocked pending joint operator design after Phase 4; no autonomous frontend implementation is authorized. That non-implementation session may remain pending while Phase 5 proceeds, but no Phase-5 slice may touch grade placement, state, revision, withdrawal, accessibility, or stale-subject conflicts. |
| 063 | planned | — | CAPTURE-VAULT-0 | 040, 042 | Add a local markdown vault and rebuildable local vector working layer, merged with canonical SQLite retrieval under explicit authority/conflict tags; no vectors over canonical records. |
| 064 | planned | — | LIT-RAG-0 | 042, 063 | Add corpus-tagged public-literature retrieval to the local working layer with source locators and canonical-over-literature authority; boundary consolidation remains a separately unnumbered planning gap. |
| 065 | planned | — | Provider-family diversification policy hook | 059b | After policy autopilot is proven, add a configurable hook that may separate families of S2/S3-derived content across provider accounts without weakening exact-packet, budget, sensitivity, or audit gates. |
| 066 | planned | — | HERMES-PASSTHROUGH-0 | 015, 018, 021, 059b, 061a, 061b, 062 | Frozen by maintainer decision on 2026-07-29 and not reopened by 081. The prior definition branch is retained; restart requires explicit maintainer approval and fresh re-derivation from current `master`. |
| 067 | planned | — | JARVIS-MCP-0 | 005, 010, 040, 042, 043, 044, 059a | Frozen by maintainer decision on 2026-07-29 and not reopened by 081. The prior definition branch is retained; restart requires explicit maintainer approval and fresh re-derivation from current `master`. |
| 068 | planned | — | HERMES-CONFIG-0 | 066, 067 | Frozen by maintainer decision on 2026-07-29 and not reopened by 081. The prior definition branch is retained; restart requires explicit maintainer approval and fresh re-derivation from current `master`. |
| 069 | planned | — | MEMORY-CONSOLIDATE-0 | 040, 042, 061a, 061b, 062, 066, 067, 068 | First Hermes dogfood: consolidate bounded accepted records/evidence into MemoryStore proposals with conflict preservation, provenance, grading, and cost evidence; never promote, overwrite, delete, or lower sensitivity. |
| 070 | merged | [#225](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/225) | UI-FOUNDATION-1 | 006, 082, 094 | Ready under [the 2026-08-04 readiness decision](070-readiness-2026-08-04.md) for one bounded implementation of semantic tokens, system/light/dark appearance, five shared primitives, limited migration, accessibility evidence, and the dependency-free UI foundation checker; no 083 shell work. |
| 071 | merged | [#147](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/147) | MODEL-SCENARIO-DOF-0: editable bindings, scenario runs, and degree-of-freedom inspection | 040, 043, 047 | Expose immutable value-free model input contracts, side-effect-free forward binding/DOF preview, parameter-backed or manual scenario bindings, existing-runner execution, and one bounded Domain Foundation panel; no inverse solver, targets, optimizer, automatic promotion, or embedded design defaults. |
| 072 | merged | [#172](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/172) | BLUEREV-PROCESS-3: explicit symmetric hydraulic topology M1 | 043, 047, 050, 051, 052, 071 | Preserve the validated deterministic parallel M1 topology as an inspectable experiment and alternative architecture. It is not the canonical BlueRev v1 serial Smart-Joint/tube topology and receives no new work in the frontend-beta queue. |
| 073 | merged | [#174](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/174) | BLUECAD-PRIMITIVE-1: fluid-open capped branch manifold | 005, 005b, 056 | Add one deterministic capped branch-header primitive with exactly one common port and 1–12 branch ports, explicit branch bores through the header wall, closed-end geometry, kernel-volume reconciliation, and property/conformance tests; no process link, layout solver, project defaults, or UI. |
| 074 | merged | [#183](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/183) | CAD-LINK-1: 072 M1 topology to deterministic multi-part BLUECAD | 038, 050, 051, 052, 071, 072, 073 | Preserve the deterministic multi-part CAD link for the 072 parallel-topology experiment. It remains inspectable and supported but is not the canonical BlueRev v1 default. |
| 075 | merged | [#191](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/191) | PROCESS-KERNEL-1: streams, components, units, and unit operations | 043, 047, 048, 071 | Re-express validated 047 as an acyclic flowsheet of typed material/scalar ports and reusable blocks, add additive unit-contract v2 and component/stream foundations, and require exact canonical 047 result identity before broader solver work. Readiness evidence and implementation ownership are frozen in [the 2026-07-27 readiness decision](075-readiness-2026-07-27.md). |
| 076 | merged | [#195](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/195) | EVIDENCE-SIGHT-0: bounded evidence-guided structural repair | 010, 038, 044, 059b, 061a, 061b | Add an opt-in, separately budgeted structural-repair cycle using deterministic attempt-scoped evidence; preserve valid candidate state and artifact pointers on every unsuccessful path; no new states, migration, promotion, or egress authority. |
| 077 | merged | [#198](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/198) | EVIDENCE-EGRESS-0: canonical evidence provenance and classification | 044, 059a, 059b, 076 | Bind canonical evidence rows and rendered evidence derivatives to workspace-scoped provenance, sensitivity, staleness, and exact-packet lineage before external model use; reuse 059a/059b authority and add no alternate egress path. Readiness sequencing, prompt authority, and no-migration packet lineage are frozen in [the 2026-07-28 readiness decision](077-readiness-2026-07-28.md). |
| 078 | planned | — | PBR-MODELING-0: bounded photobioreactor modeling kernel | 043, 047, 048, 049, 071, 075 | The planning kernel and complete documentation-only full specification with verified scientific-evidence companions are merged through PR #211. 078 remains `planned` with no readiness decision, implementation PR, migration, dependency, or runtime authorization. |
| 079 | merged | [#210](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/210) | AUTONOMOUS-DEVELOPMENT-LOOP-0: minimal scheduled continuation | 022 | Merged through PR #210. Resume exactly one existing in-review implementation PR once daily by reading the registry from exact PR heads, reusing Claude Code Action in OFF/SHADOW/EXECUTE_NO_MERGE modes, validating an untrusted patch with deterministic gates, and permitting only a non-forced same-branch push; no merge or review/repair authority. |
| 080 | planned | — | AUTONOMOUS-REVIEW-REPAIR-0 | 004, 017, 019, 022, 079 | Frozen for the duration of the frontend-beta queue. It remains separate from 079 and receives no implementation authority until a later explicit queue reopens it. |
| 081 | planned | — | FRONTEND-BETA-AUTHORITY-0 | — | Definition-only umbrella derived from `master` at `2183b2282d239ed570c59d0982e227e54c62dad7`; freezes product direction, queue, phase evidence, transition continuity, and re-derivation rules. It must never receive an implementation PR. |
| 082 | merged | [#216](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/216), [#217](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/217) | SECURE-CREDENTIAL-STORAGE-0 | 015, 018, 021, 059b, 061a | Current-user Windows DPAPI persistence and its post-merge repair are merged. The operator checkpoint on exact `master` `e5c939c3ab62d4904c65aa0ebdec8dbb496f7369` proved post-restart `secure_persisted / usable` state without environment re-entry, one confirmed no-fallback `external:scaleway` normal-spine call returning `OK`, settings restoration, and `LEAK_NOT_FOUND` across responses, logs, events, SQLite, the data root, repository and worktree. Evidence is recorded in [the 2026-08-04 Windows checkpoint](082-094-windows-checkpoint-2026-08-04.md). |
| 094 | merged | [#221](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/221) | SCALEWAY-NORMAL-SPINE-0 | 015, 018, 021, 059b, 061a, 061b | Authorize one dedicated no-fallback Scaleway route and convert existing live smoke surfaces into wrappers over the normal `run_ai_task`/059b execution, reservation and ledger spine; no second ledger, schema, frontend or credential-persistence change. |
| 083 | merged | [#231](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/231) | APP-SHELL-1 | 006, 070 | PR #231 merged the identity-independent shell under [the 2026-08-05 readiness decision](083-readiness-2026-08-05.md) and [the complete APP-SHELL-1 specification](083-app-shell-1.md), including the bounded [UI-foundation checker reconciliation](083-ui-foundation-checker-amendment-2026-08-05.md) and [production SPA fallback](083-spa-fallback-amendment-2026-08-05.md); Penpot visual identity remains separate and independently removable. |
| 084 | merged | [#236](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/236) | BLUECAD-READ-MODEL-1 | 006, 044, 050, 051, 083 | Ready for one bounded identity-independent implementation under [the 2026-08-06 readiness decision](084-readiness-2026-08-06.md) and [the complete specification](084-bluecad-read-model-1.md): add one coherent candidate aggregate read surface without schema, cache, UI migration, workflow, provider or Penpot changes. |
| 085 | merged | [#239](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/239) | BLUECAD-WORKBENCH-2 | 006, 006c, 083, 084 | PR #239 merged the complete working BLUECAD lifecycle into the shell while preserving real GLB rendering, lifecycle actions, aggregate authority, validation/evidence semantics, accessibility, and the visual-identity boundary under [the 2026-08-13 readiness decision](085-readiness-2026-08-13.md). |
| 086 | merged | [#244](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/244) | MODEL-INSPECTION-A0 | 006, 085 | Add geometry-only viewer inspection and lifecycle hardening; all hits are session-scoped and carry no semantic record or scene-component identity. |
| 087 | merged | [#250](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/250) | LINEAGE-OVERVIEW-1 | 050, 051, 083 | Add an early read-only dependency, provenance and freshness overview with a compact inspector; no recomputation, mutation, or requirement for the full Engineering Data area. |
| 088 | merged | [#256](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/256) | RUNS-WORKBENCH-1 | 043, 071, 083 | PR #256 merged the bounded read-first run list/detail workbench over persisted run, binding/result, log and artifact authority under [the 2026-08-15 readiness decision](088-readiness-2026-08-15.md); no runner mutation, polling, analytics, backend expansion or global visual identity. |
| 089 | ready | — | ANALYTICS-DOCK-1 | 035, 083, 087, 088 | Add closed-by-default, real-data analytics with declared units and comparability contracts; reject incompatible comparisons instead of normalizing them silently. |
| 090 | planned | — | AI-THREADS-0 | 040, 041, 042, 059b, 061a, 061b, 083 | Add local episodic thread persistence and thread-to-attempt provenance while preserving distinct provider/fallback, token-flow, BLUECAD workflow, proposal, cost and latency evidence. Raw complete-thread external egress remains forbidden. |
| 091 | planned | — | JARVIS-SIDECAR-1 | 042, 059b, 061a, 061b, 083, 090 | Add contextual Jarvis interaction and advisory role profiles inside the shared sidecar, reusing the existing execution, context, proposal, budget and egress boundaries; no Hermes runtime or fake autonomous presence. |
| 092 | planned | — | SCENE-BINDING-0 | 005, 006, 056, 085 | Add a verified backend GLB/component binding manifest with deterministic component IDs, artifact and manifest digests, stable node resolution, tamper rejection and parsed-binary tests. |
| 093 | planned | — | BLUEREV-SERIAL-TOPOLOGY-0 | 043, 047, 048, 049, 050, 051, 071, 075 | Future implementation authority for the canonical serial Smart-Joint/tubular-section BlueRev topology and side-stream harvest arrangement. It is outside the frontend-beta binding queue. |
## Superseded planning aliases and resolved collisions

- Historical `045 = AGENT-ORCH` references are superseded by `060`; `045` is
  cancelled as a standalone isolation program and may be reopened only by its
  explicit product-reachability or non-bundled-execution triggers.
- Historical `057 = Workspace home`, `057b`, and `057c` references remain
  superseded and must not be reused. Monolithic 058 is now cancelled; its product
  objective is redistributed across 070, 083, 091, and 029, while 058b and 058c
  retain their own re-derived Phase-6 scopes.
- Specs 030 and 037 are cancelled as standalone conversation surfaces; their valid
  proposal and BLUECAD on-ramp responsibilities are absorbed by 090 and 091.
- Specs 031, 034, and 036 retain only bounded JarvisOS-side vocabulary, persona-policy,
  and authority-display contracts. They do not authorize a second conversation or
  orchestration engine and do not reopen frozen 066–068.
- IDs 081–094 are reserved by FRONTEND-BETA-AUTHORITY-0 and its authorized 094 re-derivation as recorded in the registry;
  all references use the canonical three-digit form required by the registry gate.

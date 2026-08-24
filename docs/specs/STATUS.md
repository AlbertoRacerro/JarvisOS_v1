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

The frontend-beta direction and binding delivery queue are defined by spec 081 and, after merged
029, re-derived for the remaining operator-workstation front by definition-only spec 095.

The queue remains sequential and every implementation slice must still pass the normal
backlog row → kernel or definition → full spec → readiness → implementation → exact-head
gates → review → merge → registry-reconciliation lifecycle. A `planned` row is not
implementation authority.

**Emergency security interrupt — resolved 2026-08-19:** 099 REVIEW-SECRET-BOUNDARY-0
merged through PR #306 and is registry-reconciled. PR #303 completed the resumed 092
implementation under the existing definition/readiness and merged on 2026-08-20. The interrupt
did not re-derive 092 or any product architecture.

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
14. 090 AI-THREADS-0;
15. 091 JARVIS-SIDECAR-1;
16. 029 SETTINGS-1, freshly re-derived;
17. 095 OPERATOR-WORKSTATION-AUTHORITY-1 definition and queue re-derivation;
18. 096 OPERATOR-WORKBENCH-CORRECTION-0;
19. 071b ENGINEERING-PROPERTIES-1;
20. 092 SCENE-BINDING-0, freshly re-derived;
21. 058c SCENE-SEMANTICS-A1, freshly re-derived;
22. 097 JARVIS-ENGINEERING-ACTIONS-0;
23. 098 ENGINEERING-RECORD-LIFECYCLE-0;
24. 006b PARAMETRIC-VARIANTS-1, freshly re-derived;
25. 058b VARIANT-COMPARISON-1, freshly re-derived;
26. 100 VISUAL-IDENTITY-1;
27. 100a CODEBASE-LEAN-AUDIT-1;
28. 100b CODEBASE-LEAN-CLEANUP-1;
29. 101 CANONICAL-STATE-WRITE-1;
30. 102 ENGINEERING-EVIDENCE-CONTRACT-1;
31. 103 PROCESS-UPSTREAM-BAKEOFF-1;
32. 104 PROCESS-STACK-STRANGLER-1;
33. 105 ENGINEERING-DOMAIN-CLEANUP-1;
34. 106 ENGINEERING-EVALUATOR-1;
35. 107 PBR-EVALUATOR-1;
36. 108 DESIGN-STUDY-CONTROLLER-1;
37. 109 PROCESS-CAD-HANDOFF-1;
38. 110 MULTIFIDELITY-ENGINEERING-1.

Items 26–38 are the maintainer-approved post-functional-beta extension registered on
2026-08-21 and amended on 2026-08-22 after the public/canonical architecture and codebase-maintainability reviews. They remain `planned`
until the normal definition/full-spec/readiness lifecycle authorizes each slice. Their order
encodes the zero-sunk-cost rule: finish visual identity, audit and simplify the active semantic surface without deleting desired-but-unwired capability, fix authority/evidence semantics, evaluate upstreams from
scratch, retire duplicated generic infrastructure, then build PBR/design-study capability on
the selected boundaries.

The maintainer completed the 062 frontend design decision on 2026-08-17: no permanent
`Was this useful?` grading control belongs in normal Jarvis chat. Existing 062 backend/evaluation
evidence remains valid; a future frontend grade surface is deferred to a separately re-derived
Evaluation/Audit interaction and does not block the operator-workstation queue.

Specs 066, 067, 068, and 080 remain frozen for the duration of the current functional queue and
are not reopened by the architecture reconciliation. Spec 078 is cancelled as a standalone
implementation identity; its merged planning/scientific evidence remains historical/incumbent
reference for the zero-sunk-cost bake-off and future PBR work. Spec 107 is the sole future
integrated PBR evaluator implementation authority after 103/106. Spec 093 and any Aspen-like
editable flowsheet remain outside the current functional queue. Global visual identity is now
registered as 100: it remains independently removable from functional slices, but by maintainer
decision it is ordered after 058b and before the lean audit/cleanup and architecture-remediation runtime work.

The queue is binding but not immutable. If a slice proves non-implementable within its
accepted boundary, or a prerequisite proves insufficient, the active front stops and a later
definition-only authority spec may re-derive the remaining queue. Re-derivation must preserve
already merged slices, record the stop reason and reached state, retain the 066–068 freeze
until explicitly lifted, and explicitly identify any product decision from spec 081 or 095 that
it changes. Silent abandonment or substitution is not authorized.

## Current priority and drafting order

1. 006b PARAMETRIC-VARIANTS-1 implementation is in review under draft PR #348 after merged definition PR #345, readiness PR #346 and reconciliation PR #347. Keep #348 draft while its head is mobile; complete the bounded frontend-only previous-successful-run load into the single 071b owner, deterministic/browser gates and exact-head independent review before merge. 058b remains unauthorized until 006b implementation merges and is reconciled.
2. 099 REVIEW-SECRET-BOUNDARY-0 is merged through PR #306 and reconciled; the emergency security interrupt is closed.
3. Preserve merged 059a/059b, 061a/061b, 075, 076, 077, 079, 082, 094, 070, 083, 084, 085, 086, 087, 088, 035, 089, 054, 090, 091, 029, 096, 071b, 092, 058c, 097, and 098 authority boundaries; definition-only 095 remains non-implementation authority.
4. Preserve the merged documentation/evidence from 047–049, 072, 075 and cancelled 078 as incumbent/reference evidence with zero sunk-cost privilege during 103; 107 is the sole future integrated PBR evaluator implementation authority after 103/106.
5. Keep 066–068 and 080 frozen; keep 062 itself blocked/deferred while allowing the operator-workstation queue to proceed without routine grading UI.
6. After 058b, execute 100 visual identity, then 100a audit and a freshly re-derived 100b disposition before any 101–110 runtime work. If 100a proves no worthwhile generic cleanup outside later owned slices, 100b records and merges `NO_ACTION` without runtime churn; otherwise it executes one bounded `CLEANUP` batch. Then follow 101→110.

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
| 006b | in_review | [#348](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/348) | BLUECAD parametric variants | 006, 071b, 083, 085, 092, 058c | Re-derived as PARAMETRIC-VARIANTS-1 under definition PR #345 and [the 2026-08-24 readiness decision](006b-readiness-2026-08-24.md) under PR #346. Draft implementation PR #348 owns the frontend-only V0 that loads an exact compatible successful run into the single 071b working owner as a `Previous successful run` baseline, with exact model-version/contract/unit checks, explicit dirty replacement, stale-safe apply and zero canonical/run/provider side effects on load; no backend variant store or 058b comparison. |
| 006c | merged | [#30](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/30) | BLUECAD workbench UX pass | 006 | Add archive, malformed-detail inspection, promotion, retry/duplicate-brief flows, and safer validation rendering. |
| 007 | merged | [#17](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/17) | BLUECAD tool registry | 005 | Add fail-closed tool registration, health/hash checks, subprocess execution boundaries, and CI license-boundary enforcement. |
| 008 | merged | [#32](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/32) | BLUECAD Gmsh mesh adapter | 005, 007 | Generate deterministic Gmsh inputs and physical groups, invoke Gmsh through the registry, and return structured mesh-quality outcomes. |
| 009 | merged | [#35](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/35) | BLUECAD CalculiX FEM adapter | 008 | Assemble deterministic static CalculiX decks, run the registered solver, parse result summaries, and evaluate Tier 3 criteria. |
| 010 | merged | [#20](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/20), [#26](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/26), [#28](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/28) | BLUECAD AI loop v0 | 005 | Add the bounded candidate/attempt loop, safe-default parking, prompt/schema flow, validation, repair attempts, and traceable prompt versions. |
| 011 | planned | — | Core Team review panel | 034 | Add advisory persona reviews over artifacts and evidence; personas are bounded configurations, not autonomous authorities or a fake swarm. |
| 012 | planned | — | L2 ephemeral free-script proposals | 010, 016 | Trigger-gated only: reopen after non-loopback access, a second user, remote-agent/Hermes/MCP runner reachability, or a demonstrated need for non-bundled execution, and only behind a separate proven OS-isolation specification. |
| 013 | planned | — | Tier 2 domain-validator plugin interface | 005, 010 | Define a narrow plugin boundary for BlueRev-specific engineering checks that emit deterministic validation evidence without letting plugins own routing, memory, or promotion. |
| 014 | planned | — | OpenFOAM CFD case-bundle adapter v0 | 007, 008, 049 | Produce inspectable OpenFOAM case bundles and evidence only when process/light proxies leave a concrete decision unresolved; no generic CFD platform or automatic solver authority. |
| 015 | merged | [#33](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/33) | PROVIDER-GW-1 | 003 | Replace hardcoded bindings with a validated provider registry and generic OpenAI-compatible adapter while preserving safe defaults. |
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
| 029 | merged | [#286](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/286) | Settings and secrets operator page | 015, 018, 061a, 082, 083, 090 | SETTINGS-1 merged under [the 2026-08-17 readiness decision](029-readiness-2026-08-17.md); expose provider, budget, usage, storage and diagnostic state without placing keys in localStorage, logs, repository files, or normal frontend state. |
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
| 054 | merged | [#271](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/271) | Proposal-review UI | 040, 041, 083, 035, 087 | Re-derive as PROPOSAL-REVIEW-1 over the application shell, engineering-data navigation, and lineage overview; preserve explicit promote/reject authority and do not implement the blocked 062 grade surface. |
| 055 | planned | — | Project view: Mark-1 as one navigable object | 035, 044, 050, 092 | Assemble decisions, calculations, CAD, evidence, and lineage for one workspace without a second store; semantic 3D identity requires the verified 092 binding contract and stores no engineering truth in the view. |
| 056 | merged | [#88](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/88) | BLUECAD property-based geometry testing + determinism canary | 005 | Valid-domain property coverage, same-environment repeatability, and the canonical Linux full-manifest digest canary are merged. |
| 057 | cancelled | — | SPEC-LEDGER-0 | — | Cancelled after [planning PR #64](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/64): a generated ledger script and parallel handoff file are unnecessary while this canonical registry is sufficient. |
| 058 | cancelled | — | Unified workspace home layout | — | Cancelled as a monolithic implementation slice. Its product objective is redistributed across 070 UI foundation, 083 application shell, 091 Jarvis sidecar, and 029 Settings. |
| 058b | planned | — | Workbench UX pass 2: variant comparison and design history | 006b, 071b, 083, 085, 089 | Re-derive as VARIANT-COMPARISON-1 after 095: compare effective engineering values/model choices/results with declared units and warnings, not raw JSON/UUID history. |
| 058c | merged | [#319](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/319) | Report-to-3D linking | 044, 071b, 085, 092 | SCENE-SEMANTICS-A1 definition PR #314, model-choice amendment PR #316, fresh readiness PR #317, and implementation PR #319 are merged. The bounded schema-v3 semantic companion, guarded linked-Parameter freshness, candidate semantic-source projection, selected-object Properties composition, stable target transitions, and exact source navigation are now runtime authority; later queue items remain separate. |
| 059 | planned | — | IP-EGRESS-1 umbrella definition | 003, 015, 018, 021, 040, 042 | Definition amended through PR #95 and reconciled with ADR-059 for external policy autopilot, automatic sanitization, sampled audit, and explicit maintainer residual-risk acceptance; this row remains definition-only. |
| 059a | merged | [#90](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/90) | IP-EGRESS-1A: sensitivity and context foundation | 003, 015, 018, 021, 040, 042 | Digest-bound labels/derivatives, deterministic floors, stale handling, coherent read-snapshot selection, and S0/S1-only external preview merged in #90. |
| 059b | merged | [#119](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/119) | IP-EGRESS-1B: policy autopilot and execution enforcement | 059a | Prompt/manual-context authority, automatic sanitizer provenance, exact per-binding packets and decisions, ticket-ID confirmation, atomic projected-budget reservation, sampled audit, fallback enforcement, and usage-source-bound accounting are merged. |
| 060 | planned | — | AGENT-ORCH: Hermes integration umbrella | 040, 042, 059b | Definition-only umbrella for adopting pinned Hermes through standards-only boundaries; implementation is owned by slices 066–068, while JarvisOS retains state, policy, sensitivity, budget, egress, ledger, services, and promotion authority. |
| 061 | planned | — | TOKEN-FLOW-0 umbrella definition | 021, 059b | Definition-only umbrella for complete flow economics and bounded completion; implementation is owned by 061a core and 061b continuation slices. |
| 061a | merged | [#134](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/134) | TOKEN-FLOW-CORE-0 | 021, 059b | Correlate no-execution, synthetic, local-compute, and external-provider attempts in one canonical flow; separate adapter invocation from external dispatch, preserve 059b accounting authority, aggregate only external provider spend in USD, and expose local compute as unpriced. Continuation execution remains deferred to 061b. |
| 061b | merged | [#145](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/145) | TOKEN-FLOW-CONTINUATION-0 | 061a | Add exact-length continuation, protected accumulated segments, restart-safe 059b confirmation resume, assembled-output digests, single final record capture, and safe continuation status after 061a is merged. |
| 062 | blocked | — | GRADE-0 | 021, 059b, 061a, 061b | Backend PRs #166 and #167 remain merged evidence. Maintainer design on 2026-08-17 rejected permanent per-response grading in normal Jarvis chat; any future frontend grade interaction must be separately re-derived as secondary Evaluation/Audit UI and does not block the operator-workstation queue. |
| 063 | planned | — | CAPTURE-VAULT-0 | 040, 042 | Add a local markdown vault and rebuildable local vector working layer, merged with canonical SQLite retrieval under explicit authority/conflict tags; no vectors over canonical records. |
| 064 | planned | — | LIT-RAG-0 | 042, 063 | Add corpus-tagged public-literature retrieval to the local working layer with source locators and canonical-over-literature authority; boundary consolidation remains a separately unnumbered planning gap. |
| 065 | planned | — | Provider-family diversification policy hook | 059b | After policy autopilot is proven, add a configurable hook that may separate families of S2/S3-derived content across provider accounts without weakening exact-packet, budget, sensitivity, or audit gates. |
| 066 | planned | — | HERMES-PASSTHROUGH-0 | 015, 018, 021, 059b, 061a, 061b, 062 | Frozen by maintainer decision on 2026-07-29 and not reopened by 081, 095 or the 2026-08-21 architecture reconciliation. Restart requires explicit maintainer approval and fresh re-derivation from then-current `master`. |
| 067 | planned | — | JARVIS-MCP-0 | 005, 010, 040, 042, 043, 044, 059a | Frozen by maintainer decision on 2026-07-29 and not reopened by 081, 095 or the 2026-08-21 architecture reconciliation. Restart requires explicit maintainer approval and fresh re-derivation from then-current `master`. |
| 068 | planned | — | HERMES-CONFIG-0 | 066, 067 | Frozen by maintainer decision on 2026-07-29 and not reopened by 081, 095 or the 2026-08-21 architecture reconciliation. Restart requires explicit maintainer approval and fresh re-derivation from then-current `master`. |
| 069 | planned | — | MEMORY-CONSOLIDATE-0 | 040, 042, 061a, 061b, 062, 066, 067, 068 | First Hermes dogfood: consolidate bounded accepted records/evidence into MemoryStore proposals with conflict preservation, provenance, grading, and cost evidence; never promote, overwrite, delete, or lower sensitivity. |
| 070 | merged | [#225](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/225) | UI-FOUNDATION-1 | 006, 082, 094 | Ready under [the 2026-08-04 readiness decision](070-readiness-2026-08-04.md) for one bounded implementation of semantic tokens, system/light/dark appearance, five shared primitives, limited migration, accessibility evidence, and the dependency-free UI foundation checker; no 083 shell work. |
| 071 | merged | [#147](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/147) | MODEL-SCENARIO-DOF-0: editable bindings, scenario runs, and degree-of-freedom inspection | 040, 043, 047 | Preserve the merged immutable input-contract, side-effect-free binding/DOF preview and scenario-run authority. New operator-first Properties/working configuration work is additive under 071b; this historical implementation is not reopened. |
| 071b | merged | [#298](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/298) | ENGINEERING-PROPERTIES-1 | 071, 096 | Definition PR #295 and [the 2026-08-18 readiness decision](071b-readiness-2026-08-18.md) under PR #296 are merged. Authorize the bounded operator-first implementation of contract-driven Properties, transient working configuration, effective values/provenance, dirty/Undo/Revert state, deterministic preflight/run-start semantics, and the narrow server-owned run-create idempotency seam frozen by readiness; no second engineering store. |
| 072 | merged | [#172](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/172) | BLUEREV-PROCESS-3: explicit symmetric hydraulic topology M1 | 043, 047, 050, 051, 052, 071 | Preserve the validated deterministic parallel M1 topology as an inspectable experiment and incumbent/reference fixture. It is not the canonical BlueRev v1 default and receives zero sunk-cost privilege in the post-visual-identity process revalidation. |
| 073 | merged | [#174](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/174) | BLUECAD-PRIMITIVE-1: fluid-open capped branch manifold | 005, 005b, 056 | Add one deterministic capped branch-header primitive with exactly one common port and 1–12 branch ports, explicit branch bores through the header wall, closed-end geometry, kernel-volume reconciliation, and property/conformance tests; no process link, layout solver, project defaults, or UI. |
| 074 | merged | [#183](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/183) | CAD-LINK-1: 072 M1 topology to deterministic multi-part BLUECAD | 038, 050, 051, 052, 071, 072, 073 | Preserve the deterministic multi-part CAD link for the 072 parallel-topology experiment. It remains inspectable but is not process-design authority and may be adapted/retired after the future process-design handoff is re-derived. |
| 075 | merged | [#191](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/191) | PROCESS-KERNEL-1: streams, components, units, and unit operations | 043, 047, 048, 071 | Historical acyclic typed process-kernel experiment with exact 047 identity. No further generic solver expansion is authorized before 103; the kernel receives zero sunk-cost privilege and may be wrapped, reduced to fixtures/domain equations, or deleted by 104 after the upstream bake-off. |
| 076 | merged | [#195](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/195) | EVIDENCE-SIGHT-0: bounded evidence-guided structural repair | 010, 038, 044, 059b, 061a, 061b | Add an opt-in, separately budgeted structural-repair cycle using deterministic attempt-scoped evidence; preserve valid candidate state and artifact pointers on every unsuccessful path; no new states, migration, promotion, or egress authority. |
| 077 | merged | [#198](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/198) | EVIDENCE-EGRESS-0: canonical evidence provenance and classification | 044, 059a, 059b, 076 | Bind canonical evidence rows and rendered evidence derivatives to workspace-scoped provenance, sensitivity, staleness, and exact-packet lineage before external model use; reuse 059a/059b authority and add no alternate egress path. Readiness sequencing, prompt authority, and no-migration packet lineage are frozen in [the 2026-07-28 readiness decision](077-readiness-2026-07-28.md). |
| 078 | cancelled | — | PBR-MODELING-0: bounded photobioreactor modeling kernel | — | Cancelled/superseded as a standalone runtime implementation identity. Planning and scientific evidence through PR #211 remain historical/incumbent reference; 107 is the sole future integrated PBR evaluator implementation authority after 103/106. |
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
| 089 | merged | [#266](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/266) | ANALYTICS-DOCK-1 | 035, 083, 087, 088 | Add closed-by-default, real-data analytics with declared units and comparability contracts; reject incompatible comparisons instead of normalizing them silently. |
| 090 | merged | [#276](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/276) | AI-THREADS-0 | 040, 041, 042, 059b, 061a, 061b, 083 | Add local episodic thread persistence and thread-to-attempt provenance while preserving distinct provider/fallback, token-flow, BLUECAD workflow, proposal, cost and latency evidence. Raw complete-thread external egress remains forbidden. |
| 091 | merged | [#281](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/281) | JARVIS-SIDECAR-1 | 042, 059b, 061a, 061b, 083, 090 | Add contextual Jarvis interaction and advisory role profiles inside the shared sidecar, reusing the existing execution, context, proposal, budget and egress boundaries; no Hermes runtime or fake autonomous presence. |
| 092 | merged | [#303](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/303) | SCENE-BINDING-0 | 005, 006, 056, 071b, 085 | Definition PR #300, [the 2026-08-19 readiness decision](092-readiness-2026-08-19.md) under PR #301, and implementation PR #303 are merged. Stable scene hit → canonical `part_id` binding now uses exporter-owned semantic keys, current manifest/spec/GLB evidence, stale-safe fail-closed resolution, and bounded human Properties/Jarvis target context without adding downstream 058c model semantics or a second working-state owner. |
| 093 | planned | — | BLUEREV-SERIAL-TOPOLOGY-0 | 043, 047, 048, 049, 050, 051, 071, 103, 109 | Future serial Smart-Joint/tubular-section topology work must wait for the zero-sunk-cost process bake-off and typed process-design→CAD handoff; topology must not become detailed-CAD authority before process design is re-derived. |
| 095 | planned | — | OPERATOR-WORKSTATION-AUTHORITY-1 | — | Definition-only re-derivation authority under PR #288; freezes the Operate/Inspect/Audit hierarchy, Jarvis-over-Properties sidecar, engineering Properties/working-state/preflight/Jarvis-action semantics and ordered downstream queue. It must never receive an implementation PR. |
| 096 | merged | [#293](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/293) | OPERATOR-WORKBENCH-CORRECTION-0 | 054, 083, 088, 089, 091 | Definition PR #290 and readiness PR #291 are merged; runtime implementation PR #293 is merged with the bounded frontend-only sidecar/scroll/overflow and operator-first Runs/Review/Jarvis presentation correction using existing authority only, with no new engineering backend semantics. |
| 097 | merged | [#333](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/333) | JARVIS-ENGINEERING-ACTIONS-0 | 071b, 091, 058c | Definition PR #329, [the 2026-08-22 readiness decision](097-readiness-2026-08-22.md) under PR #331, and implementation PR #333 are merged. The bounded frontend-only deterministic engineering-action surface reuses the single 071b/058c working owner for typed atomic compare-and-apply, proven-basis-only safe fixes, complete operator-visible previews, stale target/source/revision protection, inert `Other`/assistant prose, and explicit preflight/Run separation without backend/thread/provider/history/action-store expansion. |
| 098 | merged | [#339](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/339) | ENGINEERING-RECORD-LIFECYCLE-0 | 035, 040, 050, 051, 071b | Definition PR #336, [the 2026-08-22 readiness decision](098-readiness-2026-08-22.md) under PR #337, and implementation PR #339 are merged. The Parameter-first V0 now has separate server-owned lifecycle state, exact CAS/audit/dependency fail-closed edits and transitions, lifecycle-current context/history projections, replacement-authority preservation, linked source revision plus unit-normalized value identity, and server-backed Engineering Data edit/lifecycle controls; other record kinds remain read-only. |
| 099 | merged | [#306](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/306) | REVIEW-SECRET-BOUNDARY-0 | 017, 019 | Emergency security implementation under [the 2026-08-19 readiness decision](099-readiness-2026-08-19.md) merged through PR #306: provider-secret Cheap/Senior jobs execute only trusted master code while reviewed PR content remains inert GitHub API data; the interrupt is closed; resumed 092/#303 subsequently completed and merged on 2026-08-20. |
| 100 | planned | — | VISUAL-IDENTITY-1 | 097, 098, 058b | Apply the independently removable global visual identity only after the functional operator-workstation queue completes; visual design must not redefine backend authority, engineering semantics or canonical data. |
| 100a | planned | — | CODEBASE-LEAN-AUDIT-1 | 100 | Audit the complete first-party codebase from exact post-100 master for minimum semantic surface, desired-but-unwired capabilities, dead/superseded residue, duplication, overengineering, upstream replacement candidates and measured performance hotspots; absence of a current consumer is never deletion authority. |
| 100b | planned | — | CODEBASE-LEAN-CLEANUP-1 | 100a | Freshly re-derive either one bounded high-confidence `CLEANUP` batch or an evidence-backed `NO_ACTION` disposition from 100a; preserve `WIRE`/`DEFER` capabilities, avoid pre-empting 101 or 103–105, and never invent runtime churn merely to satisfy the cleanup slot. |
| 101 | planned | — | CANONICAL-STATE-WRITE-1 | 040, 042, 071b, 098, 100b | Unify legacy modeling CRUD and MemoryStore/canonical record transitions behind one server-owned write-intent/lifecycle/audit boundary; separate Parameter record lifecycle from value/evidence quality and prevent proposed records from entering authoritative context by value-quality alone. |
| 102 | planned | — | ENGINEERING-EVIDENCE-CONTRACT-1 | 044, 077, 101 | Generalize evaluator/evidence metadata for producer/version, digests, units, fidelity, validity domain, qualification, known exclusions, uncertainty and typed outcomes while preserving current solver-specific evidence and egress lineage. |
| 103 | planned | — | PROCESS-UPSTREAM-BAKEOFF-1 | 047, 048, 049, 075, 100, 102 | Re-evaluate the custom process stack from zero against current upstreams such as IDAES/Pyomo/WaterTAP, BioSTEAM/QSDsan, CasADi/OpenMDAO, DWSIM/CAPE-OPEN and property libraries; produce explicit KEEP/WRAP/REPLACE/DELETE decisions with license, dynamics/recycle, optimization, diagnostics, Windows/local and qualification evidence. |
| 104 | planned | — | PROCESS-STACK-STRANGLER-1 | 103 | Execute the 103 decision: migrate only still-useful domain equations/tests/adapters, switch callers to selected upstream boundaries, and delete duplicated generic custom process-solver infrastructure rather than maintaining parallel engines for sunk-cost reasons. |
| 105 | planned | — | ENGINEERING-DOMAIN-CLEANUP-1 | 104 | Delete or deliberately rebuild the obsolete `app/modules/engineering` placeholder boundary and resolve the dependency/provenance `app/modules/flowsheet` naming collision with real process flowsheets, preserving compatibility only where demonstrably required. |
| 106 | planned | — | ENGINEERING-EVALUATOR-1 | 102, 105 | Define the minimum common typed EvaluationRequest/EvaluationResult boundary for replaceable process/CAD/CAE/CFD/commercial adapters, including failure taxonomy and qualification metadata without flattening solver-specific semantics. |
| 107 | planned | — | PBR-EVALUATOR-1 | 103, 106 | Freshly derive and implement the integrated photobioreactor evaluator on the selected process/dynamic upstream stack plus only necessary BlueRev-specific equations for biology, light, mixing/shear, gas transfer, controls, hydraulics and energy. |
| 108 | planned | — | DESIGN-STUDY-CONTROLLER-1 | 107 | Add a deterministic/reproducible DesignStudy/StudyController inner loop where DOE/optimizer/search receives every evaluator result directly, with persisted feasibility/failure/Pareto state while Jarvis remains in the outer interpretation/intervention loop. |
| 109 | planned | — | PROCESS-CAD-HANDOFF-1 | 005, 071b, 108 | Introduce a typed ProcessDesignEnvelope for process-driving geometry/flows/constraints and an explicit handoff to detailed GeometrySpec/CAD, with physical verification able to reopen the study instead of making CAD hidden process authority. |
| 110 | planned | — | MULTIFIDELITY-ENGINEERING-1 | 108, 109 | Add decision-driven fidelity escalation from analytical/reduced-order evaluators to CFD/FEM/specialist tools only when needed, carrying exact qualification/validity evidence and allowing high-fidelity results to feed back into the same study. |

## Superseded planning aliases and resolved collisions

- Historical `045 = AGENT-ORCH` references are superseded by `060`; `045` is
  cancelled as a standalone isolation program and may be reopened only by its
  explicit product-reachability or non-bundled-execution triggers.
- Historical `057 = Workspace home`, `057b`, and `057c` references remain
  superseded and must not be reused. Monolithic 058 is now cancelled; its product
  objective is redistributed across 070, 083, 091, and 029, while 058b and 058c
  retain their own re-derived operator-workstation scopes.
- Specs 030 and 037 are cancelled as standalone conversation surfaces; their valid
  proposal and BLUECAD on-ramp responsibilities are absorbed by 090 and 091.
- Specs 031, 034, and 036 retain only bounded JarvisOS-side vocabulary, persona-policy,
  and authority-display contracts. They do not authorize a second conversation or
  orchestration engine and do not reopen frozen 066–068.
- Historical 078 PBR-MODELING-0 is cancelled as a standalone implementation identity;
  its merged planning/scientific evidence remains reference material, while 107 is the
  sole future integrated PBR evaluator implementation authority after 103/106.
- IDs 081–099 are reserved by FRONTEND-BETA-AUTHORITY-0 plus the 094 normal-spine re-derivation, 095 operator-workstation re-derivation, and the 099 emergency security interrupt as recorded in the registry;
  all references use the canonical three-digit form required by the registry gate, with existing suffix form reused only where explicitly registered (such as 071b).
- IDs 100–110, including the explicitly registered suffix slices 100a/100b, are reserved for the post-functional-beta visual-identity, lean-codebase and zero-sunk-cost architecture/process replatforming sequence. They are planning rows only until individually re-derived and made ready.

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

## Current priority and drafting order

1. Preserve the merged 059 foundation: PR #90/059a, PR #95 definition amendment,
   PR #98/ADR-059, and PR #101 lifecycle reconciliation.
2. `059b` implementation is merged in PR #119; preserve its server-owned sensitivity,
   packet, trigger, ticket, reservation, accounting, audit, and fallback boundaries.
3. `061a` TOKEN-FLOW-CORE-0 is merged in PR #134. Preserve its canonical flow,
   attempt, confirmation, and accounting authority while implementing `061b`
   continuation, protected resume, and assembled-output completion separately.
4. Draft and promote `066` HERMES-PASSTHROUGH-0 and `067` JARVIS-MCP-0 only after
   their contracts are reconciled with 059b, 061a/061b, and existing service boundaries.
5. Draft and promote `068` HERMES-CONFIG-0 only after 066/067 are stable and a
   concrete Windows-first host-isolation boundary is selected.
6. Complete the merged `047` model through `071` editable bindings, scenario runs,
   and honest forward DOF inspection before expanding to `048` + `049`; Hermes work
   must not indefinitely displace measurable BlueRev engineering progress.
7. Run `069` MEMORY-CONSOLIDATE-0 as the first Hermes dogfood only after 066–068
   are merged and the required local route is qualified.
8. Continue `063`/`064`, `012` → `033`, and residual conversation/UI rows according
   to dependencies and measured value.

Trigger-gated rows remain `planned` until their stated evidence exists. Always
check rows marked `in_review` before choosing any `ready` spec and confirm no open
PR overlaps the target files or runtime boundary.

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
| 006b | ready | — | BLUECAD parametric variants | 006 | Add sliders and deterministic rebuilds for approved parametric GeometrySpec variants. |
| 006c | merged | [#30](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/30) | BLUECAD workbench UX pass | 006 | Add archive, malformed-detail inspection, promotion, retry/duplicate-brief flows, and safer validation rendering. |
| 007 | merged | [#17](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/17) | BLUECAD tool registry | 005 | Add fail-closed tool registration, health/hash checks, subprocess execution boundaries, and CI license-boundary enforcement. |
| 008 | merged | [#32](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/32) | BLUECAD Gmsh mesh adapter | 005, 007 | Generate deterministic Gmsh inputs and physical groups, invoke Gmsh through the registry, and return structured mesh-quality outcomes. |
| 009 | merged | [#35](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/35) | BLUECAD CalculiX FEM adapter | 008 | Assemble deterministic static CalculiX decks, run the registered solver, parse result summaries, and evaluate Tier 3 criteria. |
| 010 | merged | [#20](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/20), [#26](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/26), [#28](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/28) | BLUECAD AI loop v0 | 005 | Add the bounded candidate/attempt loop, safe-default parking, prompt/schema flow, validation, repair attempts, and traceable prompt versions. |
| 011 | planned | — | Core Team review panel | 034 | Add advisory persona reviews over artifacts and evidence; personas are bounded configurations, not autonomous authorities or a fake swarm. |
| 012 | planned | — | L2 ephemeral free-script proposals | 010, 016 | Accelerate one-design-only AI script proposals through the existing hashed/AST-checked `bluecad_l2_v0` path; scripts remain reviewed local-trusted code, not hostile-code sandbox input, and automatic untrusted execution requires 045 isolation evidence. |
| 013 | planned | — | Tier 2 domain-validator plugin interface | 005, 010 | Define a narrow plugin boundary for BlueRev-specific engineering checks that emit deterministic validation evidence without letting plugins own routing, memory, or promotion. |
| 014 | planned | — | OpenFOAM CFD case-bundle adapter v0 | 007, 008, 049 | Produce inspectable OpenFOAM case bundles and evidence only when process/light proxies leave a concrete decision unresolved; no generic CFD platform or automatic solver authority. |
| 015 | merged | [#33](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/33) | PROVIDER-GW-1 | 003 | Replace hardcoded bindings with a validated provider registry and generic OpenAI-compatible adapter while preserving safe defaults. |
| 016 | merged | [#39](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/39) | RUNNER-EXT-1: BLUECAD L2 | 005, 007 | Extend the bounded runner with a hashed, AST-checked `bluecad_l2_v0` implementation kind and strict GeometrySpec/artifact contracts. |
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
| 029 | planned | — | Settings and secrets operator page | 015, 018, 061a | Expose existing provider mode, budget, token-cap, secret-entry, and today/month token+spend counters per provider; reuse `/ai/status`, and keep keys out of localStorage, logs, repository files, and normal frontend state. |
| 030 | planned | — | Conversation-to-proposal handoff | 037, 042, 060, 068 | Superseded in part by Hermes for the conversation loop. Retain only the JarvisOS-side contract that turns a workspace-scoped conversation result into a drafted brief, record proposal, or GeometrySpec with explicit approval before existing deterministic execution. |
| 031 | planned | — | Policy-owned design vocabulary surface | 005, 030, 067 | Superseded in part by Hermes chat configuration. Retain the JarvisOS-owned capability/vocabulary contract exposed through bounded services/MCP so any orchestrator reports what is expressible, approximate, or unsupported. |
| 032 | planned | — | Core Team critique inside design conversation | 011, 030, 034 | Add advisory persona critiques to the approved design-conversation flow without pretending independent agents or bypassing validation and promotion gates. |
| 033 | planned | — | Human-gated reusable part-kind proposal | 011, 012, 031, 056 | Promote exploration into reusable typed builders only through explicit human code promotion, protected property/conformance tests, parameter-schema review, and golden fixtures; no autonomous trusted-vocabulary mutation. |
| 034 | planned | — | Persona policy and capability metadata | 060, 068 | Superseded in part by Hermes personas/subagents. Retain only versioned JarvisOS policy metadata, capability labels, context profiles, and advisory/authority constraints; no independent memory, permissions, route ownership, or promotion. |
| 035 | planned | — | Domain Foundation navigator | 040, 050 | Add searchable/editable modeling-record navigation designed around provenance and future depends-on/feeds edges rather than a flat database list. |
| 036 | planned | — | Honest orchestrator status and authority UI | 034, 058, 060, 068 | Superseded in part by the Hermes interaction surface. Retain only thin JarvisOS UI contracts needed to show advisory identity, active route/policy status, proposal state, and human authority without claiming that personas or Hermes are independent authorities. |
| 037 | planned | — | Chat entry point to BLUECAD workbench | 010, 042 | Add the smallest chat on-ramp that creates or drafts a candidate in the existing workbench instead of introducing a second product surface. |
| 038 | merged | [#65](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/65) | SIM-WIRE | 044 | Wire the existing mesh and static-FEM adapters into the BLUECAD attempt loop as an opt-in advisory stage with evidence records and no auto-promotion. |
| 039 | planned | — | FRONTIER-1 provider route | 015, 018, 059b | Add the frontier provider adapter/route only behind the same server-owned egress, projected-budget, sensitivity, sanitization, provenance, trigger, and audit boundaries as every other external call. |
| 040 | merged | [#38](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/38) | MEMORYSTORE-0 | — | Add the single proposal/promotion boundary for AI- and calculation-originated engineering records with provenance and additive migration support. |
| 041 | merged | [#50](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/50) | DECISION-CAPTURE-0 | 040 | Parse bounded `jarvis-records` blocks from approved AI task responses and create proposed records through MemoryStore without extra model calls. |
| 042 | merged | [#56](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/56) | CONTEXT-PACK-1 | 040 | Add deterministic, budgeted, inspectable record selection with FTS/LIKE fallback and a side-effect-free preview endpoint. |
| 043 | merged | [#52](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/52) | CALC-1 | 016, 040 | Add a narrow `calc_v0` runner contract with AST policy, unit-bearing JSON outputs, deterministic artifacts, and parameter proposals. |
| 044 | merged | [#62](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/62) | EVIDENCE-BRIDGE-1 | 042 | Add typed validation/mesh/FEM evidence records and deterministic bounded evidence lines for context packs. |
| 045 | planned | — | Runner hardening boundary | 043 | Define the next measured isolation step and prevent policy-guarded local Python execution from being represented as an OS-level hostile-code sandbox. |
| 046 | planned | — | Alternative design loop | 006b, 011, 038 | Trigger only after the review panel proves useful: explain a failed FEM result, propose a bounded alternative, build it, and compare variants without auto-promotion. |
| 047 | merged | [#143](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/143) | BLUEREV-PROCESS-0: geometry, hydraulics, and pumping | 043 | Ship the caller-parameterized forward `calc_v0` model for geometry, hydraulics, residence/turnover, and pumping; formulas, units, correlations, and validity domains are versioned, while all nine project/operating values remain editable bindings and numerical fixtures validate equations only. |
| 048 | planned | — | BLUEREV-PROCESS-1: biomass, nutrients, gas, harvest, and energy/cost KPIs | 043, 047 | Port ranks 8–18 while correcting productive-volume, recovery-balance, and pump-only-vs-total KPI errors; include a `preliminary_economic_evaluation_v0` output family (`variable_opex_rate`, `specific_variable_cost`, `gross_margin_proxy`) with explicit `economic_boundary` and `economic_basis` fields and per-input uncertainty/provenance, so design alternatives are economically comparable without implying a full TEA; `gross_margin_proxy` must support an explicit `not_computable` outcome when price, recovery, or time basis is unavailable rather than silently substituting zero or emitting a partial value; every claim carries units, assumptions, provenance, and verification cases. |
| 049 | planned | — | BLUEREV-PROCESS-2: buoyancy and light/transmittance proxies | 043, 047 | Add hardware mass and safety factor to buoyancy; require explicit optical path length; label proxies honestly and expose the measurements that would promote real light models. |
| 050 | planned | — | FLOWSHEET-1 dependency DAG | 047, 048, 049 | Materialize an inspectable graph from existing provenance without a recompute engine; normalize legacy FK/source forms at read time and own the shared `<kind>:<id>` resolver. |
| 051 | planned | — | FLOWSHEET-RECALC stale propagation | 050 | When an accepted input changes, deterministically mark dependent outputs stale and explain the dependency path; no automatic recomputation or silent promotion. |
| 052 | planned | — | CAD-LINK: process calculations to geometry and evidence back-links | 005, 038, 050 | Map accepted diameter, length, and tube-count outputs into GeometrySpec inputs and return validation/FEM evidence to the upstream nodes without making solver output authoritative. |
| 053 | planned | — | Decision packet and dossier export | 041, 044, 048 | Export recommendations, alternatives, evidence, assumptions, uncertainty, and provenance as a readable decision-to-evidence dossier for thesis, advisor, investor, or later IP/grant workflows. |
| 054 | planned | — | Proposal-review UI | 040, 041, 058 | Show proposed records with provenance and provide explicit promote/reject actions over existing endpoints; this is the load-bearing human authority surface. |
| 055 | planned | — | Project view: Mark-1 as one navigable object | 035, 044, 050 | Assemble decisions, calculations, CAD, evidence, and flowsheet for one workspace without inventing a second store or duplicating canonical data; 3D/digital-twin rendering follows the ADR-058 contract (`scene_component_id` plus a typed binding manifest to `<kind>:<id>` records; no engineering values stored in the view). |
| 056 | merged | [#88](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/88) | BLUECAD property-based geometry testing + determinism canary | 005 | Valid-domain property coverage, same-environment repeatability, and the canonical Linux full-manifest digest canary are merged. |
| 057 | cancelled | — | SPEC-LEDGER-0 | — | Cancelled after [planning PR #64](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/64): a generated ledger script and parallel handoff file are unnecessary while this canonical registry is sufficient. |
| 058 | planned | — | Unified workspace home layout | 006, 029, 037, 061a | Replace page-first navigation with the BLUECAD workbench/3D surface, persistent right-side AI entry, compact status strip with today/month token+spend counters per provider from existing status APIs, and shared design tokens. |
| 058b | planned | — | Workbench UX pass 2: variant comparison and design history | 006b, 058 | Add bounded side-by-side variant comparison and a parent-link history tree after parametric variants and the unified workspace exist. |
| 058c | planned | — | Report-to-3D linking | 006, 044, 058 | Let a failed validation/evidence check highlight the affected named geometry in the viewer, reusing existing artifact/node identities. |
| 059 | planned | — | IP-EGRESS-1 umbrella definition | 003, 015, 018, 021, 040, 042 | Definition amended through PR #95 and reconciled with ADR-059 for external policy autopilot, automatic sanitization, sampled audit, and explicit maintainer residual-risk acceptance; this row remains definition-only. |
| 059a | merged | [#90](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/90) | IP-EGRESS-1A: sensitivity and context foundation | 003, 015, 018, 021, 040, 042 | Digest-bound labels/derivatives, deterministic floors, stale handling, coherent read-snapshot selection, and S0/S1-only external preview merged in #90. |
| 059b | merged | [#119](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/119) | IP-EGRESS-1B: policy autopilot and execution enforcement | 059a | Prompt/manual-context authority, automatic sanitizer provenance, exact per-binding packets and decisions, ticket-ID confirmation, atomic projected-budget reservation, sampled audit, fallback enforcement, and usage-source-bound accounting are merged. |
| 060 | planned | — | AGENT-ORCH: Hermes integration umbrella | 040, 042, 059b | Definition-only umbrella for adopting pinned Hermes through standards-only boundaries; implementation is owned by slices 066–068, while JarvisOS retains state, policy, sensitivity, budget, egress, ledger, services, and promotion authority. |
| 061 | planned | — | TOKEN-FLOW-0 umbrella definition | 021, 059b | Definition-only umbrella for complete flow economics and bounded completion; implementation is owned by 061a core and 061b continuation slices. |
| 061a | merged | [#134](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/134) | TOKEN-FLOW-CORE-0 | 021, 059b | Correlate no-execution, synthetic, local-compute, and external-provider attempts in one canonical flow; separate adapter invocation from external dispatch, preserve 059b accounting authority, aggregate only external provider spend in USD, and expose local compute as unpriced. Continuation execution remains deferred to 061b. |
| 061b | ready | — | TOKEN-FLOW-CONTINUATION-0 | 061a | Add exact-length continuation, protected accumulated segments, restart-safe 059b confirmation resume, assembled-output digests, single final record capture, and safe continuation status after 061a is merged. |
| 062 | planned | — | GRADE-0 | 021, 059b, 061a, 061b | Record optional human flow grades (`useful`, `partly`, `rework`, `failed`) over finalized flow outcomes while keeping attempt execution/accounting evidence, external provider spend, local-unpriced coverage, synthetic exclusions, deterministic failures, and ungraded flows visible; grades never actuate routing. |
| 063 | planned | — | CAPTURE-VAULT-0 | 040, 042 | Add a local markdown vault and rebuildable local vector working layer, merged with canonical SQLite retrieval under explicit authority/conflict tags; no vectors over canonical records. |
| 064 | planned | — | LIT-RAG-0 | 042, 063 | Add corpus-tagged public-literature retrieval to the local working layer with source locators and canonical-over-literature authority; boundary consolidation remains a separately unnumbered planning gap. |
| 065 | planned | — | Provider-family diversification policy hook | 059b | After policy autopilot is proven, add a configurable hook that may separate families of S2/S3-derived content across provider accounts without weakening exact-packet, budget, sensitivity, or audit gates. |
| 066 | planned | — | HERMES-PASSTHROUGH-0 | 015, 018, 021, 059b, 061a, 061b, 062 | Define the loopback OpenAI-compatible agent-loop subset over `run_ai_task`, policy aliases, exact per-attempt gating, retry/idempotency, provenance, and `ai_jobs` correlation; external execution remains blocked until 059b is merged and active. |
| 067 | planned | — | JARVIS-MCP-0 | 005, 010, 040, 042, 043, 044, 059a | Expose bounded context, canonical search, MemoryStore proposal, `calc_v0`, BLUECAD candidate, and evidence tools through existing services; no direct storage/filesystem access, promotion, sampling, or authority. |
| 068 | planned | — | HERMES-CONFIG-0 | 066, 067 | Freeze a pinned/fingerprinted Hermes profile with passthrough-only model paths, Jarvis MCP only, host-level workspace isolation, explicit tool allowlist, disabled browser/computer/cron/proactive paths, and bounded delegation. |
| 069 | planned | — | MEMORY-CONSOLIDATE-0 | 040, 042, 061a, 061b, 062, 066, 067, 068 | First Hermes dogfood: consolidate bounded accepted records/evidence into MemoryStore proposals with conflict preservation, provenance, grading, and cost evidence; never promote, overwrite, delete, or lower sensitivity. |
| 071 | ready | — | MODEL-SCENARIO-DOF-0: editable bindings, scenario runs, and degree-of-freedom inspection | 040, 043, 047 | Expose immutable value-free model input contracts, side-effect-free forward binding/DOF preview, parameter-backed or manual scenario bindings, existing-runner execution, and one bounded Domain Foundation panel; no inverse solver, targets, optimizer, automatic promotion, or embedded design defaults. |

## Superseded planning aliases and resolved collisions

- Historical `045 = AGENT-ORCH` references are superseded by `060`; `045` is
  already owned by the runner-hardening boundary.
- Historical `057 = Workspace home`, `057b`, and `057c` references are
  superseded by `058`, `058b`, and `058c`; `057` remains the cancelled
  SPEC-LEDGER-0 and must not be reused.
- Specs 030, 031, 034, and 036 are superseded in part by the Hermes integration
  umbrella 060 and config slice 068. Their residual JarvisOS-side contracts remain
  live as described in the registry; they are not cancelled and do not authorize a
  second conversation or orchestration engine.

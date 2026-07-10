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

1. Implement `021b` as two sequential PRs: strict real-tool alpha proof, then
   atomic backup/restore with relocation verification.
2. Implement the already-ready engineering quality slices `024` and `056`.
3. Before serious BlueRev dogfood with real project IP or cloud providers, draft
   and implement `059` (sensitivity, retrieval, and egress enforcement).
4. Then draft in small dependency batches:
   `047` → `048` + `049` → `050` → `051` + `052` →
   `029` + `037` → `030` + `058` → `054` + `035` + `055` →
   `034` + `011` → `053`.
5. Trigger-gated rows remain `planned` until their stated evidence exists; do not
   start them merely because their number is lower.

Always check rows marked `in_review` before choosing any `ready` spec, and confirm
that no open PR overlaps the target files or runtime boundary.

## Registry

| Spec | Status | Implementation PR | Name | Depends on | Description |
| --- | --- | --- | --- | --- | --- |
| 001 | merged | [#4](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/4) | Parameter/Assumption schema freeze + Requirement record | — | Freeze engineering-record units, provenance, uncertainty fields, and requirement CRUD with additive migration behavior. |
| 002 | merged | [#7](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/7) | Local route smoke matrix + routing eval set | 001 | Add repeatable local-route measurements and an offline routing evaluation set without making live model calls in CI. |
| 003 | merged | [#8](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/8) | ESCALATE-CONFIRM-0 | 002 | Add a non-executing external escalation proposal and explicit user-confirmed execution path with cost, context-exclusion, and ledger controls. |
| 004 | merged | [#10](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/10) | Tiered PR review | — | Establish cheap review on every push, frontier/senior escalation, bounded fix rounds, and advisory-only automated review. |
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
| 012 | planned | — | L2 ephemeral free-script proposals | 010, 016 | Let AI propose one-design-only BLUECAD scripts through the existing bounded runner and validators; first verify that current `bluecad_l2_v0` contracts are sufficient rather than inventing a second runner. |
| 013 | planned | — | Tier 2 domain-validator plugin interface | 005, 010 | Define a narrow plugin boundary for BlueRev-specific engineering checks that emit deterministic validation evidence without letting plugins own routing, memory, or promotion. |
| 014 | planned | — | OpenFOAM CFD case-bundle adapter v0 | 007, 008, 049 | Produce inspectable OpenFOAM case bundles and evidence only when process/light proxies leave a concrete decision unresolved; no generic CFD platform or automatic solver authority. |
| 015 | merged | [#33](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/33) | PROVIDER-GW-1 | 003 | Replace hardcoded bindings with a validated provider registry and generic OpenAI-compatible adapter while preserving safe defaults. |
| 016 | merged | [#39](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/39) | RUNNER-EXT-1: BLUECAD L2 | 005, 007 | Extend the bounded runner with a hashed, AST-checked `bluecad_l2_v0` implementation kind and strict GeometrySpec/artifact contracts. |
| 017 | merged | [#37](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/37) | Autonomous three-tier review | 004 | Implement cheap → senior → expert advisory review with bounded Codex fix loops and human-only merge authority. |
| 018 | merged | [#33](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/33), [#43](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/43) | PROVIDER-GW-2 | 015 | Complete provider-cap/fallback enforcement and correct provider usage accounting while preserving explicit routing and audit controls. |
| 019 | merged | [#40](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/40), [#41](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/41), [#44](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/44) | Senior review hardening | 017 | Harden streaming, reasoning budgets, verdict parsing, stale-script behavior, retry limits, and review diagnostics. |
| 020 | ready | — | Pipeline doctor | 017, 019 | Add a deterministic watchdog for silent review-pipeline failures, stale branches, missing labels/comments, and stalled fix requests. |
| 021 | merged | [#70](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/70) | ALPHA-GATE hardening | — | Enforce the server-owned external-provider decision at the shared execution spine for every concrete network binding and fallback; PR #70 supersedes stale PR #66. |
| 021b | in_review | [#72](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/72) | ALPHA-GATE completion: real-tool proof + recoverable data root | 021, 038, 044 | Slice A strict real-tool proof is in review; atomic path-rebased backup/restore remains the separate Slice B implementation. |
| 022 | merged | [#49](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/49) | Codex PR autopush without automerge | 017, 019 | Add a bounded actuator for pushing materialized fixes to an existing PR branch while forbidding merge, protected-branch pushes, force-push, and secret/workflow changes. |
| 023 | planned | — | Adversarial proposal corpus | 010 | Add bounded hostile and degenerate model-output fixtures; the loop must reject or park them without crashes, unbounded work, provider calls, or authority bypass. |
| 024 | ready | — | FEM verification battery | 008, 009 | Build an analytic benchmark ladder that checks mesh/FEM results against known mechanics solutions and convergence expectations. |
| 025 | planned | — | Semantic routing evaluation and promotion policy | 002, 010 | Use labeled real task/ledger outcomes only after enough dogfood data exists; promote a local classifier per task family only above explicit thresholds and preserve deterministic escalation. |
| 026 | planned | — | BoardSession stateful multi-persona sessions | 011, 034, 040 | Deferred post-alpha: add shared-state multi-persona sessions only after the advisory panel and memory/context spine prove useful in real work. |
| 027 | planned | — | Modal and thermal analysis types | 009, 024 | Extend the verified static-FEM boundary only when a real BlueRev decision requires modal or thermal analysis; do not pre-build a broad solver matrix. |
| 028 | planned | — | Additive migration discipline | — | Document and test the existing versioned, additive migration policy before schema growth makes drift costly; no migration framework rewrite. |
| 029 | planned | — | Settings and secrets operator page | 015, 018 | Expose existing provider mode, budget, token-cap, and secret-entry endpoints safely; keys never enter localStorage, logs, repository files, or normal frontend state. |
| 030 | planned | — | Conversation v0 | 037, 042 | Turn a workspace-bound multi-turn conversation into a drafted brief or GeometrySpec that the user explicitly approves before the existing deterministic loop runs. |
| 031 | planned | — | Vocabulary-aware design conversation | 005, 030 | Give chat the live part-kind catalog and limits so it reports what is expressible, approximate, or unsupported instead of silently degrading requests. |
| 032 | planned | — | Core Team critique inside design conversation | 011, 030, 034 | Add advisory persona critiques to the approved design-conversation flow without pretending independent agents or bypassing validation and promotion gates. |
| 033 | planned | — | Human-gated reusable part-kind proposal | 011, 012, 031, 056 | Let AI draft a builder, parameter schema, and golden fixture for a new kind; property/conformance checks and explicit human code promotion are mandatory, and autonomous trusted-vocabulary mutation is forbidden. |
| 034 | planned | — | AGENT-CORE-1: personas as configuration | — | Freeze persona prompts, capabilities, context profiles, and advisory labels as configuration over the existing AI spine; no independent memory, permissions, or orchestration engine. |
| 035 | planned | — | Domain Foundation navigator | 040, 050 | Add searchable/editable modeling-record navigation designed around provenance and future depends-on/feeds edges rather than a flat database list. |
| 036 | planned | — | Honest multi-agent chat UI | 034, 058 | Present clearly labeled advisory persona calls in the unified workspace; do not claim a real swarm until orchestration evidence exists. |
| 037 | planned | — | Chat entry point to BLUECAD workbench | 010, 042 | Add the smallest chat on-ramp that creates or drafts a candidate in the existing workbench instead of introducing a second product surface. |
| 038 | merged | [#65](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/65) | SIM-WIRE | 044 | Wire the existing mesh and static-FEM adapters into the BLUECAD attempt loop as an opt-in advisory stage with evidence records and no auto-promotion. |
| 039 | planned | — | FRONTIER-1 provider route | 015, 018, 059 | Add the frontier provider adapter/route only behind the same budget, confirmation, sensitivity, redaction, provenance, and audit boundaries as every other external call. |
| 040 | merged | [#38](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/38) | MEMORYSTORE-0 | — | Add the single proposal/promotion boundary for AI- and calculation-originated engineering records with provenance and additive migration support. |
| 041 | merged | [#50](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/50) | DECISION-CAPTURE-0 | 040 | Parse bounded `jarvis-records` blocks from approved AI task responses and create proposed records through MemoryStore without extra model calls. |
| 042 | merged | [#56](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/56) | CONTEXT-PACK-1 | 040 | Add deterministic, budgeted, inspectable record selection with FTS/LIKE fallback and a side-effect-free preview endpoint. |
| 043 | merged | [#52](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/52) | CALC-1 | 016, 040 | Add a narrow `calc_v0` runner contract with AST policy, unit-bearing JSON outputs, deterministic artifacts, and parameter proposals. |
| 044 | merged | [#62](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/62) | EVIDENCE-BRIDGE-1 | 042 | Add typed validation/mesh/FEM evidence records and deterministic bounded evidence lines for context packs. |
| 045 | planned | — | Runner hardening boundary | 043 | Define the next measured isolation step and prevent policy-guarded local Python execution from being represented as an OS-level hostile-code sandbox. |
| 046 | planned | — | Alternative design loop | 006b, 011, 038 | Trigger only after the review panel proves useful: explain a failed FEM result, propose a bounded alternative, build it, and compare variants without auto-promotion. |
| 047 | planned | — | BLUEREV-PROCESS-0: geometry, hydraulics, and pumping | 043 | Port workbook ranks 1–7 into unit-bearing `calc_v0` nodes, correct hydraulic-vs-illuminated area and residence-vs-loop-turnover definitions, and ship deterministic/literature verification cases. |
| 048 | planned | — | BLUEREV-PROCESS-1: biomass, nutrients, gas, harvest, and energy/cost KPIs | 043, 047 | Port ranks 8–18 while correcting productive-volume, recovery-balance, and pump-only-vs-total KPI errors; every claim carries units, assumptions, provenance, and verification cases. |
| 049 | planned | — | BLUEREV-PROCESS-2: buoyancy and light/transmittance proxies | 043, 047 | Add hardware mass and safety factor to buoyancy; require explicit optical path length; label proxies honestly and expose the measurements that would promote real light models. |
| 050 | planned | — | FLOWSHEET-1 dependency DAG | 047, 048, 049 | Materialize an inspectable graph from existing provenance without a recompute engine; normalize legacy FK/source forms at read time and own the shared `<kind>:<id>` resolver. |
| 051 | planned | — | FLOWSHEET-RECALC stale propagation | 050 | When an accepted input changes, deterministically mark dependent outputs stale and explain the dependency path; no automatic recomputation or silent promotion. |
| 052 | planned | — | CAD-LINK: process calculations to geometry and evidence back-links | 005, 038, 050 | Map accepted diameter, length, and tube-count outputs into GeometrySpec inputs and return validation/FEM evidence to the upstream nodes without making solver output authoritative. |
| 053 | planned | — | Decision packet and dossier export | 041, 044, 048 | Export recommendations, alternatives, evidence, assumptions, uncertainty, and provenance as a readable decision-to-evidence dossier for thesis, advisor, investor, or later IP/grant workflows. |
| 054 | planned | — | Proposal-review UI | 040, 041, 058 | Show proposed records with provenance and provide explicit promote/reject actions over existing endpoints; this is the load-bearing human authority surface. |
| 055 | planned | — | Project view: Mark-1 as one navigable object | 035, 044, 050 | Assemble decisions, calculations, CAD, evidence, and flowsheet for one workspace without inventing a second store or duplicating canonical data. |
| 056 | ready | — | BLUECAD property-based geometry testing + determinism canary | 005 | Add generated valid GeometrySpec coverage and a checked-in manifest-digest canary without invoking live CAD/solver tools in normal CI. |
| 057 | cancelled | — | SPEC-LEDGER-0 | — | Cancelled after [planning PR #64](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/64): a generated ledger script and parallel handoff file are unnecessary while this canonical registry is sufficient. |
| 058 | planned | — | Unified workspace home layout | 006, 029, 037 | Replace page-first navigation with the BLUECAD workbench/3D surface, persistent right-side AI entry, compact status strip, and shared design tokens; historical roadmap references to workspace-home `057` now mean `058`. |
| 058b | planned | — | Workbench UX pass 2: variant comparison and design history | 006b, 058 | Add bounded side-by-side variant comparison and a parent-link history tree after parametric variants and the unified workspace exist. |
| 058c | planned | — | Report-to-3D linking | 006, 044, 058 | Let a failed validation/evidence check highlight the affected named geometry in the viewer, reusing existing artifact/node identities. |
| 059 | planned | — | IP-EGRESS-1: sensitivity, retrieval, and external-boundary enforcement | 015, 018, 040, 042 | Turn the existing S0–S4 PRE contracts into one fail-closed runtime decision boundary for memory/history/retrieval, provider/tool eligibility, redaction, confirmation, and provenance-preserving sanitized derivatives before real BlueRev IP is dogfooded externally. |
| 060 | planned | — | AGENT-ORCH: bounded real orchestration | 011, 034, 040, 042 | Supersede historical orchestration references to `045`; trigger only after memory/context and the advisory panel survive sustained dogfood, then add auditable bounded steps rather than a second authority or manager stack. |

## Superseded planning aliases and resolved collisions

- Historical `045 = AGENT-ORCH` references are superseded by `060`; `045` is
  already owned by the runner-hardening boundary.
- Historical `057 = Workspace home`, `057b`, and `057c` references are
  superseded by `058`, `058b`, and `058c`; `057` remains the cancelled
  SPEC-LEDGER-0 and must not be reused.
- PR #66 is superseded by merged spec `021` implementation PR #70.
- Spec `021` owns the shared external-provider execution boundary. Slice 021b-A
  is in review in PR #72; relocatable backup/restore remains the separate 021b-B
  implementation.

## Notes requiring later reconciliation

- Strategy/backlog documents are planning evidence, not live state. Where their
  numbering or sequence conflicts with this file, this registry wins; update the
  strategy document only when it is next touched for a real drafting decision.
- Historical individual spec `Status:` lines may still use the old vocabulary.
  They should not be used for dispatch decisions and do not need a bulk cleanup.
- The process verification battery remains acceptance scope inside `047`–`049`;
  do not create a separate subsystem unless implementation exposes a concrete gap.
- Founder-layer ideas (patent/prior-art, grants, BOM/supplier, regulatory) remain
  trigger-gated product directions, not specs, until a real filing, deadline,
  procurement decision, or regulatory question creates a bounded deliverable.
- The separate local-model/Hermes benchmark program remains postponed until
  2026-07-22 and does not belong in this JarvisOS implementation registry yet.
- If a row conflicts with merged code or GitHub PR state, correct this file in the
  smallest possible follow-up and record the evidence in the implementation PR
  column or description according to the column contract above.

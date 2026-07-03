# JarvisOS / BLUECAD Program Backlog

Status: living document (created 2026-07-03, Fable 5)
Purpose: every planned development — alpha and post-alpha, engineering and
UI — has a number, a one-line scope, and a pointer to where its binding
decisions live. Nothing exists only in chat history. Specs get written (by
frontier review or drafted by Codex against a kernel) only when their slot
comes up; this table is the queue.

Sources of binding decisions: `BLUECAD_CORE_DESIGN.md` (contracts, roadmap
005–014, 018), `JARVISOS_PLATFORM_GAPS_PLAN.md` (kernels 015–017, 019),
`JARVISOS_CORE_TEAM_V1.md` (roster), `BLUECAD_TOOLING_AND_LICENSING.md`
(license invariants).

## Horizon 1 — Alpha-1 (pipeline proof)

| # | Item | State |
| --- | --- | --- |
| 005 | CAD adapter MVP | implementing (PR #12, stage 2 in progress) |
| 007 | Tool registry + CI license gate | spec ready — launchable now, independent |
| 010 | AI loop v0 + candidate/attempt ledger | spec ready (after 005) |
| 006 | Workbench viewer + report + attempt history | spec ready (after 005+010) |

## Horizon 2 — Alpha-2 (user's alpha gate)

| # | Item | State |
| --- | --- | --- |
| 005b | Remaining part-kind stubs (full-reactor layouts) | spec ready (after 005) |
| 006b | Parametric variants (sliders, deterministic rebuild) | spec ready (after 006) |
| 018 | Chat entry point → workbench | roadmap row; spec to draft (small) |
| 021 | Alpha-gate demo as executable CI test + data-root backup job | idea; kernel below |

## Horizon 3 — Engineering depth

| # | Item | State |
| --- | --- | --- |
| 008 | Gmsh mesh adapter | spec ready (after 005+007) |
| 009 | CalculiX FEM adapter (static) + Tier 3 | spec ready (after 008) |
| 011 | Review panel (Core Team personas critique artifacts) | roadmap row; needs 017 + spec |
| 013 | Tier 2 domain-validator plugin interface | roadmap row; spec to draft |
| 024 | FEM verification battery (analytic benchmark ladder) | idea; kernel below |
| 027 | Modal + thermal analysis types | idea (extends 009; schema already reserves them) |
| 014 | CFD case-bundle adapter v0 (OpenFOAM, WSL2) | boundary designed in core design §6 |
| 012 | L2 free-script proposals (flagged) | roadmap row; blocked by 016 |

## Horizon 4 — Platform

| # | Item | State |
| --- | --- | --- |
| 015 | Provider gateway v1 (5 providers, route classes as data) | draft reviewed (PR #13), finalize → ready |
| 016 | Runner extension for L2 (AST allowlist) | draft reviewed (PR #14), finalize → ready |
| 019 | FRONTIER-1: Anthropic adapter, `external:frontier`, Fable approval gate | kernel frozen (platform plan); spec to draft |
| 017 | AGENT-CORE-1: personas as config | kernel frozen; spec to draft |
| 026 | BoardSession (multi-persona stateful sessions) | explicitly deferred post-alpha |
| 025 | Semantic routing eval: promote local classifier to default-pick per task class | assessment done (memory + below); post-alpha, needs BLUECAD ledger data |
| 028 | Migration discipline doc + versioned additive migrations policy | idea (one page, Codex-draftable) |

## Horizon 5 — GUI / UX program

Principles (binding for all frontend slices; "beautiful" here = legible,
calm, engineering-grade):

1. **Workbench-first**: one BLUECAD surface; chat is an on-ramp (018), never
   a second UI for the same state.
2. **Verdict before geometry**: pass/fail + parked reason always visible at
   a glance; 3D view is the centerpiece but never hides the report.
3. **Progressive disclosure**: attempts, check details, and raw JSON are one
   click away, collapsed by default; no dashboard sprawl.
4. **Design tokens, not ad-hoc CSS**: a small token set (spacing, type
   scale, status colors — one color semantic shared with validation states)
   introduced once and reused.
5. Every UI slice ships with screenshots in the PR for review (frontier or
   human) — visual review is part of the gate.

| # | Item | State |
| --- | --- | --- |
| 020 | Design system v0: tokens, layout shell, status components; restyle of existing pages kept minimal | idea; first UI slice after 006 |
| 020b | Workbench UX pass 2: variant comparison (side-by-side viewer), design-history tree from candidate parent links | idea (data model already supports it) |
| 020c | Report → 3D linking: clicking a failed check highlights the affected part in the viewer (part_ids are in `detail`) | idea; genuinely differentiating, cheap with GLB node names |

## Quality program (the "out-of-the-box" tier)

| # | Item | Why it is worth it |
| --- | --- | --- |
| 021 | **Executable alpha gate**: one CI-runnable script per horizon that does brief→build→validate→(mesh→solve)→artifacts and asserts the outcome. | Turns "alpha raggiunta" from an opinion into a green check; doubles as backup-tested demo. |
| 022 | **Property-based geometry testing** (hypothesis): generate random *valid* GeometrySpecs (bounded params) and assert invariants — watertight, volume>0 and < bbox volume, ports frame-coincident after assembly, manifest digest stable. Plus a **determinism canary**: CI job rebuilds golden fixtures and diffs manifest digests on every dependency bump. | Golden tests catch regressions you foresaw; property tests catch kernel edge cases you did not (thin walls, tiny angles, near-tangent bends). The canary catches silent behavior drift in build123d/OCP pins. |
| 023 | **Adversarial proposal corpus** for the 010 loop: a fixture set of hostile/degenerate LLM outputs (prompt-injection-shaped JSON, 1e30 dimensions, 10k parts, deeply nested junk, unicode tricks) — loop must park cleanly, never crash, never spawn work proportional to input size. | The AI loop is an attack surface even single-user (a poisoned model reply must not DoS the kernel). Cheap to build, permanent safety net. |
| 024 | **FEM verification battery** (after 009): cantilever tip deflection, thick-wall cylinder hoop stress (Lamé), simply-supported beam frequency — each vs analytic solution with stated mesh and tolerance, run under the real-solver marker and reported in `reports/`. | This is what makes results *credible engineering*, not numbers from a black box — the professional-grade differentiator for BlueRev use. Verification ladder ≈ solver acceptance test, re-run on every solver/mesh version bump. |
| 025 | **Semantic routing eval** (post-alpha): label BLUECAD ledger outcomes (cheap-tier sufficient vs escalated) as ground truth; measure local classifier accuracy per task class; promote to default-pick only above threshold, keep escalation-on-failure as the behavioral safety net. | Uses data the alpha generates for free; upgrades routing from static table to measured policy without touching safety invariants. |

## Standing maintenance

- Data-root backup with rotation (part of 021).
- License re-verification at every version pin change (tooling doc ledger).
- Assumption ledger (`BLUECAD_CORE_DESIGN.md` §11) — A3 closes with 008,
  A4 with 009, A7 with 007.

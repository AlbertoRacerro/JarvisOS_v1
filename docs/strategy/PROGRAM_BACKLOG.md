# JarvisOS / BLUECAD Program Backlog

Status: living document (created 2026-07-03, Fable 5)
Purpose: every planned development — alpha and post-alpha, engineering and
UI — has a number, a one-line scope, and a pointer to where its binding
decisions live. Nothing exists only in chat history. Specs get written (by
frontier review or drafted by Codex against a kernel) only when their slot
comes up; this table is the queue.

Sources of binding decisions: `BLUECAD_CORE_DESIGN.md` (contracts, roadmap
005–014, 037), `JARVISOS_PLATFORM_GAPS_PLAN.md` (kernels 015–016, 034, 039),
`JARVISOS_CORE_TEAM_V1.md` (roster), `BLUECAD_TOOLING_AND_LICENSING.md`
(license invariants), `BLUECAD_CONVERSATIONAL_DESIGN_LAYER.md` (north star:
conversational intent phase + self-extending vocabulary; slices 030–033),
`JARVISOS_KNOWLEDGE_GRAPH_NORTHSTAR.md` (PKG-1: persistent knowledge graph —
deferred, trigger-gated; domain/world-model track first, code-graph track
only once an internal code-navigating agent exists).

## Reserved numbering (fixed 2026-07-06, resolves collisions)

- 030–033: conversational design layer slices (`BLUECAD_CONVERSATIONAL_DESIGN_LAYER.md`).
- 034: AGENT-CORE-1 (renumbered from 017 — that number was taken by the merged
  review-chain spec `docs/specs/017-two-tier-autonomous-review.md`).
- 035: Domain Foundation navigator (ex 030); 036: multi-agent chat UI (ex 031).
- 037: chat entry point → workbench (renumbered from 018 — that number was
  taken by the merged provider-gateway-v2 spec,
  `docs/specs/018-provider-gateway-v2.md`).
- 038: SIM-WIRE (mesh+FEM into the loop) — spec ready (2026-07-07, `docs/specs/038-sim-wire.md`, implement after 044 merges).
- 039: FRONTIER-1 (renumbered from 019 on 2026-07-07 — that number was taken
  by the merged senior-review-hardening spec,
  `docs/specs/019-senior-review-hardening.md`, PR #40).
- 047–055: beta program block (BLUEREV-PROCESS-0/1/2, FLOWSHEET-1/RECALC/
  CAD-LINK, DECISION-PACKET, PROPOSAL-REVIEW UI, PROJECT-VIEW) — see
  `JARVISOS_BETA_PROGRAM.md`, which also fixes the SC-1..SC-4 seam contracts.
- 040–046: memory/swarm spine block (MemoryStore, decision capture, context
  packs, calc runner, evidence bridge, orchestration, alternative loop) —
  drafts started 2026-07-06.

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
| 037 | Chat entry point → workbench (renumbered from 018 — that number is now taken by the merged provider-gateway-v2 spec) | roadmap row; spec to draft (small) |
| 021 | Alpha-gate demo as executable CI test + data-root backup job | spec ready (2026-07-07, `docs/specs/021-alpha-gate.md` — slice A after 038+044 merge, slice B launchable now) |

## Horizon 3 — Engineering depth

| # | Item | State |
| --- | --- | --- |
| 008 | Gmsh mesh adapter | spec ready (after 005+007) |
| 009 | CalculiX FEM adapter (static) + Tier 3 | spec ready (after 008) |
| 011 | Review panel (Core Team personas critique artifacts) | roadmap row; needs 034 + spec |
| 013 | Tier 2 domain-validator plugin interface | roadmap row; spec to draft |
| 024 | FEM verification battery (analytic benchmark ladder) | spec ready (2026-07-07, `docs/specs/024-fem-verification-battery.md`) |
| 027 | Modal + thermal analysis types | idea (extends 009; schema already reserves them) |
| 014 | CFD case-bundle adapter v0 (OpenFOAM, WSL2) | boundary designed in core design §6 |
| 012 | L2 free-script proposals (flagged) | roadmap row; blocked by 016 |

## Horizon 4 — Platform

| # | Item | State |
| --- | --- | --- |
| 015 | Provider gateway v1 (5 providers, route classes as data) | draft reviewed (PR #13), finalize → ready |
| 016 | Runner extension for L2 (AST allowlist) | draft reviewed (PR #14), finalize → ready |
| 039 | FRONTIER-1: Anthropic adapter, `external:frontier`, Fable approval gate (renumbered from 019; that number is taken by the merged senior-review-hardening spec) | kernel frozen (platform plan); spec to draft |
| 034 | AGENT-CORE-1: personas as config (renumbered from 017; that number is taken by the merged review-chain spec) | kernel frozen; spec to draft |
| 026 | BoardSession (multi-persona stateful sessions) | explicitly deferred post-alpha |
| 025 | Semantic routing eval: promote local classifier to default-pick per task class | assessment done (memory + below); post-alpha, needs BLUECAD ledger data |
| 028 | Migration discipline doc + versioned additive migrations policy | idea (one page, Codex-draftable) |

## Horizon 5 — GUI / UX program

Principles (binding for all frontend slices; "beautiful" here = legible,
calm, engineering-grade):

1. **Workbench-first**: one BLUECAD surface; chat is an on-ramp (037), never
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

**UI product direction (frozen 2026-07-04, from the maintainer's external
UI review, triaged):** one home Workspace replaces the page-first UI —
BLUECAD workbench + CAD viewer as the main surface, AI execution as a
persistent right-side chat, compact mission/status strip; Dashboard demoted
to a secondary System Overview; Dev Local Chat absorbed into the AI surface
as a local/debug mode, not a nav item; Domain Foundation rebuilt as a
searchable/editable record navigator. The long-term green-shell render is
the aspirational reference, not a spec. Triage notes: the external review
assumed settings/secrets are missing — **false**: `GET/PUT /ai/settings`,
the `secrets` module (routes/service/storage), and escalation-confirm exist
on the backend; R1 is a frontend surface over existing endpoints plus a
secrets-hygiene pass, not new architecture. Multi-agent chat ships UI-first
with personas clearly labeled as advisory single-calls until 034/011 land —
never fake a swarm.

| # | Item (R-milestone) | State |
| --- | --- | --- |
| 029 | **R1 — Settings & secrets page**: provider mode, budget, token caps, API-key entry via the existing secrets endpoints; keys never in localStorage/frontend state/logs/plain repo files | idea; Codex-draftable (backend surface exists) |
| 020 | **R2 — Workspace home layout**: single home (workbench + right AI chat + status strip), Dashboard→System Overview, Dev Local Chat absorbed as mode; design tokens v0 | idea; needs frontier kernel for layout contract, then Codex |
| 035 | **R3 — Domain Foundation navigator**: search, type filter, edit/delete, detail view over modeling records (endpoints partly exist; add missing update/delete additively) | idea; Codex-draftable |
| — | **R4 — Pipeline visibility**: largely shipped by 006+010 (attempt history, parked reasons); remainder = live-smoke polish items only | mostly done |
| 036 | **R5 — Multi-agent chat UI**: persona-labeled chat over the existing single-call spine (Core Team roster as config), honest "advisory" badges; no orchestration | idea; after 020 |
| 034+011+026 | **R6 — Real multi-agent orchestration** | already in backlog (kernels frozen) |
| 020b | Workbench UX pass 2: variant comparison, design-history tree from candidate parent links | idea (data model ready) |
| 020c | Report → 3D linking: failed check highlights the affected part in the viewer | idea; cheap with GLB node names |

## Quality program (the "out-of-the-box" tier)

| # | Item | Why it is worth it |
| --- | --- | --- |
| 021 | **Executable alpha gate**: one CI-runnable script per horizon that does brief→build→validate→(mesh→solve)→artifacts and asserts the outcome. | Turns "alpha raggiunta" from an opinion into a green check; doubles as backup-tested demo. |
| 022 | **Property-based geometry testing** (hypothesis): generate random *valid* GeometrySpecs (bounded params) and assert invariants — watertight, volume>0 and < bbox volume, ports frame-coincident after assembly, manifest digest stable. Plus a **determinism canary**: CI job rebuilds golden fixtures and diffs manifest digests on every dependency bump. | Golden tests catch regressions you foresaw; property tests catch kernel edge cases you did not (thin walls, tiny angles, near-tangent bends). The canary catches silent behavior drift in build123d/OCP pins. |
| 023 | **Adversarial proposal corpus** for the 010 loop: a fixture set of hostile/degenerate LLM outputs (prompt-injection-shaped JSON, 1e30 dimensions, 10k parts, deeply nested junk, unicode tricks) — loop must park cleanly, never crash, never spawn work proportional to input size. | The AI loop is an attack surface even single-user (a poisoned model reply must not DoS the kernel). Cheap to build, permanent safety net. |
| 024 | **FEM verification battery** (after 009): cantilever tip deflection, thick-wall cylinder hoop stress (Lamé), plate-with-hole SCF (Kirsch, finite-width-corrected; the beam-frequency case is deferred until 027 lands — erratum 2026-07-07, see spec 024) — each vs analytic solution with stated mesh and tolerance, run under the real-solver marker and reported in `reports/`. | This is what makes results *credible engineering*, not numbers from a black box — the professional-grade differentiator for BlueRev use. Verification ladder ≈ solver acceptance test, re-run on every solver/mesh version bump. |
| 025 | **Semantic routing eval** (post-alpha): label BLUECAD ledger outcomes (cheap-tier sufficient vs escalated) as ground truth; measure local classifier accuracy per task class; promote to default-pick only above threshold, keep escalation-on-failure as the behavioral safety net. | Uses data the alpha generates for free; upgrades routing from static table to measured policy without touching safety invariants. |

## How backlog items become implementable (binding process note)

A backlog row is NOT launchable. The precision ladder is:
**backlog row → kernel (binding decisions) → full spec (template +
acceptance criteria + tests) → implementation**. Codex implements only from
full specs; launching Codex from a backlog row will produce guessed
architecture and is prohibited.

Who writes the spec when an item's turn comes:

- **Frontier-written or frontier-kerneled first** (judgment-heavy; a wrong
  spec here is expensive): 022 (property-test invariants and generation
  strategies), 023 (adversarial corpus design), 024 (FEM tolerances, mesh
  and benchmark selection — engineering judgment), 025 (promotion-threshold
  policy), 026 (BoardSession — needs a design session, kernel does not
  exist yet), 011 (panel semantics).
- **Codex-draftable from existing kernels/patterns, frontier/human review of
  the draft** (the 015/016 flow, which worked): 034, 039 (kernels frozen in
  `JARVISOS_PLATFORM_GAPS_PLAN.md`), 037, 021, 013, 027 (extends the 009
  pattern), 028, 020/020b/020c (UI — drafts must follow the Horizon 5
  principles and every UI PR ships screenshots for visual review).

## Standing maintenance

- Data-root backup with rotation (part of 021).
- License re-verification at every version pin change (tooling doc ledger).
- Assumption ledger (`BLUECAD_CORE_DESIGN.md` §11) — A3 closes with 008,
  A4 with 009, A7 with 007.

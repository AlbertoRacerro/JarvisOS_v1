# Work-item specs

Each file `NNN-<slug>.md` is one implementation slice, sized for a single agent
session and a single reviewable diff. Specs are written by the maintainer (with
strategic-review support) and executed by AI coding agents.

## Execution workflow

1. Pick the lowest-numbered spec with `Status: ready`.
2. Create a branch: `spec/NNN-<slug>`.
3. Read the spec fully. **Verify the "Files likely touched" list against the actual
   code before writing anything** — specs are written from docs-level knowledge and
   may be slightly stale. If reality conflicts with the spec, stop and report.
4. Implement within scope. Non-goals are binding.
5. Run the test gate in `AGENTS.md`.
6. Update the spec's `Status:` line to `implemented (pending review)` and note any
   deviations in a `## Implementation notes` section appended to the spec.
7. Summarize: what changed, files touched, test output, deviations, discoveries.

Review (human + Claude code review) happens on the diff before merge. A spec is
`done` only after merge.

## Status values

`draft` → `ready` → `implemented (pending review)` → `done` (or `blocked: <reason>`)

## Index

| Spec | Title | Status |
| --- | --- | --- |
| 001 | Parameter/Assumption schema freeze + Requirement record | implemented (pending review) |
| 002 | Local route smoke matrix + routing eval set | implemented (pending review) |
| 003 | ESCALATE-CONFIRM-0: external escalation proposal + confirm | implemented (pending review) |
| 004 | Tiered PR review: cheap-tier (GLM/DeepSeek) loop + A/B, frontier pre-merge only | implemented (pending review) |
| 005 | BLUECAD CAD adapter MVP (GeometrySpec v0, build123d, Tier 0–1 validation) | implemented (pending review) |
| 005b | BLUECAD remaining part-kind builders (parametric stubs) | implemented (pending review) (after 005) |
| 006 | BLUECAD workbench: 3D viewer + validation report + attempt history | implemented (pending review) (after 005, 010) |
| 006b | BLUECAD parametric variants (sliders → deterministic rebuild) | ready (after 006) |
| 006c | BLUECAD workbench UX pass (archive, malformed detail, promote, retry) | implemented (pending review) (after 006) |
| 007 | BLUECAD tool registry, health checks, CI license-boundary gate | implemented (pending review) |
| 008 | BLUECAD Gmsh mesh adapter (subprocess, physical groups, quality gate) | implemented (pending review) (after 005, 007) |
| 009 | BLUECAD CalculiX FEM adapter (static v0) + ResultSummary + Tier 3 | implemented (pending review) (after 008) — adapter has no call site in routes/loop yet |
| 010 | BLUECAD AI loop v0 (L1 generate → build → validate → repair) | implemented (pending review) (after 005) |
| 015 | PROVIDER-GW-1: provider gateway v1 | implemented (stage 1; completed by 018) |
| 016 | RUNNER-EXT-1: scoped runner extension for BLUECAD L2 | ready |
| 017 | Autonomous three-tier review: cheap → senior (GLM) → expert (Claude) | implemented (pending live smoke) (after 004) |
| 018 | PROVIDER-GW-2: cap enforcement, fallback execution, Scaleway retirement | implemented (pending review) (after 015) |
| 040 | MEMORYSTORE-0: AI-proposal write boundary for existing engineering records | ready |
| 041 | DECISION-CAPTURE-0: structured record proposals from AI task responses | ready (after 040) |
| 042 | CONTEXT-PACK-1: deterministic, budgeted, inspectable context packs | ready |
| 043 | CALC-1: runner extension for small engineering calculation scripts | ready (after 016 is merged, and after 040) |
| 044 | EVIDENCE-BRIDGE-1: typed evidence records for simulation/validation outcomes | ready (after 042 is merged) |

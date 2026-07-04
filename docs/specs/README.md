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
| 001 | Parameter/Assumption schema freeze + Requirement record | ready |
| 002 | Local route smoke matrix + routing eval set | ready |
| 003 | ESCALATE-CONFIRM-0: external escalation proposal + confirm | ready |
| 004 | Tiered PR review: cheap-tier (GLM/DeepSeek) loop + A/B, frontier pre-merge only | ready |
| 005 | BLUECAD CAD adapter MVP (GeometrySpec v0, build123d, Tier 0–1 validation) | ready |
| 010 | BLUECAD AI loop v0 (L1 generate → build → validate → repair) | ready (after 005) |
| 015 | PROVIDER-GW-1: provider gateway v1 | ready |

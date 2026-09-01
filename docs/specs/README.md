# Work-item specs

Each file `NNN-<slug>.md` is one implementation slice, normally sized for one reviewable implementation branch and pull request. Specs are written from current repository authority and executed by AI coding agents under `AGENTS.md` and `../AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`.

The live status and roadmap are maintained only in [`STATUS.md`](STATUS.md). Individual spec files define scope, acceptance criteria, tests, and non-goals; legacy `Status:` lines inside those files are not authoritative.

## Execution workflow

1. Read [`STATUS.md`](STATUS.md). Pick a `ready` spec only after confirming all hard dependencies are `merged` and no active PR overlaps the same files or runtime boundary.
2. Read `../../AGENTS.md`, `../AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, the selected spec, and its readiness record from exact SHAs.
3. Create the implementation branch `spec/NNN-<slug>` and set the registry row to `in_progress` when implementation begins.
4. Verify the spec's "Files likely touched" list against current code before writing. Specs can become stale. If code reality conflicts with the spec, identify the exact conflict and resolve it through the authority hierarchy rather than guessing.
5. Implement within scope. Acceptance criteria and non-goals are binding.
6. Run the test gate in `AGENTS.md`, `python scripts/check_spec_status.py --self-test`, and all spec-specific gates.
7. Open one implementation PR with `**Spec gate:** implementation NNN`, set the row to `in_review`, and add the implementation PR number. CI checks row presence, status/PR alignment, and merged hard dependencies.
8. Record material deviations, decisions, and deferred non-blocking findings in the PR or the canonical post-beta backlog defined by the execution protocol. Do not create duplicate live status lists.
9. Handle review findings on the same branch. Reproduce or trace each finding against the exact head and classify whether it is blocking, non-blocking, resolved, superseded, or unsupported.
10. Merge only under the exact-head gate in `AGENTS.md` and the execution protocol. After merge, verify `master` and reconcile the registry row to `merged` immediately.

A PR that only creates or revises a spec declares `**Spec gate:** definition NNN`; the row stays `planned`, `blocked`, or `ready` and its implementation PR column remains `—`. Unnumbered infrastructure or process work declares `**Spec gate:** N/A`.

Model and automated reviews are advisory evidence. Passing self-authored tests or receiving a model verdict does not change status by itself. The assigned technical merge owner may merge autonomously only after exact-head deterministic gates, required proof, scope validation, and closure of current blocking findings. GitHub auto-merge remains prohibited.

### Post-134 delivery and material-review amendment — 2026-09-01

After `134 MERGE-AUTHORITY-HARDENING-1` is merged and mechanically reconciled, the maintainer's current scheduling preference is **Coding → Knowledge → Development**, not unrestricted multi-lane implementation. This is scheduling policy only: `STATUS.md`, dependencies, accepted specs/readiness, and security/authority gates still decide whether work is executable. Before Coding starts, complete the maintainer-directed bounded post-134 repair gate. Then execute Coding `118 → 119 → 120 → 123 → fresh Hermes V1 re-derivation/release gate`, Knowledge `113 → 114 → 115 → 121`, and Development `116 → 117 → 122`. If the preferred next item is still `planned`, carry that same item through its normal definition/full-spec/readiness/STATUS authorization rather than jumping lanes.

Repository delivery uses **parallel analysis, serial authority**: the four ChatGPT builders may perform read-only analysis concurrently, but there is one authority-bearing lifecycle/implementation front, one active writer, and one current implementation branch/PR at a time. Builders adopt unfinished work rather than opening competing fronts.

Every material implementation PR, and every material change to architecture gates, CI/workflows, security/egress/provider/credential boundaries, merge/authority enforcement, canonical ownership, or repository-development authority, requires one independent exact-head semantic review before merge unless a narrower fresh canonical rule explicitly supersedes it. Claude is primary. A green Claude/`Manual Expert Review` workflow proves execution only; the actual exact-head semantic verdict/findings must be retrieved. If Claude terminates in failure/error/timeout, or terminates successfully without a trustworthy consumable semantic verdict, request exactly one manual Codex review on that same head immediately via top-level `@codex review`, unless a current-head Codex request/result already exists. Do not dead-wait or re-enable automatic Codex review on every push. ChatGPT adversarial self-review remains mandatory for material diffs but is supplementary when ChatGPT implemented or materially repaired the patch. Any head mutation invalidates affected review evidence.

## Status values

- `planned`
- `blocked`
- `ready`
- `in_progress`
- `in_review`
- `merged`
- `cancelled`

Definitions and update rules live in [`STATUS.md`](STATUS.md). Do not recreate a second live index in this file, the root README, strategy documents, architecture prose, chat handoffs, or individual specs.

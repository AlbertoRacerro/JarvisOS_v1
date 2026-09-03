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

Repository delivery uses **serial ChatGPT mutation authority**: there is one authority-bearing lifecycle/implementation front and one active A/B/C/D writer at a time. A builder that observes another enabled A/B/C/D `[BUSY <UTC>]` lease younger than the canonical staleness window exits promptly without helper-mode analysis, ordinary Coordination Bus production, or shared-authority mutation. Fresh GitHub/PR state is the durable continuation surface; unfinished authorized work is adopted rather than duplicated.

Every material implementation PR, and every material change to architecture gates, CI/workflows, security/egress/provider/credential boundaries, merge/authority enforcement, canonical ownership, or repository-development authority, requires one independent exact-head semantic review before merge unless a narrower fresh canonical rule explicitly supersedes it. Claude is primary. A green Claude/`Manual Expert Review` workflow proves execution only; the actual exact-head semantic verdict/findings must be retrieved. If Claude terminates in failure/error/timeout, or terminates successfully without a trustworthy consumable semantic verdict, request exactly one manual Codex review on that same head immediately via top-level `@codex review`, unless a current-head Codex request/result already exists. Do not dead-wait or re-enable automatic Codex review on every push. ChatGPT self-review may supplement this gate but never substitutes for the required independent reviewer when ChatGPT authored or materially repaired the candidate. Any head mutation invalidates affected review evidence.

### Pipeline V3.2 review convergence and bounded completeness — 2026-09-03

For material reviews, accepted scope is a closed delivery target rather than permission to search for semantic completeness. A finding blocks the current PR only when fresh evidence demonstrates at least one of: an explicit accepted requirement/invariant or frozen fixture is violated; a concrete current first-party path inside accepted scope bypasses the intended invariant; the current diff introduced a concrete regression within accepted behavior; or a material P0/P1 correctness/security defect exists in behavior the PR changes. Reviewer severity or architectural preference alone does not create scope.

For one causal mechanism, perform one bounded sibling sweep across directly analogous current in-scope surfaces before the next head mutation and batch qualifying siblings when safe. Do not generalize into speculative frameworks, broad refactors, hypothetical future callers, language-semantic completeness, or unrelated hardening. Concrete valuable out-of-scope P2/P3 findings are `PARK` and non-blocking; vague, cosmetic, preference-only, or speculative findings are `DROP`. When accepted scope is satisfied and no concrete material blocker remains, the semantic verdict is `APPROVE`.

`Manual Expert Review` binds review evidence to the exact current PR head. Before invoking Claude it requires exact-head success from deterministic `backend` and `evidence` checks, deduplicates previously validated Claude review evidence for the same SHA, and fails closed unless the current review materializes a structured exact-head verdict/findings marker. Workflow success without that marker is not semantic approval. The workflow never manages review labels, so label handling cannot become a review loop.

The former ordinary Coordination Bus V2 helper/workpack production model is retired by V3.2. Existing Bus artifacts remain historical, non-authoritative provenance only. A BUSY-contended builder does not publish a helper workpack or perform duplicate analysis; it exits so the active writer remains the single mutation/continuation owner. Active/recent PR state, exact Git state, deterministic checks, reviews, and canonical repository files are the continuation record.

## Status values

- `planned`
- `blocked`
- `ready`
- `in_progress`
- `in_review`
- `merged`
- `cancelled`

Definitions and update rules live in [`STATUS.md`](STATUS.md). Do not recreate a second live index in this file, the root README, strategy documents, architecture prose, chat handoffs, or individual specs.

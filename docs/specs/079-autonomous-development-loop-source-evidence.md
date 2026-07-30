# Spec 079 source evidence — AUTONOMOUS-DEVELOPMENT-LOOP-0

**Evidence status:** repository-pinned planning evidence.

**Pinned baseline:** `64d598ef99f6dcd6f5afe7caec7a1e7062f78c45`

**Inspection date:** 2026-07-30

This file supports the 079 planning kernel. It is not a second live roadmap, an implementation contract, or a readiness decision. `docs/specs/STATUS.md` remains authoritative for state and priority.

## Evidence labels

- `REPO_VERIFIED`: directly read from the pinned repository tree.
- `PR_VERIFIED`: directly read from GitHub pull-request metadata or discussion.
- `INFERENCE`: bounded architectural conclusion derived from cited verified facts; not an implemented capability.
- `OPEN_DECISION`: must be resolved before a full spec or readiness promotion.

## Evidence map

| ID | Label | Source locator | Verified fact / bounded conclusion |
| --- | --- | --- | --- |
| RT-01 | REPO_VERIFIED | `docs/specs/STATUS.md`, opening rules and status ladder | `STATUS.md` is the single live source of truth. Definition-only PRs do not occupy `Implementation PR` and do not move a row to `in_review`; implementation requires the backlog row → kernel → full spec → implementation ladder. |
| RT-02 | REPO_VERIFIED | `docs/specs/STATUS.md`, `Maintainer operating mode — one active front` | Only one product or implementation front may be active. Frozen work remains `planned`; restart requires an explicit maintainer decision and fresh verification from current `master`. |
| RT-03 | REPO_VERIFIED | `docs/specs/STATUS.md`, maintainer operating mode | The maintainer normally reviews weekly. Between reviews, escalation is reserved for a human decision, security problem, or budget overrun. |
| RT-04 | REPO_VERIFIED | `AGENTS.md`, `Review authority` | Automated/model review is optional and advisory. Deterministic gates plus the human maintainer own merge authority. |
| RT-05 | REPO_VERIFIED | `AGENTS.md`, external review workflow rules | Manual review workflows may not change tier/readiness labels, invoke or mention Codex, dispatch another tier, push, or merge. |
| RT-06 | REPO_VERIFIED | `AGENTS.md`, merge boundary | Agents may not merge their own PRs or enable auto-merge. PRs stop for the maintainer. |
| RT-07 | REPO_VERIFIED | `AGENTS.md`, model-finding handling | Findings must be reproduced or precisely traced. Genuine defects are fixed on the same branch; false findings require an evidence-backed rebuttal. |
| RT-08 | REPO_VERIFIED | `AGENTS.md`, `Codex is explicit-only` | No workflow automatically sends fix requests. Codex action requires an explicit maintainer request and still cannot merge, force-push, delete branches, or change secrets without authority. |
| RT-09 | REPO_VERIFIED | `AGENTS.md`, implementing-agent autonomy | Within an assigned slice an agent may continue reversible inspection, implementation, tests, diagnosis, and evidence collection, but must stop at external spending, destructive/irreversible actions, secret changes, paid workflow dispatches, and merge. |
| RT-10 | REPO_VERIFIED | `docs/specs/STATUS.md`, row 022 | The bounded same-branch Codex actuator is retained only for explicit maintainer-requested work; no workflow dispatches it automatically. |
| RT-11 | REPO_VERIFIED | `docs/specs/STATUS.md`, rows 017, 019, 020 | The historical automatic review chain is now manual/advisory, while Pipeline doctor is cancelled because the automatic review/fix pipeline was removed. |
| RT-12 | PR_VERIFIED | PR #198 metadata; `docs/specs/STATUS.md`, row 077 | PR #198 is merged as commit `64d598ef99f6dcd6f5afe7caec7a1e7062f78c45`, but the pinned registry still says `in_review`; the merge-owner update is overdue and must be reconciled. |
| RT-13 | REPO_VERIFIED | `docs/specs/078-pbr-modeling-0.md`; `docs/specs/STATUS.md`, row 078 and maintainer freeze | 078 is a planning kernel and remains `planned`. No full-spec promotion or implementation is authorized by its definition PR. |
| RT-14 | REPO_VERIFIED | `docs/specs/STATUS.md`, current priority item 8 | The priority text still says to implement ready 077 even though #198 is merged; current priority must be reconciled rather than treated as authority to reimplement 077. |
| RT-15 | PR_VERIFIED | PR #198 history | S3 required many exact-head gate/review/fix rounds. GitHub retained commits, checks, comments, and review threads, but no single canonical run record joined authorization, current head, review round, finding disposition, and next action. |
| RT-16 | INFERENCE | RT-01 through RT-15 | The missing capability is durable authorization/continuation state across sessions, not another coding model or another product orchestrator. |
| RT-17 | INFERENCE | RT-04 through RT-11 | Any automatic review/fix implementation would conflict with current governance and therefore requires an explicit later `AGENTS.md` amendment plus readiness decision; a planning kernel alone cannot authorize it. |
| RT-18 | INFERENCE | RT-01, RT-02, RT-06, RT-09 | A safe dispatcher must bind spec, scope, branch, exact head, actor role, evidence, and next action, and must stop at merge and other maintainer-owned boundaries. |
| RT-19 | OPEN_DECISION | 079 planning kernel §7 and §11 | Choose GitHub Actions, a GitHub App, or a maintainer-owned local dispatcher as the primary host, with explicit permission, replay, secret, availability, and cost analysis. |
| RT-20 | OPEN_DECISION | 079 planning kernel §5.1, §8, §11 | Choose the canonical GitHub-owned append-only/tamper-evident state representation and closed schemas. |
| RT-21 | OPEN_DECISION | 079 planning kernel §5.5 and §11 | Freeze the exact negative-review/fix/re-review state machine, finding dispositions, maximum rounds, and false-positive evidence rule. |
| RT-22 | OPEN_DECISION | 079 planning kernel §5.8 and §11 | Define authorization, content exposure, accounting, and credential custody for GitHub-hosted external models; do not claim JarvisOS 059b automatically governs them. |
| RT-23 | OPEN_DECISION | 079 planning kernel §5.9 and §11 | Define leases, concurrency, webhook/scheduler replay handling, idempotency keys, and branch/head replacement semantics. |
| RT-24 | OPEN_DECISION | 079 planning kernel §10 and §11 | Define an isolated offline test harness and disposable real-tool proof that cannot mutate `master`, production settings, branch protection, live secrets, or paid models. |

## Current capability boundary

### Present

- canonical spec state and priority in `STATUS.md`;
- bounded autonomy inside one assigned slice;
- GitHub branches, PRs, checks, comments, and review threads as raw evidence;
- deterministic CI and real-tool workflows;
- manually requested advisory reviews;
- explicit same-branch Codex actuation;
- a human-owned merge boundary.

### Not present or not authorized

- one canonical durable development-run authority;
- automatic cross-session resume;
- automatic review dispatch;
- automatic Codex fix dispatch;
- closed finding/fix/re-review state machine;
- branch lease/concurrency authority;
- external-model spend and content-exposure authority for GitHub-hosted agents;
- automatic merge or agent merge.

## Architectural implications

1. Reusing GitHub as the coordination substrate is plausible because the required raw evidence already exists there, but GitHub artifacts must be joined by an explicit authority record rather than inferred ad hoc.
2. A sticky issue comment or mutable dashboard alone is insufficient authority because edits can erase history and head-bound evidence can become stale.
3. Append-only events plus a derived snapshot are the leading representation, but the exact GitHub primitive remains an open decision.
4. The implementing and reviewing roles must remain distinct even if both are model-backed.
5. Review cleanliness cannot imply merge permission.
6. Current explicit-only rules are safety constraints, not implementation inconveniences to bypass.
7. The weekly-review objective favors honest inactivity, bounded escalation, and a digest over repeated liveness messages or provider calls.

## Evidence limitations

- This planning pass did not execute GitHub Actions, Codex, Claude, or another model.
- It did not inspect private vendor implementation details for GitHub-hosted coding agents.
- It did not prove webhook, scheduler, lease, permission, or cost behavior.
- It did not select a hosting architecture.
- It did not amend current governance.
- PR #198 history demonstrates coordination burden but is not a performance benchmark or proof that a particular autonomous architecture is safe.

These limitations block full-spec promotion, not the definition-only S4 PR.

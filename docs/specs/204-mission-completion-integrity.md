# 204 — Evidence-backed mission completion

State: **ready** (live state in [`STATUS.md`](STATUS.md)). The maintainer's urgent [issue #860](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/860), as narrowed on 2026-10-21, authorizes this repair before any phase of [issue #859](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/859). Depends on 201 and 203.

## Outcome

The single spec 201 owner advances an engineering mission task only when independent, current evidence satisfies that task's accepted completion contract. A provider's successful exit, `RELAY_STATUS propose_done`, model assertion, or durable checkpoint cannot by itself mark engineering work complete. An unfinished task remains resumable without advancing the queue. A genuine block is durably held, and uncertain remote evidence fails closed. Legitimate non-PR tasks can use an appropriate objective contract.

Existing mission definitions stay immutable. The repair must safely cover missions already submitted without a `check`, including `m-20261021T125949Z-2e0739`; it must not interrupt an active turn, create a second coordinator, bypass `effects_uncertain`, or silently reinterpret a previous complete label as verified delivery. Use the existing mission store, journal, ledger, GitHub and registry. Add only the minimum deterministic check or queued-only priority operation demonstrated necessary.

Amended 2026-10-23 (directive `L20261022220755-8248`). A claimed finish that the check does not confirm (unsatisfied or unreadable evidence), and a missing or unknown `RELAY_STATUS`, are durable checkpoints. The task stays pending and is resumed, bounded by `MAX_TASK_CHECKPOINTS`, after which it holds `task_checkpoint_limit`. A task with no completion check still holds `task_check_failed` on a claimed finish, and `blocked` still holds `task_blocked`. Nothing completes without passing its check.

## Acceptance

1. A deterministic regression reproduces unchecked false completion and shows that an unsupported or unverified claim cannot advance a task. Objective evidence allows completion; a checkpoint keeps it pending. Restart, replay, bounded retries, queue order and holds remain safe.
2. A supervised isolated multi-turn mission stays pending across a checkpoint, completes only after its required deliverables are independently verified, and fails closed when remote evidence cannot be read.
3. Audit only automatically generated spec 203 roadmap cycles from activation at `2026-10-21T10:24:42Z` until this fix. For each settled cycle, record intended work, accepted evidence, actual done/partial/missing/inconclusive state, exact PR/SHA/tests/paths and remaining action. Recover and queue specific unfinished authorized deliverables before #859 Phase A, without duplicates or edits to immutable mission files.
4. Run focused regressions, baseline deterministic gates, proportional independent review of the control-plane change, exact-head CI and remote merge verification. Reconcile `STATUS.md` after merge.

The monitor, Coding integration and local-model evaluation in issue #859 remain separate subsequent work. No new scheduler, session store, provider authority, credential handling or branch-protection authority is granted.

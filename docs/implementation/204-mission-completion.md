# Evidence-backed mission completion — evidence, 2026-10-21

PR: [#865](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/865), under issue
[#860](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/860).
Baseline: `cd9ef4610c4f52086f9c0734cc6ad13c7b0a3347`.

## Defect

The spec 201 owner advanced a mission task on any successful provider turn
whose task had no `check`. Production mission `m-20261021T125949Z-2e0739`
(issue #859 phases A–C) recorded 3/3 done while Relay reported `continue`,
`blocked`, `blocked`. It had no `completed_at` when the owner was stopped, but
the pre-204 owner would have completed it on its next start.

## Implemented (`scripts/relay_continuity.py`)

- **Execution is not delivery.** A turn's final `RELAY_STATUS` only routes it:
  `continue` is a checkpoint (the task stays pending; at most
  `MAX_TASK_CHECKPOINTS` = 12, counted durably across restarts), `blocked` holds
  `task_blocked`, and an unknown status holds `task_report_unverified`.
  `propose_done` advances only when the task's independent read-only check
  passes. A missing check, a failed check, or unreadable evidence holds
  `task_check_failed`.
- **Contracts.** `pr_merged` and `path_exists` as before. `spec_merged` reads
  `docs/specs/STATUS.md` from GitHub master, never the local checkout: the row
  must be `merged` and every PR linked in it merged. It exists because
  engineering tasks rarely know their PR number in advance. `coordinator_cycle`
  is for roadmap cycles: it settles on `propose_done` or `blocked` while the
  remote heads are readable, and records `cycle_settled`, not verified delivery.
  `submit` refuses it, so only the owner's roadmap step creates it.
- **Legacy missions.** Definitions are never edited. In an unfinished mission,
  tasks counted before 204 (`legacy_unverified`) are reopened from the first
  one on, and the history is kept under `reopened`. This happens before the
  owner runs the mission, and again after a restart settles a pending attempt.
  `contract` attaches a check to a pending task whose definition has none,
  while the owner is stopped. Finished missions are never rewritten. `missions`
  shows each task's outcome (`verified`, `cycle_settled`,
  `maintainer_attested`, `legacy_unverified`) and a `verified` flag.
- **No duplicate work.** After a release, a task whose last turn already
  reported done is re-checked before any relaunch.
- Runbook: `docs/implementation/relay-continuity-runbook.md`, "Supervised
  missions" and the hold table.

## Acceptance

1. **Deterministic regression.** These tests are in
   `backend/tests/test_relay_continuity.py`:
   - `test_unchecked_mission_cannot_complete_on_successful_provider_turn`;
   - `test_204_legacy_counted_tasks_are_reopened_not_completed`, which uses the
     2e0739 shape;
   - `test_204_legacy_completion_is_reopened_after_a_pending_final_task_settles`;
   - `test_204_completed_legacy_mission_is_not_reinterpreted_as_verified`;
   - `test_204_lying_provider_then_merged_evidence_completes_without_relaunch`;
   - `test_204_relay_status_routes_but_never_completes`;
   - `test_204_unreadable_remote_evidence_fails_closed`;
   - `test_mission_checkpoint_stays_pending_until_check_passes`;
   - `test_204_checkpoint_bound_survives_restarts`;
   - `test_204_contract_attaches_only_to_pending_unchecked_tasks`;
   - `test_204_check_task_spec_merged_reads_the_remote_registry`;
   - `test_204_roadmap_cycle_settles_on_blocked_as_unverified_cycle`;
   - `test_204_submit_refuses_coordinator_cycle_contracts`.

   The existing restart, adoption, crash-while-settling, queue-order, hold,
   release and roadmap tests still pass. `spec_merged`, `coordinator_cycle` and
   `pr_merged` were also run read-only against live GitHub: 203 and 202 pass;
   204 is "ready" and 165 "in_review", so both fail; #861 is OPEN.
2. **Real isolated multi-turn mission.** The run is recorded in
   `~/jarvis-control/work/evidence/204-e2e/RESULT.md` (head `39888ef9`, real
   Claude turns, owner under `bwrap --unshare-pid`):
   - A checkpointed, stayed pending, claimed done early and was refused, then
     completed only once the deliverable existed.
   - B failed closed on unreadable GitHub evidence, then verified PR #854 merged
     without relaunching the provider.
   - C, a pre-204-shaped record, was reopened rather than completed, held for
     want of a contract, and was verified after `contract` and `release`.

   The production control root and its STOP were not touched.
3. The spec 203 audit follows the merge (issue #860 Stage 2).
4. Review and CI: an independent Codex read-only review of `39888ef9` found one
   P1, legacy migration bypassed by a pending final task. It was fixed in
   `3240baf4` with a regression test. Exact-head CI and the re-review are
   recorded on the PR.

Known, pre-existing and out of scope: three spend-cap tests fail on
`origin/master` as well, between 23:50 and 00:00 Europe/Rome, because their
fixture text says "resets 11:50pm" and the reset is resolved against the real
clock.

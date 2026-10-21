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
3. **Spec 203 cycle audit (below).**
4. **Review and CI.** An independent Codex read-only review of `39888ef9`
   found one P1: legacy migration was bypassed when a pending final task
   settled. It was fixed in `3240baf4` with a regression test, and the re-review
   of `3240baf4` passed with no P0/P1. Exact-head CI on `26dab644` passed (9/9
   checks). Merged at `23229b96bb2f652d905b810c692497112051274e` with a head
   CAS.

Known, pre-existing and out of scope: three spend-cap tests fail on
`origin/master` as well, between 23:50 and 00:00 Europe/Rome, because their
fixture text says "resets 11:50pm" and the reset is resolved against the real
clock.

## Spec 203 roadmap cycle audit (acceptance 3)

Scope: missions that the spec 203 roadmap generated automatically between its
activation (`2026-10-21T10:24:42Z`, directive `L20261021095156-016b`) and this
fix. `roadmap.json` records three cycles (`last_mission` is cycle 3). No later
cycle was submitted, because the owner's queue still held the manual #859
mission. Excluded: host acceptance mission `m-20261021T093535Z-5613b2` and
manual mission `m-20261021T125949Z-2e0739`, which is not roadmap-generated.
Under 204 the owner would reopen its 3/3 pre-204 count and resume Phase A, which has no check, so it needs a maintainer disposition (cancel and resubmit with contracts, or attach contracts) before the owner restarts. All three cycle records are
`legacy_unverified`; they are left unchanged and judged here from evidence.

Evidence was read on 2026-10-21/22 from GitHub (PR state, merge commit, exact
head and check rollup), `origin/master` `STATUS.md`, the Relay `output.jsonl`
and `state.json` of each session, and the proof files named below.

| Cycle / mission | Intended work (as chosen by the cycle) | Acceptance evidence | State | Remaining action |
| --- | --- | --- | --- | --- |
| 1 `m-20261021T120448Z-7bcca2` (sessions `8b8b6f` Claude quota, `849096` Codex `propose_done`) | Deliver spec 174 PBR solar optics T2 | [#842](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/842) merged `297c0489` at head `e4c7ef89`, 7 checks green. Same-origin Chromium proof on `e4c7ef89` (`~/jarvis-control/work/evidence/174/README.md`, screenshots, T1/T2 run ids). Kernel evidence `backend/tests/evidence/174_optics_t2_kernel.md`. [#857](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/857) reconciled (`42ce1a84`); STATUS 174 `merged` | done | none |
| 2 `m-20261021T121127Z-a7d15a` (`2863fb` Codex `propose_done`) | Recover and deliver spec 202 operator readability | [#849](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/849) merged `37e3a070` at head `e53b2c65`, checks green. Real Chromium before/after matrix of 16 captures at that head (`docs/implementation/202-operator-readability.md`). [#858](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/858) reconciled (`a5a7f9bd`); STATUS 202 `merged` | done | none |
| 3 `m-20261021T122457Z-5ae2a9` (`5ddc9f` Claude, quota at end; `67db92` Codex `propose_done`) | Recover unpushed lanes k173 (spec 173) and k165 (spec 165) | **173:** [#862](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/862) merged `666ce397` at head `982d2fd5`, 10 checks green. Real-Chromium golden workflow at product head `842fce79`; `842fce79..982d2fd5` changes only `docs/`. [#863](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/863) reconciled (`83ea487b`) | 173 done | none |
| | | **165:** [#861](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/861) is a draft at `3a3d47ad` with 10 checks green; backend tests and real-Chromium GUI proof are recorded. The spec-required WSL host proof (real `explorer.exe`) was **not run**: the sandbox has no `/mnt/c`, `wslpath` or interop. STATUS 165 `in_review` is truthful. The cycle's `RELAY_STATUS` claimed `remaining_work: []`, but its message disclosed the checkpoint. | 165 partial | Maintainer: run `scripts/165-print-handoff-host-proof.py` on the WSL host outside the sandbox (ledger blocker `L20261021131537-4009`), then a coordinator records it, updates #861 to master (21 commits behind) and merges/reconciles. |

Remediation disposition: no remediation mission is queued. The only
unfinished deliverable needs a host action that the sandboxed owner cannot
perform. A mission would only hold, or invite an invented proof. Nothing was
duplicated, and no mission file was edited.

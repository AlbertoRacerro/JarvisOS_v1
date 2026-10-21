# 203 — Roadmap continuation through the mission owner

State: **in_review** (live state in [`STATUS.md`](STATUS.md)). Depends on 201. Definition and readiness were granted together by the maintainer directive of 2026-10-21 (ledger `L20261021095156-016b`). That directive asks for the smallest planner-to-mission integration on the spec 201 control plane. Intelligent prioritization stays separate from deterministic execution, and `STATUS.md` stays the single backlog.

## Outcome

The maintainer says "Continue developing JarvisOS according to the roadmap" once and leaves. From then on, the spec 201 owner keeps running coordinator cycles. Each cycle is one ordinary supervised mission, and its turn runs the Generic Frontier Builder Contract (`docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` §1) against fresh GitHub, `STATUS.md` and ledger state. The turn chooses, prepares, implements, reviews, merges and reconciles the highest-value authorized work. The owner then decides deterministically whether to submit the next cycle. Provider failover, restart adoption, reconciliation and holds are the existing 201 behavior, unchanged.

## Division of authority

- **Coordinator turn (intelligent).** Selects work from `STATUS.md`, recovers existing PRs, worktrees and claims before creating new ones, and obeys recorded maintainer directives and holds. Its authority is that of the Frontier Coordinator under `AGENTS.md`; the cycle's text adds none. It never submits missions or changes the roadmap state.
- **Owner (deterministic).** It has no notion of specs or priorities. It submits a cycle only when roadmap mode is on and not paused, and every mission in the queue has finished. Maintainer-submitted missions therefore always go first, and there is at most one cycle at a time. It pauses roadmap mode, and notifies, when:
  - the cycle's final turn reported `RELAY_STATUS` `blocked` (the coordinator needs a maintainer decision or found no authorized work);
  - three consecutive completed cycles left the remote branch heads (`git ls-remote --heads origin`) unchanged (`no_progress`);
  - a cycle mission was cancelled.

  If the remote refs cannot be read, no cycle is submitted until they can. A held mission blocks the queue, as in 201, so no cycle is submitted past a hold.
- **Entry points.** `relay_continuity.py roadmap start --authority <directive>`, `roadmap stop --note …` and `roadmap status`. The coordinator in a Relay REPL records the maintainer's sentence as a directive and runs `roadmap start`. The owner starts once the REPL exits and frees the coordinator lease; the 201 REPL independence is unchanged.

## Included repair

Spec 201 host acceptance defect A: the owner counted its own sandbox PID-namespace init (cwd = checkout) as live work, so an owner (re)started inside a mission's work window waited on itself and then held. Continuous operation across restarts needs this fixed. The owner's ancestry exclusion now includes PID 1 of its namespace.

## Non-goals

- No change to the coordinator lease or REPL independence. No keystroke injection.
- No model-generated mission files and no mission submission from inside a turn.
- No change to spec 079. Its continuation mode is `OFF` and must stay `OFF` while roadmap mode is on, because `EXECUTE_NO_MERGE` would add a second writer on the same PR.
- No governance-file edits, new daemon, queue, store or credential.
- Defect B (a unit restart kills a running turn) is not fixed here. Recovery stays the 201 crash settlement and reconciliation.
- Historical holds, Lumen v2.1 and other maintainer reservations stay as recorded in the ledger. The owner never releases a hold.

## Acceptance

1. Unit tests cover start, stop and status, submission only on an empty queue, each pause rule, waiting on unreadable remote refs, and the PID 1 exclusion.
2. A real isolated run on a no-remote clone with a local bare `origin`, an isolated ledger and control root, with the owner under the unit's process model:
   - `roadmap start` produces a real coordinator cycle that does the directive's work and pushes.
   - The next cycle is submitted automatically.
   - A cycle that reports `blocked` pauses roadmap mode.
   - A restart of the owner during a cycle does not wait on its own namespace init.
3. Production: roadmap mode enabled under the maintainer's directive, with the first production cycle observed or explicitly reported as pending the release of the REPL lease.

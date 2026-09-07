# Post-112 controlled parallel delivery profile

Status: canonical concurrency profile
Authorized: 2026-08-28
Refactored: 2026-09-07 — concurrency mechanics only

This file defines **only the concurrency and shared-writer mechanics** used after spec 112 is merged.

Engineering philosophy, model roles, review policy, lifecycle compression, convergence, merge criteria, and maintainer interruption rules live in `AGENTS.md` and `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`. Do not duplicate them here.

`docs/specs/STATUS.md` remains the sole live authority for work state, dependencies, priority, and implementation-PR association. This file is not a roadmap and contains no permanent spec ordering.

## 1. Activation

This profile is active only when fresh exact `master` shows `112 PROJECT-KNOWLEDGE-CORE-1` as `merged`.

Before that condition, ordinary serial delivery applies.

After activation, parallelism is permitted only where the acting Frontier Coordinator has enough evidence that the concurrent work does not create unsafe shared state/authority races.

A conflict serializes only the conflicting work. It does not require unrelated disjoint work to stop.

## 2. Scheduler topology

The normal automation topology is four interchangeable frontier-builder scheduler slots, currently staggered at:

- A — `:00`;
- C — `:15`;
- B — `:30`;
- D — `:45`.

The letters are scheduling slots, not architecture roles and not model identities.

Any sufficiently capable model/session may execute a slot if it can read canonical repository state and use the required deterministic capabilities.

## 3. Global shared-writer mutex

Only one frontier scheduler may own GitHub/shared-authority mutation at a time.

Before the first shared mutation:

1. inspect live A/B/C/D automation titles;
2. if another enabled builder has `[BUSY <UTC-ISO>]` less than **20 minutes** old, do not perform shared mutation;
3. otherwise rename only the current slot to `<BASE_TITLE> [BUSY <UTC-ISO>]`;
4. immediately inspect the topology again;
5. if another fresh BUSY owner is now present, restore the base title and remain non-writer; otherwise the current slot owns the shared writer lease.

A BUSY timestamp at least 20 minutes old is stale coordination evidence and does not prove ownership.

If a run keeps mutation authority for roughly **10 minutes**, refresh its own BUSY timestamp and immediately re-check before another mutation boundary. A resumed/stalled session never relies on an old title as authority.

Always restore the base title on exit, including failure paths.

The automation-title lease is anti-race coordination only. **Exact SHA, current remote state, expected-head CAS, and post-mutation verification remain correctness.**

## 4. What requires shared serialization

Serialize mutations that can collide through common authority or state, including as applicable:

- `STATUS.md` and shared roadmap state;
- merges and merge sequencing;
- shared branches/PR heads;
- common routers/registries;
- migrations/schema sequencing;
- common credentials/provider/egress policy;
- repository-wide workflows/control files;
- shared frontend/backend integration owners;
- any path/state a fresh ownership audit shows is common to active fronts.

The coordinator may make several related shared mutations during one lease when that is the shortest safe path to convergence.

## 5. What may run in parallel

Parallel work is encouraged when it has a real throughput or risk-reduction advantage and the state boundaries are safe.

Examples:

- read-only research and exact-head analysis;
- independent semantic critique;
- browser proof that does not mutate source;
- disjoint implementation in isolated worktrees/branches;
- focused tests on isolated state;
- constrained-worker candidate work;
- planning/readiness analysis for an authorized disjoint front.

Disjointness should be judged by **actual state and authority**, not just filenames. Consider:

- files/modules;
- database/schema/migrations;
- durable stores;
- shared configuration;
- provider/credential/egress ownership;
- Git branch/worktree ownership;
- workflow/control-plane ownership;
- product/domain invariants.

Do not require a formal disjointness essay when the separation is obvious and reversible. Require stronger evidence only when a collision could produce material corruption, authority bypass, or difficult rollback.

## 6. Writer and non-writer behavior

The writer owns the current bounded shared action and should continue until that action reaches a stable durable state rather than relinquishing the lease after every tiny mutation.

A non-writer must not race the shared state. It may:

- inspect fresh evidence;
- perform genuinely independent critique;
- diagnose CI;
- prepare a non-duplicative workpack;
- work in a demonstrably disjoint isolated lane;
- do nothing when additional parallel analysis would only duplicate existing work.

**Doing nothing is better than producing duplicate review noise.** A non-writer is not required to manufacture helper work every wake.

## 7. Isolated worktree/worker principle

Where trusted local or cloud workers exist, isolated worktrees may preserve durable work across sessions and allow disjoint implementation.

A worker's authority is determined by the server/control-plane capability granted to it, not by its model name or prompt claim.

A worker going offline removes only capabilities physically dependent on that worker. It must not globally disable GitHub, hosted CI, cloud review, governance, or other independent lanes.

Dirty/persistent work is not silently migrated between workers. Reconnect/resume revalidates current remote/head state before delivery.

Detailed local-worker behavior belongs to its accepted implementation/specification, not to this concurrency profile.

## 8. Lane selection

Do not encode a historical fixed lane order here.

At each scheduling decision:

1. read fresh `STATUS.md` and current maintainer scheduling directives;
2. identify the highest-value authorized work;
3. continue unfinished work before opening duplicates;
4. use parallel lanes only where dependencies and state/authority boundaries permit;
5. serialize only the shared/conflicting portion.

A `planned` item is still non-implementation authority. Parallelism does not bypass readiness or hard dependencies.

Temporary maintainer priorities should live in the current scheduling directive/automation metadata or canonical live planning state, not become permanent sections of this file.

## 9. Review concurrency

Review behavior follows the execution protocol.

Concurrency-specific rule only:

- independent frontier peers may review a frozen exact head in parallel;
- a moving repair head should have one primary internal review/workpack rather than four duplicate scheduler reviews;
- when a material finding causes mutation, affected old-head reviews no longer certify the new head;
- unrelated evidence remains reusable when its truth was not affected.

The first sufficient qualified review path should be consumed; do not wait for slower duplicate reviewers after the active contract is already satisfied.

## 10. CI and proof waits

A running CI/review/proof job is not a reason to create competing source mutations.

During a wait, use available time only for non-conflicting useful work. Do not poll merely to occupy the session, and do not create speculative future scope because the current gate is slow.

If the current front is genuinely blocked by environment/human evidence, scan fresh authorized disjoint work as described in the execution protocol. Preserve the blocked gate rather than weakening it.

## 11. Conflict handling

When concurrent work collides:

1. stop the conflicting mutation path;
2. determine which work owns the shared boundary from fresh authority/state;
3. preserve recoverable work where practical;
4. rebase/rederive the affected lane against current master/head;
5. keep unrelated lanes running if still independent.

Do not solve a local conflict by creating another queue, store, branch authority, policy file, or coordination framework unless the minimum-necessary test proves it is required.

## 12. Success criterion

This profile succeeds when four scheduler slots provide low reaction latency and useful parallel intelligence **without multiplying writers, duplicated reviews, governance surfaces, or head invalidations**.

The desired operating model is:

`parallel intelligence + isolated disjoint work; serialized shared authority; exact-state verification; rapid convergence`.
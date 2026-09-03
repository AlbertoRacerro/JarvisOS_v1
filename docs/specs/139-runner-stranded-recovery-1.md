# 139 RUNNER-STRANDED-RECOVERY-1

Status: full specification / planning authority

## Purpose

Close the bounded post-134 F8 resilience gap in the existing local Python runner: an abrupt server-process failure after a queued job is claimed can leave the persisted runner job and simulation run indefinitely `running`. Recovery must distinguish genuinely abandoned execution from a still-live child process and must not steal live work.

This is a corrective runner-lifecycle slice, not a lease framework, distributed scheduler, generic process supervisor, sandbox redesign, or new execution engine.

## Derivation evidence

Derived from exact master `6e1d369d936935174d2384c391ee18da5c5ea6df` after spec 138 reconciliation.

Fresh source confirms `backend/app/modules/runner/local_python.py::execute_python_script` still launches the execution owner as a separate Python child through blocking `subprocess.run`. Runner persistence can therefore outlive the server process that claimed the job, while the child has no persisted ownership identity proving whether it is still alive after an abrupt parent failure.

The post-134 F8 workpack established that runner/service claims the persisted runner job and simulation run as `running` before child/filesystem execution, so process death can strand that state. Subsequent bounded revalidation established two material constraints: normal application startup alone is not proof of abandonment, and a backend/data-root lock alone is insufficient because a child may survive the parent, especially on Windows.

## Authority and dependencies

Depends on merged 138 and the existing runner persistence/execution contracts. Implementation authority exists only after an accepted readiness decision and a canonical `STATUS.md` row for 139 is `ready`.

## Required behavior

1. Preserve the current queued-to-running claim semantics unless a smaller causal change is needed to attach execution ownership.
2. Add the minimum runner-specific ownership/liveness evidence required to distinguish a genuinely abandoned `running` execution from a still-live execution child after abrupt server-process death.
3. A normal startup/reload event, a newly started server process, or acquisition of a backend/data-root lock MUST NOT by itself prove a persisted `running` job is abandoned.
4. When execution ownership is provably gone, reconcile the coherent runner-job/simulation-run pair exactly once to an existing terminal state with a deterministic typed interruption/failure reason.
5. Preserve existing rows, artifacts, logs and events; recovery must not delete evidence or fabricate successful outputs.
6. Queued, succeeded and failed jobs/runs remain untouched by recovery.
7. Inconsistent persisted pairs fail closed and deterministically; recovery must not silently rewrite one side into an invented coherent history.
8. A still-live execution child must not be terminalized, reclaimed, or allowed to race a replacement execution against the same output lineage.
9. The losing/original stale owner must be unable to overwrite a recovered lineage after ownership is conclusively gone and recovery has completed.
10. Recovery must be idempotent: a second reconciliation over already recovered terminal state is a no-op.

## Minimum implementation boundary

Implementation may touch only the existing runner execution/persistence/startup surfaces required by the accepted design, expected to include a bounded subset of:

- `backend/app/modules/runner/local_python.py`
- `backend/app/modules/runner/service.py`
- runner persistence/model/migration code only if ownership identity cannot be represented safely with the current schema
- `backend/app/main.py` and/or `backend/app/core/bootstrap.py` only for the final, proven-safe reconciliation hook
- focused runner/startup tests
- normal lifecycle bookkeeping in `docs/specs/STATUS.md`

A schema/migration change is authorized only if readiness confirms it is the minimum mechanism needed for child ownership/liveness. Do not introduce generic leases, heartbeats, distributed locks, a process registry, or a new runner service abstraction merely for completeness.

## Deterministic acceptance matrix

| Case | Expected result |
| --- | --- |
| coherent persisted `running` pair with execution ownership provably gone | terminalized exactly once with deterministic interruption/failure reason; evidence retained |
| same recovered pair on second reconciliation | no-op |
| queued/succeeded/failed pair | untouched |
| inconsistent runner-job/simulation-run state | fail closed deterministically; no invented success/retry history |
| normal supported reload while a runner execution is completing | live job is not recovered or terminalized |
| second supported launcher while the first backend/execution remains live | running row is not mutated merely because another startup path executes |
| abrupt server-process death while execution child remains live | new server does not falsely declare the job abandoned or start competing work |
| abrupt server-process death after execution ownership is conclusively gone | stranded pair becomes recoverable exactly once |
| stale/original execution owner after recovery | cannot overwrite the recovered lineage |

Tests must exercise real process/liveness behavior at the smallest deterministic seam practical; a unit test that only asserts a state-transition helper without proving the live-child/abandoned-child distinction is insufficient.

## Required gates

- focused runner recovery and child-ownership tests
- focused application/startup regression proving the chosen hook executes only under the accepted ownership preconditions
- normal repository CI on the frozen implementation head
- independent exact-head semantic review because this changes production runner recovery/ownership semantics

## Failure modes to prevent

- terminalizing a live job merely because the backend restarted;
- treating a released backend lock as proof that a child subprocess is dead;
- duplicate execution writing into the same run/output lineage;
- orphan children mutating artifacts after a replacement run begins;
- startup/reload repeatedly rewriting terminal history;
- deleting or masking evidence to make stranded rows disappear;
- adding a broad lease/heartbeat/process-supervision framework when a runner-specific ownership proof suffices.

## Non-goals

- no distributed or multi-host runner scheduling;
- no generic process supervisor;
- no generic backend single-instance framework;
- no runner sandbox redesign;
- no unrelated timeout/cancellation API expansion;
- no BLUECAD stale-generation repair (F9);
- no calc-runner artifact/proposal consistency repair (F10);
- no Coding 118+ scope.

## Minimum-necessary test

The repair is acceptable only if the chosen ownership mechanism directly proves the one ambiguity that makes naive startup reconciliation unsafe: whether the execution child that owns a persisted `running` row is still alive. Anything broader than the smallest mechanism and reconciliation needed for that proof requires fresh authority.
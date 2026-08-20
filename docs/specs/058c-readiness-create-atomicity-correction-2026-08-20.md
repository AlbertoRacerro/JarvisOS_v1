# 058c — fresh readiness correction: atomic create freshness boundary

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-runner-freshness-surface-correction-2026-08-20.md`  
Reason: exact-head review of PR #317 proved that a freshness read performed merely "immediately before" persistence still leaves a replacement-vs-create TOCTOU race. A linked Parameter can become stale after that read and before `simulation_runs` / `runner_jobs` are inserted.

This correction is part of the 058c readiness decision. Where it conflicts with earlier readiness records, this file governs. It changes no runtime code and does not promote `058c` from `planned`.

## 1. Failure mode closed

The current guarded create path validates model inputs before persistence and uses `BEGIN IMMEDIATE` only for request-key serialization. Canonical Parameter replacement also mutates SQLite under write ownership. If linked-source freshness is checked outside the write transaction that persists the new run/job, a concurrent replacement can commit between the freshness decision and the inserts. The resulting queued run would carry a source snapshot that was already stale at persistence time.

The phrase "immediately before" is therefore insufficient. Create-time freshness is an integrity boundary and must be atomic with persistence.

## 2. Exact create contract

For every create path whose immutable input snapshot contains one or more `source_parameter_id` bindings:

1. acquire the existing SQLite write transaction used to own creation (`BEGIN IMMEDIATE` or the current equivalent after fresh implementation inspection) **before the final canonical freshness decision**;
2. inside that same transaction, re-resolve each persisted source identity in the same workspace and consume canonical 051 node freshness plus the already-required status/value/unit/domain checks;
3. only if every source is still usable may the transaction insert the new `simulation_runs` and `runner_jobs` rows and their creation events;
4. if any source is stale, superseded, missing, cross-workspace, malformed, or otherwise invalid, roll back and persist **zero** new run/job rows for that create intent;
5. request-key replay/idempotency remains authoritative: an already-existing same-key/same-payload row is reconciled under existing semantics rather than treated as a fresh create. This correction does not authorize rewriting historical snapshots or revalidating a completed replay as though it were a new run;
6. do not hold the write transaction across script execution, provider work, filesystem-heavy work, or unrelated validation. Only the final source-integrity decision, idempotent ownership decision, run/job/event persistence, and commit belong to this atomic boundary.

The required serialization is intentionally narrow. It reuses SQLite's existing writer exclusion against canonical Parameter replacement and does not introduce a lock service, second freshness store, queue coordinator, background worker, or new lifecycle state.

## 3. Allow-list amendment

Implementation may modify only the already-authorized runner create/guarded service path and focused tests as needed to move the **final** canonical linked-source freshness/status resolution into the same existing SQLite write transaction as run/job persistence. Existing flowsheet freshness helpers may be consumed read-only inside that transaction. No new endpoint, persistence table, event family, provider path, frontend freshness authority, or general transaction framework is authorized.

If current helper signatures cannot consume an existing connection without opening a second connection, the smallest connection-aware read helper in the existing canonical freshness module is authorized solely to preserve one-transaction semantics. It must not duplicate freshness logic or create a parallel authority.

## 4. Merge-blocking acceptance

Implementation evidence must prove all of the following:

1. fresh linked source + normal create still persists exactly one simulation run and one runner job;
2. stale/superseded linked source at final create ownership persists zero new run/job rows;
3. a deterministic concurrent test holds a Parameter replacement and runner create against the same workspace/source and proves there is no interleaving in which create commits a snapshot whose source was already stale before that create transaction committed;
4. whichever writer acquires SQLite ownership first has deterministic semantics: create-first may commit a snapshot that was fresh during its atomic create boundary and a later replacement may stale it before execution, where the separately required atomic queued-job claim check blocks execution; replacement-first causes create to fail closed before persistence;
5. request-key concurrent retries still create at most one run/job pair and same-key/different-payload still conflicts under existing authority;
6. the write transaction is released before script invocation and no broader lock is introduced.

The concurrency test must exercise the real create/replacement transaction boundary rather than only unit-testing a helper in isolation.

## 5. Review consequence

The Codex P1 delivered on exact head `c9d2a62aff9d7c0e3ee73be6764fb2c040051605` is valid and blocks that head. This correction closes the specification gap by replacing the earlier non-atomic "immediately before persistence" wording with an explicit same-write-transaction requirement.

All gate/review evidence from earlier heads is stale for merge authority. The new exact head requires fresh deterministic CI and an independent peer/GLM verdict that explicitly checks create-time atomicity together with the already-frozen preview and queued-job-claim freshness boundaries. No further Codex review is authorized for PR #317.
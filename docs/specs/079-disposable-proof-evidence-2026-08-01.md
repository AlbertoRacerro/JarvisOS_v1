# Spec 079 initial disposable proof evidence — 2026-08-01

## Status and authority

This document records the first offline disposable-prototype evidence authorized by the maintainer after merge of PR #207.

It is **partial proof evidence only**. It does not move spec 079 beyond `planned`, does not satisfy readiness, and does not authorize a GitHub App, service, provider call, credentials, repository settings, implementation skeleton, or operational grant.

The prototype was kept outside the JarvisOS repository, used deterministic fake actors only, denied socket access during tests, and made zero live or paid calls.

## Prototype boundary

Prototype name: `jarvisos-079-proof`

Execution form:

- local disposable Git repository, separate from JarvisOS;
- exported and executed again from a clean Git archive without `.git` metadata;
- Python source declares compatibility with Python 3.11 or later;
- observed runtime for this evidence: Python 3.13.5;
- no package installation required for the proof run;
- no GitHub App installation, webhook endpoint, production repository mutation, provider credential, database, queue, or network dependency.

The available ChatGPT GitHub connector cannot create a new repository. The source prototype therefore remains a local disposable artifact rather than durable GitHub evidence. Before readiness, it must be imported into a separately owned proof repository or independently rebuilt and rerun from the recorded contract. This limitation is a blocker to treating the result as final architecture evidence.

## Exact artifact evidence

Prototype source commit inside the local disposable repository:

`66e441cd413684fdd0aff37ef0e9b5904e7ef0ad`

Clean proof bundle SHA-256:

`110dc033342a2f5ad8340f042d115637c2c1db67cf0b83e6de581a5baf75f910`

Evidence file SHA-256 values inside that clean bundle:

- `evidence/proof-report.json`: `49c06061322b73d6d9784c07c41a583d552074764125de513e74197619696c86`
- `evidence/cas-stress-report.json`: `ff2b4387dfb3d140ae8db66d560d179e1f9cba38309c0097601c53f4b4d48644`
- `evidence/proof-summary.md`: `755dbf07ba9579db00d17b86a3305f6c1802dac0c500b9ea4608840f3aea2c0a`

The bundle is retained as a conversation artifact. Its hash is recorded here so later import or reconstruction can be checked byte-for-byte.

## Results

### Unit and conformance proof

Command:

```text
PYTHONPATH=src python scripts/run_proofs.py
```

Result from both the source repository and the clean exported tree:

```text
20 passed
```

The test suite installs an autouse socket-denial fixture. Any attempted Python socket connection fails the proof rather than reaching a network.

### Concurrent exact-parent CAS stress

Command:

```text
PYTHONPATH=src python scripts/stress_cas.py
```

Result from the clean exported tree:

- rounds: 100;
- contenders per round: 32;
- total attempts: 3,200;
- canonical winners: 100;
- rejected stale contenders: 3,100;
- failed rounds: 0;
- network calls: 0;
- paid calls: 0.

Every round produced exactly one canonical winner through an exact-parent commit plus non-forced ref update model.

## Properties exercised successfully

1. Canonical JSON is deterministic and rejects floats.
2. Event and snapshot digests detect payload alteration, chain breakage, and idempotency-key conflicts.
3. Concurrent writers starting from one control head produce exactly one canonical winner.
4. A stale writer loses rather than overwriting the winner.
5. A response lost after successful ref update can be reconciled without duplicating the event.
6. Repository-wide claim, lease expiry, and one-active-request checks fail closed.
7. Review attempt and fix/re-review round remain distinct; concurrent reviewer dispatch is rejected.
8. Integer micro-USD reservations enforce request/run caps, idempotent replay, cancellation, and exact finalization.
9. Accepted-but-ambiguous fake provider requests are not silently retried.
10. Pending-stop priority is deterministic and active requests must settle or be proven cancelled before state departure.
11. Repository-scoped security halt from `idle` preserves an incident identity and recovery does not invent a run.
12. Additional security evidence can be recorded while already halted.
13. PR creation is idempotent, valid no-change creates no PR, and head movement invalidates gates and review.
14. A closed or conflicting PR requires human reconciliation.
15. Capability checks deny automated merge, auto-merge equivalents, force, protected-ref deletion, settings, secrets, protected paths, and reviewer writes.
16. Invalid unsigned webhook traffic creates no trusted delivery and no canonical halt.
17. A signed delivery-ID digest mismatch is classified as verified security evidence.

## Evidence not yet obtained

The following merged-spec requirements remain open and mandatory:

- real GitHub REST and Git Data exact-parent/ref-update behavior under races, timeouts, replay, and eventual consistency;
- actual GitHub App installation identities and token separation;
- real protected-branch and ruleset abuse tests;
- real endpoint/method/ref/path capability-wrapper enforcement;
- webhook ordering, duplicate delivery, outage, suspension, and installation-deletion behavior;
- PostgreSQL/queue reconstruction, backup, RPO, and RTO exercises;
- actual PR, check, workflow, human-close, and human-merge observation semantics;
- real provider pricing, quota, usage, cancellation, duplicate-charge, and ambiguous-acceptance reconciliation;
- fork, prompt-injection, secret-egress, hostile-diff, and scope-escape exercises;
- operational kill switches and recovery drills;
- long-inactivity and restart behavior;
- exhaustive conformance coverage for every closed event and transition in the full specification;
- durable separate-repository publication of the prototype and independent rerun;
- a dated readiness decision and `STATUS.md` promotion.

## Conclusion

The selected control-plane primitives are viable in the deterministic fake model: the initial prototype found no contradiction in the tested exact-parent CAS, replay, lease, request, review, spend, pending-stop, recovery, PR, permission, or webhook boundaries.

This result is not sufficient for readiness. Spec 079 remains `planned`, and the next proof step is durable publication in a separate proof repository followed by real GitHub App/ref/ruleset/credential tests with fake actors and zero paid provider calls.

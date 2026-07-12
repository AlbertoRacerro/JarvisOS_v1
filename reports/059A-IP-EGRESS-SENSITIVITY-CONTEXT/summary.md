# 059a — Sensitivity and context foundation

Status: implementation in review.

Base commit: `736bedd98f9bdbb5fc8a7ea0b644e1828a522fd4`.
Implementation PR: #90.

## Scope boundary

This slice adds only digest-bound sensitivity labels, operator-reviewed sanitized
derivatives, deterministic sensitivity floors, stale-source handling, and
sensitivity-aware context selection/preview. It does not alter provider-adapter
invocation, confirmation tickets, fallback execution, or the external execution
spine; those remain owned by 059b.

## Implemented contracts

- legacy records without a current digest-bound label are withheld; their manifest
  level is `unknown` only when no deterministic S2-S4 floor is known;
- deterministic floors may raise a human label and remain visible in withheld audit
  manifests, but never grant permission;
- explicit downgrade attempts from S2-S4 are rejected before floor normalization;
- S2-S4 source records are never modified to create an external-safe form;
- sanitized derivatives preserve source refs, source digests, transformations,
  policy version, reviewer state, and their own content digest;
- multi-source derivative drafts resolve every source digest and effective level and
  write the draft plus audit event under one serialized SQLite transaction;
- only effective `S0` and `S1` raw records or derivatives may enter external or
  manual previews; approved `S2` derivatives remain internal review artifacts and
  are withheld with an explicit reason;
- source selection, current source state, and latest-label reads used for
  authorization share one SQLite read transaction, including status, query, and
  evidence-verdict predicates;
- approved derivatives are revalidated against source digests and current source
  levels, including S4 relabels without content changes;
- external and manual previews compute staleness without mutating derivative or
  event state;
- derivative GET is read-only; persistence of an `approved -> stale` transition is
  exposed through an explicit revalidation operation;
- draft or approved derivatives that become stale transition atomically and write a
  `SanitizedDerivativeMarkedStale` ledger event in the same transaction;
- preview withholding occurs before context budgeting and reports included,
  withheld, and budget-dropped manifests separately;
- an approved derivative inherits the highest context priority of the source kinds
  it replaces instead of falling through to priority zero;
- multi-source derivatives replace their complete source set atomically and
  overlapping derivatives are not combined into an ambiguous packet;
- manual blocks cannot self-declare a sensitivity level or impersonate a modified
  server-owned derivative;
- both preview routes fail closed with HTTP 404 for a missing workspace.

## Review disposition

The early Codex review of commit `db2748f58e` raised one P1 and three P2 findings:

1. approved S2 derivatives were not invalidated after a source relabel to S4;
2. downgrade intent could be hidden by deterministic-floor normalization;
3. schema migration truth still identified 0008 as current after adding 0009;
4. the sensitivity import block failed Ruff ordering.

Those findings were fixed before the senior review. Subsequent senior and Claude
reviews identified route-status drift, read mutation, causally incorrect label
ordering, policy-version drift, derivative overlap, stale source deletion, dead
connection-opening wrappers, and selection occurring outside the authorization
snapshot. The correction batch treats those as code defects rather than
documentation-only risks.

The S2 policy ambiguity is resolved conservatively: S2 remains a valid persisted
classification and derivative review level, but external eligibility is restricted
to S0/S1. This rule is explicit in parent spec 059, slice 059a, runtime, and tests.

A later senior audit found two regressions encoding opposite deletion semantics.
The obsolete mixed-snapshot expectation was removed: once selection has started
inside the read transaction, a concurrent source deletion is intentionally observed
only by a later preview. The current preview remains bound to its coherent old
SQLite snapshot. A source already missing before explicit revalidation instead
marks the derivative `stale` with `source_missing:<ref>`.

The same audit found two additional consistency defects. Unlabelled records with a
hard S2-S4 floor were being reported as `unknown`, discarding a known restrictive
signal. Multi-source derivative drafting also assembled source state across multiple
connections. Both paths are now bound to their deterministic or transactional truth.

A final repository-wide audit found that the parent spec had been accidentally
truncated after its ledger section. Commit
`87c2dd77bbea03d18d6554d1f10d36729129817f` restored the provenance paragraph,
delivery split, expected-file boundaries, required tests, stop conditions,
non-goals, and acceptance criteria. The restored stop condition was reconciled with
the S0/S1 policy by explicitly denying raw S2/S3/S4/unknown content.

The exact-head Codex review then reproduced one PR-attributable focused-test defect:
the evidence snapshot fixture inserted an `evidence_records.report_artifact_id` that
did not exist while SQLite foreign keys were enabled. Commit
`b0197ad70f5fb711e2c4b6b1b92c29296eaf701a` fixed the fixture without disabling or
bypassing the constraint: it creates the referenced artifact and evidence record in
the same transaction. Codex reviewed that exact head and reported no major issue.

A proposed additional guard against direct hostile mutation of server-owned SQLite
derivative rows was dispositioned as a separate hardening concern rather than added
to 059a. Valid application paths construct derivative content digests and provenance
server-side and expose no derivative-update endpoint. No test, assertion, or gate was
weakened by this disposition.

## Added regression evidence

The sensitivity regression modules cover:

- missing-workspace 404 behavior for external and manual previews;
- stale draft approval persisting state and an audit event;
- read-only derivative GET plus explicit revalidation;
- source-priority inheritance under budget pressure;
- parity with the existing raw context-pack output for an eligible S1 record;
- zero AI gateway/provider invocation during preview;
- route-level 409 and 422 mappings;
- S2 derivative withholding in automatic and manual previews;
- causal latest-label ordering with adversarial timestamps;
- policy-version invalidation;
- coherent read-snapshot behavior for selection and eligibility, including
  concurrent predicate changes and source deletion after snapshot acquisition;
- a foreign-key-valid evidence fixture for evidence-verdict snapshot regression;
- fail-closed stale transition when a source is missing before revalidation;
- one-transaction source binding for multi-source derivative drafting;
- preservation of known S2, S3, and S4 deterministic floors in withheld manifests;
- multi-source atomic replacement and overlap rejection.

## Executed verification evidence

Verification was executed read-only on exact code head
`b0197ad70f5fb711e2c4b6b1b92c29296eaf701a`:

- `python -m ruff check app tests ../scripts/check_spec_status.py ../scripts/cheap_review.py ../scripts/manual_review.py`
  returned exit status `0` with `All checks passed!`;
- `python -m pytest -q tests/test_ai_sensitivity_snapshot_binding.py`
  returned exit status `0`: `3 passed in 0.84s`;
- `python -m pytest -q tests/test_ai_sensitivity*.py`
  returned exit status `0`: `52 passed, 169 warnings in 6.35s`;
- `python -m pytest -q` returned exit status `2` during collection because the task
  environment did not have `hypothesis` installed. The exact blockers were
  `tests/bluecad/test_geometry_property_invariants.py` and
  `tests/bluecad/test_manifest_determinism_canary.py`. `hypothesis==6.156.6` is
  already declared in `backend/requirements-dev.txt`; no test was skipped, xfailed,
  edited, or called green to conceal this environment failure.

No PR-attributable Ruff or sensitivity-test failure remained in the executed
verification commands. This evidence does not replace the full CI and real-tool
proof required by the merge gate.

## Known infrastructure blocker

GitHub Actions currently refuses to start jobs because of the repository/account
billing or spending-limit state. Failed runs contain no executed steps, so they are
not Ruff, Pytest, canary, or real-tool failures. Local and model-run evidence cannot
replace the required final-head CI gate.

## Merge gate

The PR must pass the full deterministic CI and real-tool proof on the final head,
then receive a completed Codex review on that exact head. Every new finding must be
resolved or explicitly dispositioned before human merge. CI green alone is
insufficient, and no merge is permitted before the final Codex review.

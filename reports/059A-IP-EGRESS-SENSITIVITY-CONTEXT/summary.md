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
  authorization must share one SQLite read transaction, including status, query,
  and evidence-verdict predicates;
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
snapshot. The current correction batch treats those as code defects rather than
documentation-only risks.

The S2 policy ambiguity is resolved conservatively: S2 remains a valid persisted
classification and derivative review level, but external eligibility is restricted
to S0/S1. This rule is now explicit in both parent spec 059 and slice 059a.

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
- fail-closed stale transition when a source is missing before revalidation;
- one-transaction source binding for multi-source derivative drafting;
- preservation of known S2, S3, and S4 deterministic floors in withheld manifests;
- multi-source atomic replacement and overlap rejection.

## Known infrastructure blocker

GitHub Actions currently refuses to start jobs because of the repository/account
billing or spending-limit state. Failed runs contain no executed steps, so they are
not Ruff, Pytest, canary, or real-tool failures. Local and model-run evidence cannot
replace the required final-head CI gate.

## Merge gate

The PR must pass the full deterministic CI and real-tool proof on the final head,
then receive a new completed Codex review on that exact head. Every new finding
must be resolved or explicitly dispositioned before human merge. CI green alone
is insufficient, and no merge is permitted before the final Codex review.

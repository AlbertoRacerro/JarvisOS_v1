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

- legacy records without a current digest-bound label are `unknown` and withheld;
- deterministic floors may raise a human label but never grant permission;
- explicit downgrade attempts from S2-S4 are rejected before floor normalization;
- S2-S4 source records are never modified to create an external-safe form;
- sanitized derivatives preserve source refs, source digests, transformations,
  policy version, reviewer state, and their own content digest;
- source and latest-label reads used for authorization share one SQLite read
  transaction, and preview withholds an already-selected block when its digest no
  longer matches the current source snapshot;
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
- manual blocks cannot self-declare a sensitivity level or impersonate a modified
  server-owned derivative;
- both preview routes fail closed with HTTP 404 for a missing workspace.

## Review disposition

The early Codex review of commit `db2748f58e` raised one P1 and three P2 findings:

1. approved S2 derivatives were not invalidated after a source relabel to S4;
2. downgrade intent could be hidden by deterministic-floor normalization;
3. schema migration truth still identified 0008 as current after adding 0009;
4. the sensitivity import block failed Ruff ordering.

Those findings were fixed before the senior review. Claude Code then reviewed head
`5f4ea9f` and reproduced additional defects in the route contract, stale lifecycle,
audit ledger, GET mutation, budget priority, and route-level test coverage. The
current branch addresses those findings with focused regressions. The budget fix
uses source-kind priority inheritance rather than assigning every derivative an
arbitrary decision-level priority.

The review also identified a broader duplicated-selection/private-helper risk. That
is documented for a shared public selector before 059b; it is not expanded into a
large context-builder refactor inside this bounded 059a correction.

## Added regression evidence

The review-hardening test module covers:

- missing-workspace 404 behavior for external and manual previews;
- stale draft approval persisting state and an audit event;
- read-only derivative GET plus explicit revalidation;
- source-priority inheritance under budget pressure;
- parity with the existing raw context-pack output for an eligible S1 record;
- zero AI gateway/provider invocation during preview;
- route-level 409 and 422 mappings.

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

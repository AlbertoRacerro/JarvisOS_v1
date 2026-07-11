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
- approved derivatives are revalidated against source digests and current source
  levels, including S4 relabels without content changes;
- external and manual previews compute staleness without mutating derivative or
  event state;
- preview withholding occurs before context budgeting and reports included,
  withheld, and budget-dropped manifests separately;
- manual blocks cannot self-declare a sensitivity level or impersonate a modified
  server-owned derivative.

## Early Codex review disposition

Codex reviewed commit `db2748f58e` and raised one P1 and three P2 findings:

1. approved S2 derivatives were not invalidated after a source relabel to S4;
2. downgrade intent could be hidden by deterministic-floor normalization;
3. schema migration truth still identified 0008 as current after adding 0009;
4. the sensitivity import block failed Ruff ordering.

All four findings are fixed on the current branch. Focused regressions additionally
prove that external and manual previews remain read-only when they detect stale
derivatives. The temporary branch-scoped patch workflow removed itself and is not
part of the final PR diff.

## Merge gate

The PR must pass the full deterministic CI and real-tool proof on the final head,
then receive a new completed Codex review on that exact head. Every new finding
must be resolved or explicitly dispositioned before human merge. CI green alone
is insufficient, and no merge is permitted before the final Codex review.
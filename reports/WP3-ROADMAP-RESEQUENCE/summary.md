# WP3 — roadmap resequencing

## Scope

Canonical roadmap and report only. No runtime, schema, workflow, provider, UI,
test, specification kernel, ADR, or PR #90/059a implementation file is changed.

## Maintained priority

1. Preserve the merged egress foundation: PR #90/059a, PR #95 definition amendment,
   PR #98/ADR-059, and PR #101 lifecycle reconciliation.
2. Reconcile and promote 059b through the normal full-spec ladder before any
   policy-autopilot runtime or real project-data external dogfood.
3. Promote 062 GRADE-0 and 061 TOKEN-FLOW-0 as separate bounded slices.
4. Build the productive engineering loop: 047 → 048 + 049.
5. Promote 063 CAPTURE-VAULT-0; 064 LIT-RAG-0 follows only after selecting the
   first bounded public corpus.
6. Accelerate the CAD exploration-to-promotion path 012 → 033 while preserving
   reviewed local-trusted execution and explicit human promotion.
7. Develop 030 + 037, then continue the dependency-driven backlog.

Hermes integration rows 066–069 are added by the separate PR #99 and must be
interleaved without displacing the productive 047–049 loop or bypassing 059b,
061, or 062.

## Folded requirements

- 029 and 058 consume today/month token and spend counters per provider through
  existing status data rather than creating a second usage store.
- 025 depends on graded dogfood and uses deterministic cost-per-useful-outcome
  evidence with holdout, promotion, and reversion thresholds.
- 012 accelerates only reviewed local-trusted ephemeral scripts through the
  existing bounded path.
- The existing L2 runner is not OS-level isolation. Automatic execution of
  untrusted generated code remains blocked on measured 045 isolation evidence.
- 033 retains explicit human code promotion, parameter-schema review, golden
  fixtures, and protected conformance/property tests.

## Reconstruction

This branch is reconstructed directly from post-#96 master commit
`243c7b1e1a4fb5bb9002055b322a2d7543a44096`. Its final diff is exactly:

- `docs/specs/STATUS.md`;
- this report.

All 061–064 kernels and the post-ADR-059 lifecycle reconciliation are inherited
from `master`, not duplicated in this PR.

## Verification gate

Keep draft until:

1. the branch consists only of the bounded roadmap delta above current `master`;
2. the diff contains exactly the two declared files;
3. GitHub Actions execute and pass on the exact head;
4. a current-head failure-mode-first review completes;
5. every finding is resolved or explicitly dispositioned;
6. the maintainer authorizes merge.

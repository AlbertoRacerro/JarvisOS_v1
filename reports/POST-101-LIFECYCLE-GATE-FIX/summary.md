# Post-101 059b lifecycle gate correction

## Problem

PR #101 correctly reconciled ADR-059 lifecycle wording, but one sentence in the
parent 059 definition still created a circular gate by saying implementation work
could not begin until that same implementation had merged.

## Correction

- 059b remains blocked until its full implementation specification is reconciled
  and the canonical registry explicitly promotes it to `ready`.
- Implementation work may begin after that promotion.
- Policy-autopilot runtime activation and real external execution remain blocked
  until the implementation PR is reviewed and merged.
- No sensitivity, sanitization, packet, trigger, budget, confirmation, audit, or
  authority policy changed.

## Verified scope

Exactly two docs/report files:

- `docs/specs/059-ip-egress-1.md`;
- this report.

The parent-spec diff contains only three lifecycle hunk corrections: the binding
maintainer-direction paragraph, the target-policy-autopilot lifecycle paragraph,
and the matching non-goal. No runtime, schema, workflow, provider, frontend, test,
STATUS, AGENTS, DECISIONS, or merged 059a implementation file changed.

## Verification gate

Required before merge:

1. exact two-file diff;
2. GitHub Actions green on the final repository-reachable head;
3. current-head review with no unresolved findings;
4. explicit maintainer merge authorization.

# 059 egress autopilot amendment — reconciliation report

## Scope

Docs/registry/report only. No runtime, schema, provider, gateway, execution,
confirmation, fallback, frontend, workflow, or merged 059a implementation file is
changed.

## Base and reconciliation

- New base: `master` after squash merge of PR #90, commit
  `d8353f7e8a3f616d3befe0e14a2478084d66d3fc`.
- Merged 059a remains authoritative for digest-bound labels/derivatives,
  deterministic floors, coherent SQLite read snapshots, stale handling, read-only
  previews, and effective S0/S1-only external eligibility.
- The previous WP1 branch was not merged mechanically because it diverged on parent
  spec 059 and `STATUS.md`; the amendment was reconstructed on the new base.

## Maintainer decision recorded

External providers are the normal workhorse after deterministic policy gates.
Effectively S0/S1 exact packets may receive a silent server-owned allow when no
configured confirmation trigger fires. The maintainer accepts residual imperfect-
sanitization risk to prioritize prototype velocity.

This does not weaken the execution spine: all calls use `run_ai_task`, write
`ai_jobs`, use explicit external routes, re-check each fallback, and remain subject
to provider, credential, projected-budget, sensitivity, and exact-packet policy.
S4 and monthly hard-budget denial have no override.

## Conflict disposition after PR #90

The earlier draft allowed trigger `t3` to confirm an effective S2/S3 derivative.
That conflicts with merged 059a, which permits only effective S0/S1 content in
external previews. The reconciled decision is:

- S2/S3/unknown sources may be sanitized automatically;
- effective S0/S1 output may be auto-approved and externally eligible;
- output that remains S2/S3 invokes `t3` and pauses for review/resanitization or
  remains local;
- confirmation cannot turn effective S2/S3 into an externally eligible packet.

This preserves the explicit instruction to keep 059a intact.

## Additional contracts

- default deterministic human-audit sample: 5% weekly;
- sampled rejection revokes the derivative and logs sanitizer failure;
- fail-closed per-packet count and serialized-size caps for S2/S3/unknown-derived
  blocks;
- provider-family diversification retained as planned follow-up row 065;
- trigger list is configuration, not scattered constants;
- pre-call projected economic checks close the final-call budget overshoot gap;
- legacy client-supplied escalation text/route/token fields are ignored or rejected.

## Registry state

- 059a: `merged`, PR #90;
- 059b: `blocked` until this amendment and the associated ADR merge and the full
  implementation spec is reconciled;
- 065: `planned` provider-family diversification hook.

## Verification expectations

This PR must remain draft until:

- GitHub Actions executes on the reconciled head;
- spec-status and documentation gates pass;
- the diff is confirmed docs/registry/report only;
- a current-head review is completed and findings are resolved or dispositioned;
- the maintainer explicitly authorizes merge.

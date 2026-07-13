# 059 egress autopilot amendment — reconciliation report

## Scope

Docs/registry/report only. No runtime, schema, provider, gateway, execution,
confirmation, fallback, frontend, workflow, or merged 059a implementation file is
changed.

## Base and reconciliation

- PR #90 merged 059a at
  `d8353f7e8a3f616d3befe0e14a2478084d66d3fc`.
- PR #98 subsequently merged ADR-059, resolving ADR-057's former per-call
  confirmation conflict.
- PR #95 merged the definition amendment after ADR-059, while retaining several
  temporal phrases that still described the ADR as pending; PR #101 reconciles
  those phrases with current canonical history.
- Merged 059a remains authoritative for digest-bound labels/derivatives,
  deterministic floors, coherent SQLite read snapshots, stale handling, read-only
  previews, S4-source derivative rules, and effective S0/S1-only external
  eligibility.

## Maintainer target policy

External providers are intended to become the normal workhorse after deterministic
policy gates. Effectively S0/S1 exact packets may receive a silent server-owned
allow when no configured confirmation trigger fires. The maintainer accepts
residual imperfect-sanitization risk to prioritize prototype velocity.

ADR-059 is now the durable authority for that policy and supersedes only ADR-057's
per-call confirmation sentence. Neither the ADR nor the merged definition activates
runtime by itself. 059b remains blocked until its full implementation specification
is reconciled, explicitly promoted, implemented, reviewed, and merged.

## Execution-spine preservation

The amendment does not create a second AI path:

- every model-backed sanitizer, including local Ollama, must run through
  `run_ai_task` on an explicit local route and create its own `ai_jobs` row;
- only a strictly deterministic non-model transformation may run without an AI
  call;
- sanitizer model output and schema validity have no authority;
- external calls use explicit external routes, exact-packet decisions, projected
  economic checks, and independent fallback re-checks;
- raw/final secret-bearing S4 content and monthly hard-budget denial have no
  confirmation override.

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

## S4 source versus surviving secret content

Merged 059a distinguishes a sensitive source from its sanitized representation:

- raw S4 and any final or derived content that remains S4 or secret-bearing are
  denied with no override;
- a derivative originating from an S4-labelled source may be externally eligible
  only when current, provenance-bound, effective S0/S1, deterministic checks show
  that no secret survives, and every other gate passes.

The amendment uses the same rule and does not impose a contradictory permanent ban
based only on the source label.

## Additional contracts

- default deterministic human-audit sample: 5% weekly;
- sampled rejection revokes the derivative and logs sanitizer failure;
- fail-closed per-packet count and serialized-size caps for S2/S3/unknown-derived
  blocks;
- provider-family diversification retained as planned follow-up row 065;
- trigger list is configuration, not scattered constants;
- pre-call projected economic checks close the final-call budget overshoot gap;
- legacy client-supplied escalation text/route/token fields are ignored or rejected.

## Codex review dispositions

The exact-head Codex review on `2dd62cd21c` raised three findings, all accepted and
corrected:

1. model-backed sanitization is explicitly bound to `run_ai_task` and `ai_jobs`;
2. S4-source derivatives retain merged 059a S0/S1 secret-free eligibility semantics;
3. the durable-policy conflict was resolved by ADR-059 through PR #98.

No finding was dismissed or worked around.

## Registry state

- 059: `planned`, definition-only and aligned with accepted ADR-059;
- 059a: `merged`, PR #90;
- 059b: `blocked` pending full-spec reconciliation and explicit promotion;
- 065: `planned` provider-family diversification hook.

## Verification expectations

The post-merge lifecycle reconciliation must remain draft until:

- GitHub Actions execute on the final reconciled head;
- spec-status, full backend, Ruff, geometry-canary, and applicable BLUECAD proof
  gates pass;
- the diff is confirmed docs/registry/report only;
- a fresh current-head review is completed and findings are resolved or explicitly
  dispositioned;
- the maintainer explicitly authorizes merge.

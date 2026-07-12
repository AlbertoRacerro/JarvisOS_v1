# WP4 — external policy autopilot ADR

## Scope

Docs/report only. This work records the durable architecture decision for the
external-provider policy autopilot. It changes no runtime, schema, tests,
workflow, provider adapter, frontend, specification, registry row, or merged 059a
implementation.

## Rebase

The PR branch was reconstructed directly from current `master` commit
`d8353f7e8a3f616d3befe0e14a2478084d66d3fc`. It no longer depends on the stale
WP2/WP3 branch chain.

## Required final diff

Exactly three files:

- `docs/DECISIONS.md`: append ADR-059;
- `AGENTS.md`: narrowly reconcile the model-economy confirmation wording;
- this report.

## ADR-059 decision

ADR-059 must record that:

- cheap external providers are the normal workhorse after deterministic,
  server-owned gates;
- `route_class="auto"` remains local-only and never executes an external provider;
- an explicit external route may execute only after the exact outbound packet,
  provider/model, sensitivity, credentials, projected economics, and fallback
  binding are allowed by server-owned policy;
- effectively S0/S1 exact packets may silently allow when no configured trigger
  fires;
- S2/S3/unknown sources may use automatic local sanitization with deterministic
  pre/post scans, current source/digest provenance, and versioned sanitizer policy;
- every model-backed sanitizer, including local Ollama, uses `run_ai_task` on an
  explicit local route and writes its own `ai_jobs` row;
- sanitizer/model output is advisory and cannot lower floors or authorize egress;
- default human audit samples 5% of auto-approved derivatives per calendar week;
- sampled rejection revokes the derivative and logs sanitizer failure;
- raw S4 and any final content that remains secret-bearing or above S1 are denied;
- a current, provenance-bound, secret-free effective S0/S1 derivative originating
  from an S4-labelled source retains the eligibility semantics merged in 059a;
- configured trigger families may require exact-packet human confirmation, but
  confirmation cannot turn S2/S3/S4 into eligible content or override monthly hard
  budget, missing credentials, stale provenance, or unsupported mechanics;
- context minimization and fail-closed count/serialized-size caps for
  S2/S3/unknown-derived blocks are mandatory;
- every provider attempt and fallback uses the shared execution spine and writes
  safe ledger evidence;
- the maintainer accepts residual imperfect-sanitization risk for prototype
  velocity.

ADR-059 supersedes only ADR-057's sentence requiring explicit user confirmation
for every external call. It preserves ADR-057's model-economy hierarchy and all
server-owned execution, audit, safe-default, and model-advisory invariants.

## Verification gate

The PR remains draft until:

- `docs/DECISIONS.md`, `AGENTS.md`, and this report are the only changed files;
- GitHub Actions executes and passes on the exact final head;
- a current-head Codex review completes;
- all findings are fixed or explicitly dispositioned;
- the maintainer authorizes merge.

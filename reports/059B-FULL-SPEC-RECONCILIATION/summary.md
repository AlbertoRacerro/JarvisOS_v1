# 059b full-spec reconciliation

## Purpose

Reconcile `059b` against current `master` before any implementation begins and
promote it only after the execution-spine, prompt/context, confirmation, economic,
schema, and 059a integration boundaries are mechanically implementable.

## Current-runtime findings

1. `AIGateway.run_task` forwards caller prompt and manual context directly to
   `run_ai_task`; external execution is blocked only by the current provider/status
   gate.
2. `run_ai_task` canonicalizes and size-bounds context, but before
   `adapter.complete(...)` it enforces provider/budget readiness only. No exact
   packet egress decision exists per concrete fallback binding.
3. `confirm_escalation` trusts client-owned outbound text, route, and token fields.
4. The current budget gate checks already-recorded month-to-date usage and does not
   atomically reserve the pending call or evaluate a daily soft threshold.
5. Merged 059a supports canonical record labels and approved derivatives. Its manual
   preview accepts only exact server-loaded approved derivative blocks; arbitrary
   manual blocks remain `unknown` and withheld.
6. The 059a derivative schema has no structured automatic-sanitizer job/config
   provenance or policy-approval source, and no prompt-derivative contract exists.
7. Current schema migration is `0009_sensitivity_context_foundation`; packet,
   decision, ticket, attempt, prompt-derivative, reservation, workspace-policy, and
   sampled-audit tables do not exist.
8. Existing user-facing cost estimation is route-based and cannot authorize a
   concrete provider/model or fallback with potentially different pricing.

## Reconciled implementation boundary

The full spec and binding companions now require:

- one per-network-attempt egress hook inside `run_ai_task`, after concrete binding
  resolution and immediately before request construction/adapter invocation;
- a server-owned prompt envelope and prompt-derivative path separate from 059a
  canonical record references;
- rejection of arbitrary external manual blocks unless they resolve through the
  existing 059a manual-preview contract;
- canonical persisted packets, immutable decisions, single-use tickets, immutable
  attempt links, prompt derivatives, workspace overrides, and deterministic sampled
  audit evidence;
- exact policy ownership at `configs/ai_egress_policy.json`;
- concrete provider/model pricing added to the existing
  `configs/ai_providers.yaml` registry, with route-level estimates advisory only;
- a separate compare-and-swap `egress_budget_reservations` lifecycle: decisions stay
  immutable and reference projections/reservation IDs, while active reservations are
  atomically created only when network execution is authorized and later moved
  through in-flight and reconciliation/release/expiry states;
- no outbound packet body before every included material item is current,
  provenance-bound, secret-free, and effective S0/S1;
- model-backed sanitizer binding/fallback closure restricted to local-only routes;
- provider retries returned to the shared spine for a new decision rather than
  hidden inside an adapter call;
- a bounded additive 059b compatibility extension for honest policy-sanitizer
  provenance while preserving all existing 059a label, manual-review, staleness,
  source-digest, S4-source, and eligibility semantics;
- a ticket-ID-only confirmation path; legacy client fields are rejected or ignored;
- exact fallback reconstruction and re-evaluation;
- no provider-adapter authority, no second AI spine, no second sensitivity system,
  and no runtime activation in this definition PR.

## Promotion decision

After this reconciliation, `059b` is promoted from `blocked` to `ready` in the
canonical registry. This authorizes an implementation branch only. External policy
autopilot, Hermes external passthrough, and real project-data egress remain inactive
until the implementation PR is reviewed and merged.

## Definition-PR scope

Exactly:

- `docs/specs/059b-ip-egress-enforcement.md`;
- `docs/specs/059b-implementation-clarifications.md`;
- `docs/specs/059b-config-ownership.md`;
- `docs/specs/STATUS.md`;
- this report.

No runtime, schema, workflow, provider, frontend, test, dependency, ADR, parent 059,
merged 059a, Hermes runtime, or real external-call behavior changes.

## Merge gate

- changed-file scope is exactly the five files above;
- registry checker and self-test green;
- `git diff --check` clean;
- current-head CI green;
- current-head failure-mode-first review and Codex review complete;
- explicit maintainer merge authority.

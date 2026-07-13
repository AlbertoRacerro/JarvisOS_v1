# 059b implementation clarifications

Status: binding companion to `059b-ip-egress-enforcement.md` for implementation
readiness. If wording in the full spec is ambiguous on the points below, this file
controls. `docs/specs/STATUS.md` remains authoritative for lifecycle state.

## Purpose

Close the final two failure modes found during full-spec review without changing
ADR-059, ADR-060, the parent 059 policy, or merged 059a behavior.

## 1. Immutable decision versus reservation lifecycle

An `EgressDecision` is immutable. It records the projected input/output tokens,
projected cost upper bound, concrete pricing identity/version, and optional
reservation ID. It does **not** own mutable reservation state.

059b therefore adds a separate `egress_budget_reservations` table/service with:

- decision ID and packet digest;
- concrete provider ID and model ID;
- projected input/output tokens and cost upper bound;
- state constrained to `active`, `reconciled`, `released`, or `expired`;
- creation/expiry/reconciliation timestamps;
- linked `ai_jobs`/egress-attempt ID when reconciled;
- compare-and-swap version or equivalent SQLite predicate preventing double
  transition.

Rules:

- Silent allow creates an `active` reservation in the same `BEGIN IMMEDIATE`
  transaction that writes the allow decision.
- A confirmation-required decision creates no active budget hold while the ticket is
  merely pending. Ticket consumption revalidates all limits and atomically creates
  the active reservation immediately before network invocation.
- Existing actual `ai_jobs` usage plus unexpired active reservations is the
  authoritative projected-limit input. This is not a second actual-usage ledger.
- Failed-before-network authorization releases the active reservation and records
  zero provider consumption.
- A real adapter attempt reconciles the reservation to reported usage or the bounded
  fallback estimate, including provider-error attempts.
- Expiry is fail-safe crash recovery, not a normal substitute for explicit
  reconciliation.
- Decisions and attempt evidence remain append-only; only reservation state follows
  the bounded lifecycle above.

Any full-spec phrase suggesting that mutable reservation state lives inside
`egress_decisions` is superseded by this separation.

## 2. Concrete binding pricing

Route-alias pricing alone cannot authorize a concrete external attempt because a
fallback provider/model may have different prices.

The economic decision binds a price record to:

- provider ID;
- model ID;
- input and output unit prices;
- currency;
- pricing-source/version digest;
- effective timestamp or configuration version.

A route-level estimate may remain a user-facing advisory preview. Immediately before
an external attempt, policy must resolve a conservative price for the exact concrete
provider/model. Missing, stale, unsupported, or non-USD pricing without a configured
conversion contract fails closed. Each fallback resolves and binds its own price
record.

## 3. Relationship to merged 059a

The parent 059 non-goal against “reopening 059a” means 059b may not weaken or rewrite
059a authority, eligibility, staleness, S4-source, manual-review, label, or derivative
semantics.

Implementation may make only bounded additive compatibility changes needed to record
honest policy-sanitizer provenance, such as nullable provenance columns and an
internal service entry point that uses the existing derivative lifecycle. Existing
059a rows, APIs, human approval behavior, and tests must remain backward compatible.
Callers may not write the derivative table directly.

If honest provenance cannot be added under those constraints, implementation must
stop and amend the definition rather than impersonate `local-user`, create a second
sensitivity store, or silently change 059a semantics.

## Required additional tests

- Immutable decision rows never change when a reservation is reconciled or released.
- Two concurrent silent allows cannot reserve the same final budget window.
- Two concurrent ticket consumptions create at most one active reservation and one
  adapter invocation.
- Pending confirmation tickets do not indefinitely reserve budget.
- Reservation expiry cannot make an already-started attempt appear uncharged.
- Concrete fallback pricing differs safely from route-preview pricing.
- Missing concrete provider/model pricing makes zero adapter calls.
- Existing 059a manual derivative and label tests remain unchanged and green.
- Policy-sanitizer provenance cannot be represented as a human review.

## Scope

This companion changes definition only. It does not create schema, code, pricing,
reservations, external calls, or Hermes runtime.
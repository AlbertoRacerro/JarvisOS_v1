# 059b implementation clarifications

Status: binding companion to `059b-ip-egress-enforcement.md` for implementation
readiness. If wording in the full spec is ambiguous on the points below, this file
controls. `docs/specs/STATUS.md` remains authoritative for lifecycle state.

## Purpose

Close the final failure modes found during full-spec review without changing ADR-059,
ADR-060, the parent 059 policy, or merged 059a behavior.

## 1. Immutable decision versus reservation lifecycle

An `EgressDecision` is immutable. It records the projected input/output tokens,
projected cost upper bound, concrete pricing identity/version, and optional
reservation ID. It does **not** own mutable reservation state.

059b therefore adds a separate `egress_budget_reservations` table/service with:

- decision ID and packet digest;
- concrete provider ID and model ID;
- projected input/output tokens and cost upper bound;
- state constrained to `active`, `in_flight`, `reconciled`, `released`, or `expired`;
- creation, expiry, attempt-start, and reconciliation timestamps;
- linked `ai_jobs`/egress-attempt ID once the network attempt starts;
- compare-and-swap version or equivalent SQLite predicate preventing double
  transition.

Rules:

- Silent allow creates an `active` reservation in the same `BEGIN IMMEDIATE`
  transaction that writes the allow decision.
- A confirmation-required decision creates no active budget hold while the ticket is
  merely pending. Ticket consumption revalidates all limits and atomically creates
  the active reservation immediately before network invocation.
- Immediately before calling the adapter, the same bounded execution path changes
  `active` to `in_flight` and binds the attempt identity. An `in_flight` reservation
  cannot expire or be released by ordinary stale-reservation cleanup.
- Existing actual `ai_jobs` usage plus unexpired `active` and all `in_flight`
  reservations is the authoritative projected-limit input. This is not a second
  actual-usage ledger.
- Failed-before-network authorization releases the `active` reservation and records
  zero provider consumption.
- A real adapter attempt reconciles the `in_flight` reservation to reported usage or
  the bounded fallback estimate, including provider-error attempts.
- Only never-started `active` reservations may transition to `expired`. Expiry is
  fail-safe crash recovery, not a substitute for explicit attempt reconciliation.
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

## 3. Eligibility before packet creation

`EgressPacket` means a fully formed candidate outbound body. It may be persisted only
after prompt and every included context block are current, provenance-bound,
secret-free, and effective S0/S1.

For raw S2/S3/S4/unknown material, sanitizer failure, stale provenance, malformed
manual blocks, or any other pre-eligibility denial/pause:

- create no outbound packet body;
- persist only an immutable decision/evaluation with safe input digests, manifest
  counts, levels, and deterministic reason code;
- make zero adapter calls;
- expose no raw body through the API or ledger.

An otherwise eligible S0/S1 packet may still be persisted and then denied or paused
by credential, projected-budget, trigger, or unsupported-binding policy. Decision
packet IDs/digests are therefore nullable for pre-packet denials and required for
post-packet decisions.

Any full-spec sequence that appears to write an outbound packet before eligibility is
established is superseded by this ordering.

## 4. Local sanitizer route closure

A model-backed sanitizer invocation is an internal task with a dedicated task kind
and explicit local route. Its complete binding/fallback closure must satisfy
`requires_network = false`.

- A local sanitizer may not fall back to an external provider.
- It may not recursively invoke external egress policy or another sanitizer pass
  without an explicit bounded orchestration step.
- It receives only the exact material selected for that sanitizer operation, with
  automatic project-context inclusion disabled.
- The sanitizer `ai_jobs` row records safe digests/version metadata only.
- A test must fail if any sanitizer binding or fallback becomes network-capable.

## 5. Adapter retry visibility

Current OpenAI-compatible adapters perform one HTTP POST per `complete(...)` call.
059b preserves that property: provider adapters may not hide automatic network
retries from the shared spine.

A retry or fallback that can issue another HTTP request must return control to
`run_ai_task`, receive a new fallback/retry index, and undergo a fresh packet,
decision, credential, trigger, pricing, and reservation evaluation. Transport logic
may not silently issue a second network request under the first decision.

## 6. Prompt authority

The final prompt level is the maximum of all applicable server-owned evidence:

deterministic secret/IP/confidential floors, existing deterministic task/history
signals where applicable, current policy defaults, and optional local advisory
classification that may raise but never lower the result.

The FAST_DEV S1 default applies only when no higher signal exists and no untrusted
manual/project body has been folded into the prompt. Moving attached context into the
prompt string does not exempt it from prompt classification or sanitization.

## 7. Deterministic sampling

The default 5% automatic-audit decision is frozen as a stable hash threshold, not a
runtime random draw:

1. canonicalize `policy_version`, ISO UTC week, derivative kind, derivative ID, and
   content digest;
2. compute SHA-256;
3. interpret the first unsigned 64 bits and select when `value mod 10000 < 500`.

This produces a deterministic 5% rate in expectation and permits synchronous queue
creation without a worker or knowledge of the final weekly cohort. Policy may raise
the threshold up to 10000 but cannot lower the default below 500 without a later
maintainer decision.

## 8. Relationship to merged 059a

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
- An `in_flight` reservation cannot expire before attempt reconciliation.
- A pre-packet S2/S3/S4/unknown denial persists no outbound body.
- Concrete fallback pricing differs safely from route-preview pricing.
- Missing concrete provider/model pricing makes zero adapter calls.
- A sanitizer binding or fallback becoming network-capable makes a test fail.
- A hidden second HTTP request inside an adapter makes a test fail.
- The sampling algorithm is stable across process restarts and input ordering.
- Existing 059a manual derivative and label tests remain unchanged and green.
- Policy-sanitizer provenance cannot be represented as a human review.

## Scope

This companion changes definition only. It does not create schema, code, pricing,
reservations, external calls, or Hermes runtime.

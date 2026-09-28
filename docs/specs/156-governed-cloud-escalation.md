# 156 — Governed cloud escalation

State: **ready**. Combined definition and readiness under the maintainer's 2026-09-28 directive to deliver a minimum viable governed cloud path before 155. Dependencies 154b and 154c are merged. This is a bounded extension of the existing 059b external execution spine, not a new egress authority.

## Outcome

An operator can keep ordinary work on the configured Gemma local responder and explicitly escalate one difficult, cloud-safe task to the cheapest configured model that meets that task family's evidence-backed quality floor. An objective local failure signal may offer the same one-step escalation; it does not authorize egress on its own. Jarvis applies privacy, provider and spend constraints before comparing model cost. Cloud output is advisory data: it cannot issue broker tool calls or promote canonical engineering state without existing Jarvis validation and authority.

## Accepted capability

1. A configurable catalog names the eligible external provider/model bindings, task families and qualification floors, context/output limits, currency, reviewed token prices and their source/review date. An unknown quality level is ineligible. Selection after hard filters is deterministic and minimizes a conservative upper cost for the bounded request. The selected provider, model, price version and reason are visible to the operator.
2. A single escalation request accepts only a server-resolved, currently approved sanitized derivative and its explicit task class. It sends neither the raw conversation nor workspace context, memory, tool output or agent prompt. The existing `STRICT_IP` classification, packet, confirmation, credential and egress gates remain mandatory at dispatch. Unclassified or invalid source lineage yields a classification/approval request or a local-only result, never provider dispatch.
3. Positive hard per-request and per-thread/session cost ceilings bound projected spend before reservation. The existing global, provider and monthly gates remain in force. Concurrency cannot oversubscribe a cap; a failed reservation, provider failure or exhausted budget records a truthful terminal result and leaves the local workflow available without a second cloud attempt.
4. Every attempt links its local trigger, approved derivative and exact egress packet to provider/model, task class, decision, actual reported usage and priced cost. Cost shown in EUR is a reproducible calculation from recorded provider-currency price and a dated conversion rate; when usage or conversion is unavailable, mark it unknown rather than reporting a fabricated exact charge. Show outcome and reason even when no network call occurred.
5. The operator can inspect and invoke the one-step path from the Sidecar/Hermes workflow without giving Hermes provider choice, egress, spending or execution authority. The approved derivative is the entire cloud input. Returned text remains separate advisory content until an operator or existing deterministic authority uses it.

## Boundaries

- Safe defaults stay: paid AI off, zero budget, fake provider mode. No live paid call without the existing operator settings and credentials.
- No automatic retry, fallback chain or second cloud hop for this path; no learned routing, speculative confidence or semantic sanitizer, cloud planner/local executor autonomy, broad provider search, or new promotion authority.
- Existing local replies and Hermes inference remain local. Escalation never serializes their prompt or tool transcript into an external packet.
- 155 stays planned until this path is implemented and live accepted, then its contract is defined against the hybrid architecture.

## Required evidence

- Deterministic tests exercise model eligibility and cheapest adequate choice; stale/missing qualification or price rejection; derivative and workspace binding; unclassified and sensitive input refusal; bounded request/session reservations under concurrency; provider failure and zero-budget behavior; packet/usage/price/FX provenance; and cloud output's advisory-only boundary.
- Real operator tasks show local work staying on Gemma, a difficult cloud-safe derivative escalating, unclassified IP-sensitive material stopping for classification, an approved sanitized derivative without protected context in the packet, and safe provider/budget failure. Inspect actual provider/model, packet, token usage and EUR conversion provenance. Use a real browser for operator-visible criteria and the relevant host for local Gemma behavior.
- Review the exact implementation head for egress, credential and authority regressions before merge. Do not claim a live paid-provider result when credentials, spend authorization or host access are unavailable.

## Completion

One useful cloud reasoning step is available through Jarvis's existing egress gate with bounded spend and inspectable provenance; local and protected work stays local. Reconcile the implementation PR and only then begin 155.

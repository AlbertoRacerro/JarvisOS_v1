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

## Scaleway live qualification 2026-09-28

On the canonical WSL host, systemd v255 delivered the named `SCALEWAY_API_KEY` credential to a Jarvis process through `LoadCredentialEncrypted=` and `$CREDENTIALS_DIRECTORY`. `systemd-creds has-tpm2` reported partial support with no usable device, so the encrypted WSL copy uses the installation-bound root-only host key. The Windows DPAPI source remains in place. The one-time importer passed its in-memory plaintext through stdin directly to `systemd-creds encrypt`; only ciphertext persists in WSL. This is credential availability evidence, not approval of Scaleway for strategic/IP-derived workloads.

The isolated acceptance runtime used STRICT_IP, a $0.05 software budget, a genuine completed local interaction, and an approved S0 derivative containing only public textbook heat-balance values. Scaleway `deepseek-v4-flash-0731` answered the bounded engineering task correctly: `2 kg/s × 4.2 kJ/(kg·K) × 10 K = 84 kW`. The successful `ai_jobs` record was `b04d8662-dd32-4f3d-837a-f582ed1355b8`; `egress_attempts` recorded 288 input tokens, 223 output tokens, and USD 0.00033479208 at the reviewed pricing. One earlier 80-token attempt failed after network dispatch and was conservatively accounted at USD 0.00031791564. This single task supports only the narrow acceptance quality tier; it does not establish broader model reliability or provider trust.

The 156 escalation `9753b010-4fff-4842-a8b8-eb9a6ec265a5` completed from the actual local interaction `53c65dcb-6036-41c9-ba64-00d008ea0ce4` and approved derivative `94162a49-5f82-4776-9750-57940751af40`. Its packet contained only that derivative as context plus the fixed approved prompt. The model again returned 84 kW. The record includes provider/model, price source and version, packet digest, 288 input/175 output tokens, USD 0.00029100456 and EUR 0.0002552 at the recorded ECB rate. It remained advisory: no project decision or action was applied. An unapproved derivative returned 409; an unclassified protected prompt returned `prompt_sanitization_required` before network; reducing the acceptance budget below prior spend yielded `global_monthly_cost_cap_exceeded`, zero accounted cost and no new network attempt. The browser Sidecar displayed the completed advice, advisory notice, and token provenance from this same isolated runtime. The acceptance runtime was then returned to paid AI off, zero budget, fake provider mode and stopped; the temporary browser build was restored to its normal API target.

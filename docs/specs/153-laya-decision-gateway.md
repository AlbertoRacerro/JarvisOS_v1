# 153 — Laya decision gateway for Hermes

State: **ready**. Combined definition, full contract and readiness, authorized by the maintainer's 2026-09-25 Frontier Coordinator directive. Smallest follow-up to 147, 151 and 152: it gives the Hermes agent mode a cheap typed "System-1" advisor without moving any authority out of JarvisOS.

## Fresh baseline

147 merged a bounded typed decision core: `DecisionRequest`/`DecisionResult` (bool/enum/score outputs, explicit `abstained` outcome, `validate_decision_result`), a replaceable `DecisionModel` protocol with `RuleDecisionModel` and optional `GlinerDecisionModel`, and evidence/resource-aware local candidate selection. Nothing outside the backend calls it. 152 (stacked on 151) runs Hermes as an agent mode of the Sidecar, and the grant-checked broker exposes only read-only context/Second Brain navigation tools. Hermes today decides route, retry, escalation and model choice with its own full-model reasoning or not at all. That is expensive on the 27B local route (measured about 3.5 tok/s on Q4_K_XL and about 24 tok/s on IQ2_M), and the choices leave no Jarvis-side evidence.

## Accepted capability

1. **Laya, one named gateway.** A JarvisOS-owned `DecisionGateway` port, named Laya, with a closed catalogue of four typed recommendation kinds: `route_class` (answer directly / use a read tool / needs a capability Jarvis does not grant), `retry_or_stop` after a failed or empty tool/inference step, `escalate` (stay local / ask the human / suggest a stronger admitted route), and `model_select` among the currently available admitted local candidates. Each kind has a fixed `DecisionRequest` shape, bounded input and a typed output with confidence and abstention. The backing `DecisionModel` is replaceable by configuration (rules by default, a small local classifier or the 151 runtime when qualified). Nothing outside the port depends on which model is behind it.
2. **Served to Hermes as advice only.** The 152 broker adds one read-only tool, `jarvis.decide`, under the same server-side thread grant. Hermes may call it and may ignore it. Laya never admits, reserves, grants, egresses, executes, switches routes or starts models. Every result is a non-authoritative recommendation. Jarvis still decides admission, reservation, route availability, egress and grants deterministically at the moment of use, so a `model_select` or `escalate` recommendation that the policy would refuse is refused there as it is today.
3. **Evidence.** Each call records kind, request digest, backing model identity/revision, outcome (decided/abstained), latency and the recommendation as tool evidence on the Hermes interaction's flow. The recommendation is not written into project truth.

## Non-goals

- No planning, tool orchestration, memory or conversation in Laya; Hermes keeps planning and tool orchestration.
- No new authority path, no automatic route/model switch, no external-provider call from Laya, no free-form text output.
- No new decision kinds beyond the four without a spec change; no fine-tuning or model download in this slice.

## Required evidence

- Deterministic tests: catalogue shapes and bounds per kind; abstention on out-of-catalogue or low-confidence input; `validate_decision_result` enforced on every backend; backend replacement by configuration without caller change; broker grant check for `jarvis.decide`; a recommendation to use an unavailable or policy-refused route is refused by the existing admission path; evidence recorded per call.
- Real runtime: a real Hermes turn through the 152 path calls `jarvis.decide` at least once, and the call is visible in the durable flow evidence. Latency is reported for the rule backend and for any model backend used.
- Laya is recorded as unqualified for a kind if its backend abstains on or mis-decides the qualification fixtures for that kind. For that kind Hermes then falls back to its own reasoning.

## Completion

Hermes in the Sidecar can ask Jarvis for a cheap typed recommendation on routing, retry, escalation and model choice. The answer is evidenced and replaceable, and it changes no Jarvis authority. Registry and PR association are reconciled after merge.

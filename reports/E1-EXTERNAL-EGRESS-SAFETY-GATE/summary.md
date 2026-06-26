# E1 — External Egress Safety Gate

## Status

GREEN — audited, deterministic gate only.

E1 adds a provider-agnostic external egress safety gate. It does not enable external routing and does not call any external provider.

## Starting state

- Starting HEAD: `abb292c0e208b992ca01ce165745ab82aa5841b3`
- Milestone: `E1-EXTERNAL-EGRESS-SAFETY-GATE`
- Scope: deterministic egress gate + offline tests
- Runtime execution enabled: no
- External provider calls: no
- Retrieval/memory changes: no
- Budget enforcement: no

## Files added

- `scripts/router_policy_external_egress_gate.py`
- `tests/test_router_policy_external_egress_gate.py`

## Purpose

E1 creates the deterministic safety chokepoint that future external execution must pass before any payload leaves the local system.

The gate is intentionally standalone. It does not execute an external call. It only evaluates whether an exact outbound component list would be allowed to leave.

Future external execution should require at least:

```text
candidate/proposal or explicit external selection
AND explicit user shareability opt-in
AND user confirmation
AND E1 egress gate allowed
AND budget OK
AND provider config OK
```

E1 implements only the egress gate.

## Design decisions

### Opt-in is consent, not a safety label

`explicit_user_shareability_opt_in` is required for allow, but it is not trusted as proof that content is safe or public. The opt-in means the user consents to considering the payload for external sharing. It does not bypass deterministic deny checks.

### Unknown-clean + opt-in can allow

E1 does not require a trusted automatic "public" classifier. For v0:

```text
unknown-but-clean + opt-in true + no positive danger signal -> allow
unknown-but-clean + opt-in false -> deny
positive danger signal + opt-in true -> deny
```

This avoids both failure modes:

```text
assume_public_simple=True  -> everything looks public -> unsafe no-op gate
conservative blanket mode  -> everything unknown/manual_review -> deny-all
```

### Positive danger signals always deny

The gate denies if any component derives a real danger signal, including secret/credential context, raw-private or IP-sensitive context, `sensitivity_bucket_proposal in {"sensitive", "secret"}`, BlueRev/IP A5-R3 floor producing `sensitive`, memory-write/document-write/operational-write reasons, credential-save/token/secret reasons, non-low-risk hard reasons, derivation failure, and component mismatch between evaluated and send payload.

### `assume_public_simple` is not allow evidence

E1 derives safety with `assume_public_simple=False`. No component is allowed merely because a dev shortcut marked it public.

### No conservative-overlay deny-all

E1 does not treat blanket conservative `unknown` or blanket `requires_manual_review=True` as a positive danger signal by itself. It keys deny decisions on concrete positive danger signals.

### Derive-only safety

E1 does not trust caller-carried safety metadata as authority. The gate derives safety internally from component text/source using deterministic router signals where possible.

### Single-source component contract

E1 evaluates the exact component list intended for outbound rendering. The decision includes component identities and digests. Payload/component mismatch denies. Future E4 must not send components that E1 did not evaluate.

## Behavior summary

Implemented gate: `evaluate_external_egress_gate(...)`.

Structured output includes `allowed`, primary `reason_code`, `reason_codes`, checked component count, checked component identities, component digests, and per-component safety results.

The gate:

- requires explicit shareability opt-in for allow
- allows unknown-clean content with opt-in
- denies unknown-clean content without opt-in
- denies all positive danger signals even with opt-in
- denies sensitive/secret/raw-private/manual-review danger components
- denies history contamination
- denies failed derivation
- denies evaluated/send payload mismatch
- preserves bare-BlueRev non-false-positive behavior
- consumes A5-R3 BlueRev/IP floor as a deny signal
- does not set or use `external_allowed=true`
- does not enable external execution

## Test coverage

Covered cases include clean unknown current message + opt-in allow; without opt-in deny; positive danger + opt-in deny; `assume_public_simple` not used as allow evidence; BlueRev public wording + opt-in allow; proprietary/confidential BlueRev/IP wording deny; secret + BlueRev deny as secret; history contamination deny; failed derivation deny; payload component mismatch deny; checked component identity/digest reporting; no provider/API/model calls.

## Checks run

- `python -m unittest tests.test_router_policy_external_egress_gate` -> passed, 12 tests
- `python -m unittest tests.test_router_policy_message_route_smoke tests.test_router_policy_external_egress_gate` -> passed, 105 tests
- `python -m unittest tests.test_router_policy_semantic_validator` -> passed, 40 tests
- `python -m pytest tests/test_router_policy_external_egress_gate.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py -q` -> passed, 145 tests
- marker check -> expected marker hits found; no `external_allowed` hits in E1 files
- `git diff --check` -> passed (LF-to-CRLF warnings only on Windows)

## Boundary check

E1 did not add backend route execution, frontend behavior, provider calls, API keys, external routing execution, memory/retrieval, budget enforcement, streaming, model calls, DevLoop/agent automation, or BlueRev modeling behavior.

## Residual risk

E1 does not improve semantic detection coverage. If IP-sensitive content is not detected by deterministic scanners and the user explicitly opts in, future external execution could allow it.

This is accepted for v0 because:

- opt-in is explicit
- E1 denies all detected positive danger signals
- external execution is not implemented in E1
- future E2/E3/E4 must still add privacy defaults, budget enforcement, provider configuration, confirmation, and final execution gating
- retrieval/memory are not injected into external payloads yet

Do not claim E1 proves semantic publicness. E1 enforces deterministic no-egress boundaries plus explicit user consent.

## Final status

E1 code and tests are GREEN after direct audit.

Final commit message: `Add external egress safety gate`

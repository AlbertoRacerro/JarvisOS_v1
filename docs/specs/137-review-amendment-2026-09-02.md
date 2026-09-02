# 137 AE002-GENERIC-NETWORK-COVERAGE-1 — exact-head review amendment

Status: binding planning/readiness amendment

This amendment closes the two material exact-head review findings raised against planning head `80ae97de22991ebaa75844ddc051f93935b7b8bb`. It is additive to `137-ae002-generic-network-coverage-1.md` and `137-readiness-2026-09-02.md`; where earlier wording is narrower, this amendment controls. The READY decision remains valid only with these requirements included.

## Delta 1 — constructor-bound httpx dispatch

Fresh review proved an existing concrete blind spot not covered by the earlier constructor families: `backend/app/modules/local_ai_eval/probe_micro_contracts.py::run_probe_case` dispatches through a bound `httpx.Client` (`client.post(...)`). The current scanner reduces that call to a generic `client.post`, so the F5 repair would still permit a first-party direct network dispatcher to remain invisible.

The implementation MUST extend the same bounded same-file constructor/binding normalization already authorized by 137 to `httpx.Client` and `httpx.AsyncClient` instances and classify their concrete request methods (`request`, `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `stream`, where present on the concrete client API) as AE002 outside accepted/exact-exempted owners. This is not a generic method-name rule and does not authorize broad interprocedural data-flow analysis.

The current-tree dispatcher is now explicitly classified rather than deferred: `backend/app/modules/local_ai_eval/probe_micro_contracts.py::run_probe_case` is an evaluation-only local-model transport owner, but its direct callable boundary currently accepts a caller-supplied endpoint. Before its exact AE002 retained-owner exception becomes valid, this slice MUST invoke the already-existing `validate_native_endpoint(endpoint_url)` inside `run_probe_case` before request construction/dispatch. This is the same defense-in-depth rule already applied by 137 to `_stdlib_json_post_client`: reuse the existing local endpoint contract at the exact-exempted transport boundary; do not invent another policy.

This review delta therefore authorizes one additional exact AE002 retained-owner entry:

- `backend/app/modules/local_ai_eval/probe_micro_contracts.py::run_probe_case` — classification `accepted_owner`; owner/rationale: local micro-contract evaluation transport, valid only after its own existing `validate_native_endpoint` guard is enforced.

This is the eleventh and final inventoried exact AE002 entry authorized by 137. No twelfth exception, directory-wide owner, wildcard, or broad `local_ai_eval` exemption is authorized without fresh re-derivation. The allowed implementation paths are correspondingly expanded only to `backend/app/modules/local_ai_eval/probe_micro_contracts.py::run_probe_case` and focused no-network tests for that exact boundary; no other `backend/app/**` mutation is authorized.

Deterministic acceptance MUST include at least:

- a same-file `httpx.Client()` binding followed by `.post(...)` outside an accepted owner -> AE002;
- an `httpx.AsyncClient()` binding followed by a representative request method outside an accepted owner -> AE002;
- existing module/alias `httpx` cases remain detected;
- unrelated objects exposing `.post`, `.request`, or `.stream` remain non-findings;
- direct `run_probe_case(..., endpoint_url=<external-or-malformed>)` fails through the existing endpoint validator before mocked client dispatch, while the current valid localhost endpoint reaches only the mocked transport seam;
- the full-tree scan is green only with the exact `run_probe_case` retained-owner entry plus the ten previously inventoried entries;
- if widened detection exposes any further current-tree httpx client dispatcher, implementation stops for exact-site disposition rather than adding another exception.

No new runtime owner, network library, broad exception, or product-provider behavior is authorized.

## Delta 2 — proxy escape at exact-exempted localhost urllib transports

Fresh review also proved that initial loopback validation plus redirect rejection is insufficient with standard urllib behavior. If `HTTP_PROXY`/`HTTPS_PROXY` is configured and the environment does not bypass the loopback host, urllib may dispatch the validated localhost request to an external proxy. `build_opener(...)` also installs proxy handling by default unless explicitly disabled.

Before either localhost transport may receive its exact AE002 exception, the implementation MUST make proxy escape fail closed at both existing boundaries:

- `scripts/local_model_structured_output_probe.py::call_ollama_chat`
- `scripts/router_policy_local_responder.py::_stdlib_json_post_client`

The minimum authorized design is a local transport opener that disables environment proxy handling (for example, an opener containing an explicit empty `ProxyHandler({})`) together with the already-required redirect rejection. An equivalently smaller deterministic mechanism is acceptable only if it proves the request cannot be routed through an environment-configured external proxy. Do not add a generic proxy-policy service or modify global process environment state.

Deterministic no-network acceptance MUST include, for both transports:

- hostile proxy environment variables pointing to a representative external proxy while the target URL is valid loopback;
- proof that the configured proxy path is not used and no request is emitted to the proxy;
- the valid loopback request still reaches only the mocked local transport seam;
- redirect rejection remains effective and no external follow-up request occurs;
- redirect-safe/proxy-disabled opener `.open` dispatch remains mechanically visible to AE002 outside the two exact-exempted owner symbols.

## Frozen implementation impact

The only file-boundary expansion from the previously accepted packet is the exact `probe_micro_contracts.py::run_probe_case` validation/test seam required to make the newly detected current-tree `httpx.Client` owner truthful. Otherwise these deltas remain within the existing scanner/config and two localhost urllib transport boundaries.

All prior 137 non-goals, exact-exception constraints, provider-import regression coverage, socket datagram coverage, redirect requirements, stable diagnostics, full-tree gate, independent exact-head semantic review, and PROUD gate remain binding.

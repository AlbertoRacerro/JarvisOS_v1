# 137 AE002-GENERIC-NETWORK-COVERAGE-1 — exact-head review amendment

Status: binding planning/readiness amendment

This amendment closes material exact-head review findings raised during planning. It is additive to `137-ae002-generic-network-coverage-1.md` and `137-readiness-2026-09-02.md`; where earlier wording is narrower, this amendment controls. The READY decision remains valid only with these requirements included.

## Delta 1 — constructor-bound httpx dispatch

Fresh review proved an existing concrete blind spot not covered by the earlier constructor families: `backend/app/modules/local_ai_eval/probe_micro_contracts.py::run_probe_case` dispatches through a bound `httpx.Client` (`client.post(...)`). The current scanner reduces that call to a generic `client.post`, so the F5 repair would still permit a first-party direct network dispatcher to remain invisible.

The implementation MUST extend the same bounded same-file constructor/binding normalization already authorized by 137 to `httpx.Client` and `httpx.AsyncClient` instances and classify their concrete dispatch methods (`request`, `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `stream`, and `send`, where present on the concrete client API) as AE002 outside accepted/exact-exempted owners. `send` is required because a caller can construct an `httpx.Request` separately and dispatch it through a bound client without invoking any request verb. This is not a generic method-name rule and does not authorize broad interprocedural data-flow analysis.

The current-tree dispatcher is now explicitly classified rather than deferred: `backend/app/modules/local_ai_eval/probe_micro_contracts.py::run_probe_case` is an evaluation-only local-model transport owner, but its direct callable boundary currently accepts a caller-supplied endpoint. Before its exact AE002 retained-owner exception becomes valid, this slice MUST invoke the already-existing `validate_native_endpoint(endpoint_url)` inside `run_probe_case` before request construction/dispatch. This is the same defense-in-depth rule already applied by 137 to `_stdlib_json_post_client`: reuse the existing local endpoint contract at the exact-exempted transport boundary; do not invent another policy.

The same exact-exempted transport MUST also disable environment proxy inheritance. Any concrete `httpx.Client` that can reach the dispatch inside the retained-owner symbol must be structurally constrained to `trust_env=False` or an equivalently bounded deterministic setting that prevents `HTTP_PROXY`/`HTTPS_PROXY`/related environment proxy variables from routing a validated loopback request through an external proxy. It is not sufficient to harden only the default client created by `run_probe_suite`, because both `run_probe_suite` and `run_probe_case` currently accept caller-supplied `httpx.Client` objects. The implementation must therefore make proxy safety true at the dispatch boundary itself: either remove/restrict arbitrary network-capable client injection so the retained owner constructs/owns a proxy-disabled client, or fail closed before dispatch unless the injected client is deterministically constrained to the same proxy-disabled contract. Do not rely on caller discipline, mutate global environment state, add a proxy-policy service, or accept an unverifiable/private-state assumption as proof.

This review delta therefore authorizes one additional exact AE002 retained-owner entry:

- `backend/app/modules/local_ai_eval/probe_micro_contracts.py::run_probe_case` — classification `accepted_owner`; owner/rationale: local micro-contract evaluation transport, valid only after its own existing `validate_native_endpoint` guard is enforced and every client that can reach its dispatch is structurally proxy-disabled.

This is the eleventh and final inventoried exact AE002 entry authorized by 137. No twelfth exception, directory-wide owner, wildcard, or broad `local_ai_eval` exemption is authorized without fresh re-derivation. The allowed implementation paths are correspondingly expanded only to `backend/app/modules/local_ai_eval/probe_micro_contracts.py::run_probe_case`, the minimum adjacent `run_probe_suite` injection/construction seam required to make that boundary structurally proxy-safe, and focused no-network tests for those exact boundaries; no other `backend/app/**` mutation is authorized.

Deterministic acceptance MUST include at least:

- a same-file `httpx.Client()` binding followed by `.post(...)` outside an accepted owner -> AE002;
- an `httpx.AsyncClient()` binding followed by a representative request method outside an accepted owner -> AE002;
- bound `httpx.Client.send(request)` and `AsyncClient.send(request)` outside an accepted owner -> AE002;
- existing module/alias `httpx` cases remain detected;
- unrelated objects exposing `.post`, `.request`, `.stream`, or `.send` remain non-findings;
- direct `run_probe_case(..., endpoint_url=<external-or-malformed>)` fails through the existing endpoint validator before mocked client dispatch, while the current valid localhost endpoint reaches only the mocked transport seam;
- hostile proxy environment variables do not route `run_probe_case` through an external proxy;
- an explicitly caller-supplied/default-configured `httpx.Client` that would inherit environment proxies cannot reach the retained-owner dispatch: it is rejected before dispatch or the arbitrary-client injection surface has been removed/replaced by a structurally safe seam;
- valid tests use only a proxy-disabled concrete client or a non-network mock/transport seam that cannot weaken the production proxy contract;
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

## Delta 3 — constructor-bound requests Session dispatch

Fresh review of head `2a6a2f50555ecd12e3428a92c26d1fa67de13eca` proved the same constructor-provenance blind spot exists for the already-supported `requests` family: `requests.Session()` / `requests.session()` returns an object whose `.request(...)`, HTTP verb methods, and `.send(...)` perform concrete network dispatch, while the current scanner sees only generic instance method names.

The implementation MUST extend the same bounded same-file constructor/binding normalization to concrete `requests.Session` / `requests.session` instances, including aliased/from-import constructor forms where resolvable. On those proven bindings, classify `request`, `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, and `send` as AE002 outside accepted/exact-exempted owners. Do not classify same-named methods on unrelated objects.

Deterministic acceptance MUST include at least:

- `session = requests.Session(); session.post(...)` outside an accepted owner -> AE002;
- `session = requests.session(); session.request(...)` outside an accepted owner -> AE002;
- an alias/from-import Session construction followed by representative dispatch -> AE002;
- `Session.send(prepared_request)` on a proven requests-session binding -> AE002;
- unrelated `.post`, `.request`, or `.send` methods remain non-findings;
- existing module-level `requests.get/post/request/...` detection remains unchanged except for the explicit HEAD/OPTIONS completion in Delta 4.

This delta adds no retained-owner exception and authorizes no new path outside the existing scanner/test boundary. If the widened full-tree scan exposes a previously hidden current-tree `requests.Session` dispatcher outside an already accepted owner, implementation must stop for exact-site disposition rather than silently broadening exceptions.

## Delta 4 — module-level HEAD and OPTIONS dispatch

Fresh review of head `4b306faeda55f8a14c4a8b86ce5d3a23013ceed6` proved that the existing module-level `httpx` / `requests` dispatcher set remains narrower than the concrete client/session set: module-level `head(...)` and `options(...)` are real network-dispatch methods but are not currently classified by AE002.

The implementation MUST add `head` and `options` to the existing module-level dispatch families for both `httpx` and `requests`, preserving the same import/alias/from-import binding rules used for the already-detected verbs. This is a concrete family completion only; it does not authorize generic same-name method matching.

Deterministic acceptance MUST include at least:

- direct and aliased `httpx.head(...)` and `httpx.options(...)` outside accepted owners -> AE002;
- direct and aliased `requests.head(...)` and `requests.options(...)` outside accepted owners -> AE002;
- representative from-import forms where the existing scanner resolves equivalent module-level dispatch -> AE002;
- accepted-owner/exact-exception semantics remain unchanged;
- unrelated `.head` / `.options` methods remain non-findings.

This delta adds no retained-owner exception and no implementation path outside the existing scanner/test boundary.

## Frozen implementation impact

The only file-boundary expansion from the previously accepted packet remains the exact `probe_micro_contracts.py` validation/client-construction seam required to make the newly detected current-tree `httpx.Client` owner truthful. All additional `httpx.send`, `requests.Session`, and module-level HEAD/OPTIONS work stays inside the already-authorized scanner and focused architecture-enforcement tests.

All prior 137 non-goals, exact-exception constraints, provider-import regression coverage, socket datagram coverage, redirect requirements, stable diagnostics, full-tree gate, independent exact-head semantic review, and PROUD gate remain binding.

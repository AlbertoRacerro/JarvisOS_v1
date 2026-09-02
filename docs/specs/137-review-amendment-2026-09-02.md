# 137 AE002-GENERIC-NETWORK-COVERAGE-1 — exact-head review amendment

Status: binding planning/readiness amendment

This amendment closes the two material exact-head review findings raised against planning head `80ae97de22991ebaa75844ddc051f93935b7b8bb`. It is additive to `137-ae002-generic-network-coverage-1.md` and `137-readiness-2026-09-02.md`; where earlier wording is narrower, this amendment controls. The READY decision remains valid only with these requirements included.

## Delta 1 — constructor-bound httpx dispatch

Fresh review proved an existing concrete blind spot not covered by the earlier constructor families: `backend/app/modules/local_ai_eval/probe_micro_contracts.py` constructs an `httpx.Client` and later dispatches through the bound client (`client.post(...)`). The current scanner can reduce that call to a generic `client.post`, so the F5 repair would still permit a first-party direct network dispatcher to remain invisible.

The implementation MUST therefore extend the same bounded same-file constructor/binding normalization already authorized by 137 to `httpx.Client` / `httpx.AsyncClient` instances and classify their concrete request methods (`request`, `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `stream`, as applicable to the concrete client API) as AE002 outside accepted/exact-exempted owners. This is not a generic method-name rule and does not authorize broad interprocedural data-flow analysis.

Deterministic acceptance MUST include at least:

- a same-file `httpx.Client()` binding followed by `.post(...)` outside an accepted owner -> AE002;
- an `httpx.AsyncClient()` binding followed by a representative request method outside an accepted owner -> AE002 when the frozen scanner handles that concrete constructor;
- the existing module/alias `httpx` cases remain detected;
- unrelated objects exposing `.post`, `.request`, or `.stream` remain non-findings;
- the full-tree scan accounts for the current `local_ai_eval/probe_micro_contracts.py` dispatcher through the existing accepted-owner/exception policy rather than silently leaving it invisible. If widening detection exposes any further previously unclassified current-tree httpx client dispatcher, implementation stops for exact-site disposition rather than adding a broad exception.

No new runtime owner, network library, directory-wide exception, or application behavior is authorized.

## Delta 2 — proxy escape at exact-exempted localhost urllib transports

Fresh review also proved that initial loopback validation plus redirect rejection is insufficient with standard urllib behavior. If `HTTP_PROXY`/`HTTPS_PROXY` is configured and the environment does not bypass the loopback host, urllib may dispatch the validated localhost request to an external proxy. `build_opener(...)` also installs proxy handling by default unless it is explicitly disabled.

Before either localhost transport may receive its exact AE002 exception, the implementation MUST make proxy escape fail closed at both existing boundaries:

- `scripts/local_model_structured_output_probe.py::call_ollama_chat`
- `scripts/router_policy_local_responder.py::_stdlib_json_post_client`

The minimum authorized design is a local transport opener that disables environment proxy handling (for example, an opener containing an explicit empty `ProxyHandler({})`) together with the already-required redirect rejection. An equivalently smaller deterministic mechanism is acceptable only if it proves the request cannot be routed through an environment-configured external proxy. Do not add a generic proxy-policy service or modify global process environment state.

Deterministic no-network acceptance MUST include, for both transports:

- hostile proxy environment variables pointing to a representative external proxy while the target URL is valid loopback;
- proof that the configured proxy handler/path is not used and no request is emitted to the proxy;
- the valid loopback request still reaches only the mocked local transport seam;
- redirect rejection remains effective and no external follow-up request occurs;
- redirect-safe/proxy-disabled opener `.open` dispatch remains mechanically visible to AE002 outside the two exact-exempted owner symbols.

## Frozen implementation impact

These deltas do not expand the previously authorized file boundary. They affect only:

- `scripts/check_architecture_enforcement.py` and its focused scanner tests for constructor-bound httpx detection;
- the two already-authorized localhost urllib transport symbols and their focused no-network tests for proxy-disable proof;
- exact current-tree AE002 disposition/config only if the widened scanner exposes a concrete pre-existing dispatcher that must be classified under existing exact-owner rules. No broad or wildcard exception is authorized.

All prior 137 non-goals, exact-exception constraints, provider-import regression coverage, socket datagram coverage, redirect requirements, stable diagnostics, full-tree gate, independent exact-head semantic review, and PROUD gate remain binding.

# 137 AE002-GENERIC-NETWORK-COVERAGE-1 — exact-head review amendment 2

Status: binding planning/readiness amendment

This amendment is additive to the accepted 137 definition/full spec/readiness and the first 2026-09-02 review amendment. Where earlier wording is narrower, this amendment controls. It closes only the material exact-head review gaps identified at head `79435270230473583097416d11ac16bcd4f89168`; it does not authorize a broader network-policy redesign.

## Delta 5 — exact retained-owner identities must be unambiguous

Fresh review proved that the current scanner's `path::bare_function_name` representation can suppress a future class method or nested function with the same bare name as an exempted symbol. Exact retained-owner exceptions therefore MUST NOT rely on an ambiguous bare-name lookup.

The implementation MUST choose the smallest deterministic mechanism that makes every retained exception target unique within its file. Either:

- use qualified lexical identities that include enclosing class/function scope; or
- fail configuration validation closed when an exempted bare name is not unique in that file.

The implementation MUST preserve the existing exact path+symbol exception model and MUST NOT broaden to directory, module, wildcard, substring, decorator, or call-name exemptions.

Deterministic acceptance MUST include a hostile same-file sibling case in which an accepted owner name is duplicated in a class or nested lexical scope and prove that the sibling dispatch is not suppressed. Malformed, missing, or ambiguous retained-owner entries must fail closed with stable diagnostics.

## Delta 6 — urllib3 PoolManager.urlopen dispatch

For a proven same-file `urllib3.PoolManager` binding, both `.request(...)` and `.urlopen(...)` are concrete network-dispatch methods. The implementation MUST classify constructor-bound `PoolManager.urlopen(...)` as AE002 alongside `.request(...)`, including practical alias/from-import constructor forms where resolvable. Unrelated `.urlopen` methods remain non-findings.

Deterministic acceptance MUST include `pool = urllib3.PoolManager(); pool.urlopen("GET", external_url)` outside an accepted owner -> AE002 and an unrelated object exposing `.urlopen(...)` -> non-finding.

This delta adds no retained-owner exception and no implementation path beyond the already-authorized scanner/test boundary.

## Delta 7 — aiohttp ClientSession.ws_connect dispatch

For a proven same-file `aiohttp.ClientSession` binding, `.ws_connect(...)` is a concrete outbound WebSocket dispatch path in addition to the already frozen HTTP request methods. The implementation MUST classify bound `ClientSession.ws_connect(...)` as AE002, including practical alias/from-import constructor forms where resolvable. Unrelated `.ws_connect` methods remain non-findings.

Deterministic acceptance MUST include `session = aiohttp.ClientSession(); await session.ws_connect(external_url)` outside an accepted owner -> AE002 and an unrelated object exposing `.ws_connect(...)` -> non-finding.

This delta adds no retained-owner exception and no implementation path beyond the already-authorized scanner/test boundary.

## Delta 8 — low-level http.client dispatch methods

For proven same-file `http.client.HTTPConnection` / `HTTPSConnection` bindings, low-level methods can create outbound traffic without a `.request(...)` call. The implementation MUST classify:

- `.connect(...)`;
- `.request(...)`;
- `.send(...)` because it may establish the connection when no socket exists; and
- `.endheaders(...)` because after `putrequest(...)` it drives the send path.

Detection remains constructor-provenance-bound. Generic `.send`, `.endheaders`, `.connect`, or `.request` calls on unrelated objects MUST remain non-findings.

Deterministic acceptance MUST include hostile fixtures for bound `HTTPConnection.send(...)` and the `putrequest(...); endheaders(...)` path, plus representative HTTPS and alias/from-import construction. This delta adds no retained-owner exception and no implementation path beyond the already-authorized scanner/test boundary.

## Delta 9 — redirect escape at the exact-exempted httpx transport

The exact `backend/app/modules/local_ai_eval/probe_micro_contracts.py::run_probe_case` retained owner is valid only when both proxy escape and redirect escape are structurally impossible at its dispatch boundary. A caller-supplied `httpx.Client(trust_env=False, follow_redirects=True)` is not safe merely because proxy inheritance is disabled: a validated loopback endpoint may redirect to an external host.

The implementation MUST therefore make redirect safety true for every client that can reach `run_probe_case` dispatch. Use the smallest deterministic design: remove/restrict arbitrary network-capable client injection so the retained owner owns a client with redirects disabled, or fail closed before dispatch unless the supplied seam is structurally constrained to `trust_env=False` (or equivalent proxy-disabled behavior) AND redirects disabled. Do not introspect undocumented/private client state as proof, rely on caller discipline, mutate global environment state, or add a new network-policy service.

Deterministic no-live-network acceptance MUST include:

- a loopback response attempting a 3xx redirect to a representative external URL and proof that no follow-up external request occurs;
- a caller-supplied/default client capable of redirects cannot reach the retained-owner dispatch unless the injection surface has been removed/replaced by a structurally safe seam;
- hostile proxy variables remain unable to route the loopback request externally;
- valid loopback execution still reaches only a mocked/non-network transport seam;
- direct external/malformed endpoint input still fails through the existing endpoint validator before dispatch.

The allowed backend mutation boundary remains only `run_probe_case` and the minimum adjacent `run_probe_suite` client-construction/injection seam required to make both proxy and redirect safety structural.

## Delta 10 — close the complete arbitrary-client routing bypass family

Fresh exact-head review of Delta 9 proves that `trust_env=False` plus `follow_redirects=False` is still not a sufficient safety proof for a caller-supplied `httpx.Client`. Public HTTPX routing controls can independently redirect dispatch through an explicit `proxy=`, proxy-bearing `mounts`, or a caller-selected `transport`; an injected subclass/wrapper can likewise own the dispatch method itself. All of these are the same causal failure mode: an arbitrary network-capable object crosses the exact-exempted `run_probe_case` boundary and can route a validated loopback URL somewhere else.

The bounded sibling sweep for this causal class is therefore frozen here. Before the exact `run_probe_case` AE002 exception is valid, arbitrary `httpx.Client` / `AsyncClient` / compatible network-client injection MUST NOT reach its dispatch boundary. The production path MUST own construction of the concrete HTTPX client used for this localhost probe with environment proxy inheritance disabled and redirects disabled. It MUST NOT accept caller-controlled explicit proxy configuration, proxy mounts, custom network transports, client subclasses/wrappers, or another general-purpose dispatch object at that retained-owner boundary.

For deterministic no-live-network testing, use a separate seam that cannot itself choose network routing. The smallest acceptable shapes are monkeypatching the module-owned HTTPX construction/dispatch in tests, or a narrowly typed response/test hook whose contract cannot carry proxy, mounts, transport, destination, or a general-purpose request method. Do not preserve arbitrary client injection merely for test convenience, and do not introspect private/undocumented HTTPX fields to try to prove an injected client safe.

This delta deliberately resolves the sibling family in one step rather than enumerating only the literal `proxy=` example. It covers the current first-party `run_probe_suite -> run_probe_case` path and direct calls to `run_probe_case`; it does not create a generic HTTPX policy framework or change unrelated application clients.

Deterministic acceptance MUST prove all of the following without live network access:

- the normal probe path constructs/uses only the module-owned client with proxy inheritance disabled and redirects disabled;
- the former arbitrary-client injection path is absent or fails closed before `run_probe_case` dispatch;
- representative explicit proxy, proxy-mount, custom-transport, and client-subclass/wrapper attempts cannot reach the retained-owner dispatch through a caller-controlled network client;
- hostile environment proxy variables still cannot affect dispatch;
- a loopback-to-external redirect still cannot trigger a follow-up request;
- valid loopback execution remains testable through the non-routing test seam and preserves existing probe result semantics.

The allowed backend mutation boundary remains `run_probe_case` plus the minimum adjacent `run_probe_suite` construction/signature/test seam required to remove arbitrary network-client injection. No provider, runtime routing, global egress, schema/store, workflow, frontend, or generic client abstraction change is authorized.

## Frozen completion condition

The eleven exact retained-owner entries remain the complete authorized exception set. No twelfth exception, wildcard, directory owner, new runtime network owner, generic data-flow engine, or network-policy subsystem is authorized.

The 137 implementation is complete only when the full-tree deterministic gate proves the complete frozen concrete family set from the original 137 packet plus both review amendments, including: provider regression coverage; urllib/urllib3; socket connect/datagram paths; aiohttp including `ws_connect`; websockets; http.client including low-level dispatch; module- and constructor-bound httpx/requests including HEAD/OPTIONS and send; exact unambiguous retained-owner identity; strict loopback validation; proxy-disabled and redirect-safe retained local transports; no arbitrary network-capable client injection at `run_probe_case`; stable fail-closed diagnostics; and no live-network dependency in tests.

Any newly exposed current-tree dispatcher not already one of the eleven exact retained owners requires fresh exact-site disposition before implementation merge; it does not authorize automatic exception growth.
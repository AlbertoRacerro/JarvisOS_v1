# 137 AE002-GENERIC-NETWORK-COVERAGE-1

Status: full specification / planning authority

## Purpose

Close the bounded post-134 F5 correctness gap in the already-merged 128 architecture gate: AE002 currently detects a narrow HTTP/provider subset and can miss concrete generic Python network-dispatch families that can create a second external-egress path.

This is repository-development enforcement only. It does not change runtime routing, provider behavior, egress policy, credentials, schemas, stores, domain APIs, or product UI.

## Derivation evidence

Derived from exact master `701b9fa86c20272b9e675961d6231144be111efb` after 136 reconciliation.

Fresh source inspection confirms `scripts/check_architecture_enforcement.py::_scan_python` currently classifies as AE002 only:

- `httpx` / `requests` methods `get`, `post`, `put`, `patch`, `delete`, `request`, `stream`; and
- provider-import calls ending in `.complete`.

The existing focused tests in `backend/tests/test_architecture_enforcement_gate.py` prove aliased `httpx` and provider `.complete()` behavior but do not prove `urllib.request`, `urllib3`, raw socket dispatch, `aiohttp`, `websockets`, or `http.client`.

The current `_call_name` resolver handles names/attributes and import aliases but loses constructor/instance provenance for expressions such as `urllib3.PoolManager().request(...)`, `aiohttp.ClientSession().get(...)`, and `http.client.HTTPConnection(...).request(...)`. It also mis-normalizes an unaliased dotted import such as `import urllib.request` because the bound top-level name and imported module path are currently conflated. Merely adding string prefixes to the existing `external` expression is therefore insufficient.

Current-head review additionally proves that import normalization cannot overwrite the scanner's separate full-module knowledge: today `provider_import` relies on the full imported target retained in `_aliases`. Correcting `import urllib.request` by mapping only the Python-bound top-level name would otherwise make an unaliased `import app.modules.ai.providers.foo` invisible to the existing provider `.complete()` detector. The implementation must therefore keep bound-name resolution and full imported-module inventory as separate deterministic facts, with a regression fixture for unaliased dotted provider imports.

### Existing dispatch inventory that the widened scanner will expose

Fresh exact-master inspection of every current `urlopen` occurrence proves ten retained symbols across six files. They are not accidental newly-created bypasses and must not be discovered only after implementation makes the full-tree gate red:

| Exact symbol | Existing purpose | Frozen disposition |
| --- | --- | --- |
| `scripts/cheap_review.py::gh_request` | repository review/control-plane GitHub API request | exact AE002 exception; existing review tooling |
| `scripts/cheap_review.py::call_model` | explicit review-model transport | exact AE002 exception; existing review tooling |
| `scripts/cheap_review.py::call_model_with_retry` | explicit bounded review-model retry transport | exact AE002 exception; existing review tooling |
| `scripts/daily_development_continuation.py::_request` | 079 continuation control-plane GitHub API read | exact AE002 exception; owner 079 |
| `scripts/daily_development_continuation.py::_load_jwks` | 079 trusted GitHub OIDC JWKS read | exact AE002 exception; owner 079 |
| `scripts/daily_development_continuation.py::_post_comment` | 079 bounded continuation marker GitHub API write | exact AE002 exception; owner 079 |
| `scripts/verify_merge_authority.py::_request_json` | 134 read-only GitHub merge-authority verification | exact AE002 exception; owner 134 |
| `scripts/codex_pr_autopush.py::gh_request` | bounded 022/Codex PR actuator GitHub API request | exact AE002 exception; owner 022 |
| `scripts/local_model_structured_output_probe.py::call_ollama_chat` | evaluation-only Ollama probe | exact AE002 exception only after the same implementation constrains its URL boundary to loopback |
| `scripts/router_policy_local_responder.py::_stdlib_json_post_client` | localhost-only Ollama responder behind endpoint validation | exact AE002 exception; localhost-only routing evaluation tooling |

The local structured-output probe is not currently safe to classify as localhost-only merely because its default URL is localhost: `call_ollama_chat(..., url=...)` accepts an arbitrary caller-supplied URL and dispatches it through `urllib.request`. Before its exact AE002 exception becomes valid, this slice must add a deterministic fail-closed loopback URL check at that function boundary. The check is limited to this evaluation script and is not new application/runtime egress policy.

The existing exception schema is exact `path::symbol`, validates that the target symbol exists, and forbids wildcards. These ten narrow retained-owner declarations therefore do not suppress sibling functions or future call sites. No directory-wide owner, wildcard, generic `urlopen` exemption, or new runtime egress owner is authorized.

If implementation exposes any additional pre-existing newly-detected dispatch outside these ten exact symbols, it must stop and re-derive that call site rather than silently widening the exception list.

## Authority and dependencies

Depends on merged 128 and 134. 128 remains the owner of AE002 semantics. This slice is a corrective extension of that accepted rule family, not a second network policy engine.

Implementation authority exists only after an accepted readiness decision and `STATUS.md=ready`.

## Required behavior

1. Extend the existing AST-based AE002 classifier to cover concrete first-party direct-dispatch families:
   - `urllib.request`: at least `urlopen`, including module alias and from-import forms;
   - `urllib3`: direct/module request calls and `PoolManager`/equivalent constructor-bound `.request` dispatch;
   - `socket`: `create_connection` and constructor-bound `socket(...).connect` / `connect_ex` / `sendto`, plus destination-bearing `sendmsg(..., address)` on platforms that expose it; `sendto` and destination-bearing `sendmsg` are required because datagram egress can transmit to an external destination without a prior connect;
   - `aiohttp`: module/session request methods (`request`, `get`, `post`, `put`, `patch`, `delete`, `head`, `options`) when reached through a concrete `ClientSession` binding or direct module API;
   - `websockets`: `connect` dispatch, including alias/from-import forms;
   - `http.client`: constructor-bound HTTP/HTTPS connection `.request` and `.connect` dispatch.
2. Reuse and correct the current import-alias resolver. Unaliased dotted imports must resolve according to Python binding semantics (`import urllib.request` binds `urllib`, while `import urllib.request as ur` binds `ur` to the full module). Preserve a separate full imported-module inventory so existing provider-import `.complete()` detection remains effective for unaliased dotted provider imports. Add only the minimum bounded local call-target/binding normalization needed to identify constructor-bound network objects in the same Python source file.
3. Preserve accepted external owners exactly as today: `backend/app/modules/ai/providers/` and `backend/app/modules/local_ai/`.
4. Preserve exact exception semantics and stable diagnostics. Add only the ten inventoried exact AE002 retained-owner entries above; `scripts/local_model_structured_output_probe.py::call_ollama_chat` may be exempted only together with the loopback boundary below. No other config broadening is authorized by this readiness packet.
5. Constrain `scripts/local_model_structured_output_probe.py::call_ollama_chat` to deterministic loopback destinations before its retained-owner exception applies. Parse the supplied URL without DNS/network lookup; accept `localhost` or an IP address for which Python's standard-library IP classification is loopback; reject malformed/missing hosts, user-info ambiguity, and non-loopback hosts before constructing or sending the request. Preserve the current default localhost behavior.
6. Unknown or unresolvable dynamic calls are not to be guessed into semantic authority. The implementation should cover the frozen concrete patterns above and document residual dynamic-dispatch risk rather than invent a generic taint engine.
7. No source-text/regex-only substitute for AST ownership classification.

## Allowed implementation paths

- `scripts/check_architecture_enforcement.py`
- `backend/tests/test_architecture_enforcement_gate.py`
- `configs/architecture_enforcement.json` only for the ten exact inventoried AE002 retained-owner entries above; any eleventh new AE002 exception requires fresh authority.
- `scripts/local_model_structured_output_probe.py` only for the bounded deterministic loopback URL validation required above.
- a focused existing/new test for that script's URL-boundary behavior, with no network call.
- normal lifecycle bookkeeping in `docs/specs/STATUS.md`.

No runtime `backend/app/**`, frontend, workflow, provider, database, schema/migration, or product code mutation is authorized.

## Deterministic acceptance matrix

The focused test surface must prove at least:

| Family | Required hostile fixture |
| --- | --- |
| urllib.request | unaliased dotted module import, alias import, and from-import `urlopen` outside accepted owner -> AE002 |
| urllib3 | module/alias request and constructor-bound `PoolManager().request` -> AE002 |
| socket | `create_connection` plus constructor-bound `.connect`/`.connect_ex`/`.sendto` and destination-bearing `.sendmsg(..., address)` -> AE002 |
| aiohttp | `ClientSession` binding and request verb/session `.request` dispatch -> AE002 |
| websockets | module alias and from-import `connect` -> AE002 |
| http.client | HTTP/HTTPS connection binding followed by `.request`/`.connect` -> AE002 |
| provider regression | unaliased dotted `app.modules.ai.providers...` import followed by `.complete()` outside accepted owner still -> AE002 |
| exact accepted owner | the same concrete dispatch patterns under an accepted owner remain non-findings |
| ten retained symbols | full-tree scan remains green only because the ten inventoried existing call sites are exact symbol-scoped exceptions, with the local probe guarded first |
| local probe boundary | default/explicit loopback URL accepted; representative external host, malformed/missing host, and user-info ambiguity rejected before dispatch |
| exact exception | one exact symbol exemption does not cover a sibling symbol |
| stability | repeated scan of identical fixture tree yields identical diagnostics |

Alias coverage must include ordinary `import X as Y` and `from X import Y as Z` forms where applicable, plus the Python semantics of unaliased dotted imports.

## Required gates

- `python scripts/check_architecture_enforcement.py --self-test`
- focused `backend/tests/test_architecture_enforcement_gate.py`
- focused no-network local-probe URL-boundary test
- normal repository architecture gate / required PR CI on the frozen implementation head
- independent exact-head semantic review because this changes an architecture enforcement gate

## Failure modes to prevent

- apparent coverage added only for simple dotted calls while constructor-bound calls still bypass AE002;
- datagram `socket.sendto` or destination-bearing `socket.sendmsg` remains a direct egress bypass because neither needs a prior connection;
- alias normalization duplicates dotted module components and causes false negatives for `import urllib.request`;
- alias normalization fixes `urllib.request` but silently disables existing unaliased dotted provider `.complete()` detection;
- the local structured-output probe is exempted as "localhost-only" while still accepting arbitrary external URLs;
- a broad method-name rule flags unrelated `.connect()` / `.request()` calls as external dispatch;
- accepted-owner behavior changes unintentionally;
- newly detected legacy calls are hidden by broad exceptions instead of exact audited dispositions;
- scanner becomes a broad data-flow/taint framework beyond the bounded concrete patterns;
- nondeterministic binding resolution changes diagnostics between scans.

## Non-goals

- no application/runtime egress repair; 129 already owns accepted execution-spine closure;
- no generic interprocedural taint analysis;
- no JavaScript/TypeScript network scanner expansion in this repair;
- no new provider/network library;
- no change to AE001/AE003/AE004 except shared helper code only when strictly required and behavior-preserving;
- no cleanup/refactor unrelated to AE002 coverage or the one retained local-probe boundary required to make its exception truthful;
- no implementation of F7-F10 or 118+.

## Minimum-necessary test

The gap is inside one existing static scanner and one focused deterministic test surface. Extending those owners with bounded call-target/binding recognition, preserving provider-import detection, adding ten exact pre-existing owner dispositions, and making the one falsely-local retained owner actually fail closed to loopback is the smallest corrective action that closes the named bypasses without turning current sanctioned control/local tooling into surprise gate debt. A new policy service, runtime instrumentation, dependency graph, directory-wide allowlist, or broad linter framework would be disproportionate and is not authorized.

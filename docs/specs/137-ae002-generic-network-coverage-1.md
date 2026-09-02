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

The current `_call_name` resolver handles names/attributes and import aliases but loses constructor/instance provenance for expressions such as `urllib3.PoolManager().request(...)`, `aiohttp.ClientSession().get(...)`, and `http.client.HTTPConnection(...).request(...)`. Therefore merely adding string prefixes to the existing `external` expression is insufficient.

## Authority and dependencies

Depends on merged 128 and 134. 128 remains the owner of AE002 semantics. This slice is a corrective extension of that accepted rule family, not a second network policy engine.

Implementation authority exists only after an accepted readiness decision and `STATUS.md=ready`.

## Required behavior

1. Extend the existing AST-based AE002 classifier to cover concrete first-party direct-dispatch families:
   - `urllib.request`: at least `urlopen`, including module alias and from-import forms;
   - `urllib3`: direct/module request calls and `PoolManager`/equivalent constructor-bound `.request` dispatch;
   - `socket`: `create_connection` and constructor-bound `socket(...).connect` / `connect_ex`;
   - `aiohttp`: module/session request methods (`request`, `get`, `post`, `put`, `patch`, `delete`, `head`, `options`) when reached through a concrete `ClientSession` binding or direct module API;
   - `websockets`: `connect` dispatch, including alias/from-import forms;
   - `http.client`: constructor-bound HTTP/HTTPS connection `.request` and `.connect` dispatch.
2. Reuse the current import-alias resolver. Add only the minimum bounded local call-target/binding normalization needed to identify constructor-bound network objects in the same Python source file.
3. Preserve accepted external owners exactly as today: `backend/app/modules/ai/providers/` and `backend/app/modules/local_ai/`.
4. Preserve exact exception semantics and stable diagnostics. Do not broaden `configs/architecture_enforcement.json` merely to keep the gate green.
5. Unknown or unresolvable dynamic calls are not to be guessed into semantic authority. The implementation should cover the frozen concrete patterns above and document residual dynamic-dispatch risk rather than invent a generic taint engine.
6. No source-text/regex-only substitute for AST ownership classification.

## Allowed implementation paths

- `scripts/check_architecture_enforcement.py`
- `backend/tests/test_architecture_enforcement_gate.py`
- `configs/architecture_enforcement.json` only if fresh exact evidence proves an existing retained debt entry is required; broadening is not expected.
- normal lifecycle bookkeeping in `docs/specs/STATUS.md`.

No runtime `backend/app/**`, frontend, workflow, provider, database, schema/migration, or product code mutation is authorized.

## Deterministic acceptance matrix

The focused test surface must prove at least:

| Family | Required hostile fixture |
| --- | --- |
| urllib.request | module import, alias import, and from-import `urlopen` outside accepted owner -> AE002 |
| urllib3 | module/alias request and constructor-bound `PoolManager().request` -> AE002 |
| socket | `create_connection` plus constructor-bound `.connect`/`.connect_ex` -> AE002 |
| aiohttp | `ClientSession` binding and request verb/session `.request` dispatch -> AE002 |
| websockets | module alias and from-import `connect` -> AE002 |
| http.client | HTTP/HTTPS connection binding followed by `.request`/`.connect` -> AE002 |
| exact accepted owner | the same concrete dispatch patterns under an accepted owner remain non-findings |
| exact exception | one exact symbol exemption does not cover a sibling symbol |
| stability | repeated scan of identical fixture tree yields identical diagnostics |

Alias coverage must include ordinary `import X as Y` and `from X import Y as Z` forms where applicable.

## Required gates

- `python scripts/check_architecture_enforcement.py --self-test`
- focused `backend/tests/test_architecture_enforcement_gate.py`
- normal repository architecture gate / required PR CI on the frozen implementation head
- independent exact-head semantic review because this changes an architecture enforcement gate

## Failure modes to prevent

- apparent coverage added only for simple dotted calls while constructor-bound calls still bypass AE002;
- alias normalization maps `import urllib.request` incorrectly and causes false negatives;
- a broad method-name rule flags unrelated `.connect()` / `.request()` calls as external dispatch;
- accepted-owner behavior changes unintentionally;
- new exceptions are added instead of fixing detection;
- scanner becomes a broad data-flow/taint framework beyond the bounded concrete patterns;
- nondeterministic binding resolution changes diagnostics between scans.

## Non-goals

- no runtime egress repair; 129 already owns accepted execution-spine closure;
- no generic interprocedural taint analysis;
- no JavaScript/TypeScript network scanner expansion in this repair;
- no new provider/network library;
- no change to AE001/AE003/AE004 except shared helper code only when strictly required and behavior-preserving;
- no cleanup/refactor unrelated to AE002 coverage;
- no implementation of F7-F10 or 118+.

## Minimum-necessary test

The gap is inside one existing static scanner and one focused deterministic test surface. Extending those two owners with bounded call-target/binding recognition is the smallest corrective action that actually prevents the named bypasses. A new policy service, runtime instrumentation, dependency graph, or broad linter framework would be disproportionate and is not authorized.

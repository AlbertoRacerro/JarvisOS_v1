# 1G-B2-F3-A4 - Approved Local Responder Adapter Smoke

## Summary

A4 adds a localhost-only Ollama `/api/generate` responder adapter that can be
injected into the A3 local-route smoke path.

## Start

- start HEAD: `e620de4d7df65ad5b35c80fe9bf2398fbdaccd58`
- implementation base HEAD: `e620de4d7df65ad5b35c80fe9bf2398fbdaccd58`
- working tree status before commit: clean before implementation

## Adapter

- module: `scripts/router_policy_local_responder.py`
- builder: `build_local_responder(...) -> Callable[[str], str]`
- call function: `call_local_ollama_generate(prompt, ...) -> str`
- client contract: `client(endpoint: str, payload: dict, timeout_s: float) -> dict`
- builder side effects: none

## Endpoint Validation

- parser: `urllib.parse.urlparse`
- scheme: `http`
- allowed hosts: `127.0.0.1`, `localhost`, `::1`
- required path: `/api/generate`
- rejects credentials, query strings, and fragments
- rejects non-localhost endpoints and localhost-like suffixes

## Bounds And Determinism

- prompt must be `str`
- prompt length above `max_prompt_chars` is rejected before client call
- output is sliced to `max_output_chars`
- temperature must be `0.0`
- payload uses `stream=false`
- payload contains no tool, memory, retrieval, decision, or provider metadata

## CLI Mode

`--run-local` constructs the local responder and injects it into
`run_local_route`. It does not bypass RouterPolicy decision production,
semantic validation, or the A3 safe-local guard.

Default CLI/library behavior remains offline-safe. `responder=None` does not
call a model.

## Offline Test Strategy

Unit tests use fake clients and patched `urllib.request.urlopen` only. They do
not require Ollama, Gemma, or any real model server.

## Runtime Boundary

- real local calls made during tests: `false`
- external calls made: `false`
- provider API calls made: `false`
- tool/browser/terminal/MCP execution added: `false`
- memory/retrieval/file writes added: `false`
- backend routes added: `false`
- frontend UI added: `false`
- database migrations added: `false`
- BlueRev modeling added: `false`

## Residual Risks

- A4 does not approve broad runtime RouterPolicy routing.
- A4 does not add a backend route or UI for local responder use.
- Manual smoke depends on Ollama running and the selected model already being pulled.
- Responder metadata and richer response contracts remain deferred.

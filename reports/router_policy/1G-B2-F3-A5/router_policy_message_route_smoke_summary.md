# 1G-B2-F3-A5 - Real Message Input To Local-Route Smoke

## Summary

A5 adds a controlled real-message smoke bridge:

```text
message_text
-> smoke-only RouterPolicyInput v0_3_1_1
-> run_local_route(...)
-> injected/local responder only if all A3/A4 gates pass
```

## Start

- start HEAD: `56d7266f34c7faaf452e539425a2c3e4ef2bceff`
- implementation base HEAD: `56d7266f34c7faaf452e539425a2c3e4ef2bceff`
- working tree status before commit: clean before implementation

## Normalizer Status

- complete production message normalizer found: `false`
- smoke-only fallback used: `true`
- production Phase A/B normalizer added: `false`
- schema validation unavailable; structural checks only

## Gating

- arbitrary `--message` defaults to no-execution
- `--run-local` alone does not make fallback input executable
- safe fallback CLI execution requires `--assume-public-simple --run-local`
- `assume_public_simple` does not override deterministic hard-gate signals
- `assume_public_simple_used` is included in results

## Message Safety

- `input_obj["message_text"]` is the original message string
- responder receives exactly `input_obj["message_text"]`
- decision JSON, audit notes, reports, memory, retrieval data, and file contents are not sent as prompt

## Structural Validation

A5 validates the producer-used RouterPolicy input shape before calling A3:

- required top-level sections
- `message_text` equality
- Phase A hard booleans and hard reason-code mapping
- router/action critical strings, enums, booleans, and token count
- user/provider/budget/context metadata fields

This is not full Draft 2020-12 validation.

## CLI Output Redaction

- no full input object
- no raw message on no-execution
- no full decision JSON
- no audit notes
- no response when `executed=false`
- bounded response when `executed=true`

## Runtime Boundary

- real local calls made during tests: `false`
- external calls made: `false`
- provider API calls made: `false`
- non-localhost network calls added: `false`
- tool/browser/terminal/MCP execution added: `false`
- memory/retrieval/file writes added: `false`
- backend routes added: `false`
- frontend UI added: `false`
- database migrations added: `false`
- BlueRev modeling added: `false`

## Residual Risks

- A5 is not production Phase A/B normalization.
- No complete production message normalizer was found.
- RouterPolicy input validation is structural only, not full Draft 2020-12 schema validation.
- Smoke hard-gate detection is conservative and not a general classifier.
- Manual smoke depends on Ollama running and the selected model already being pulled.

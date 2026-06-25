# 1G-B2-F3-C1 - Dev Message Route Endpoint Smoke

## Summary

C1 adds a dev-only backend endpoint for the existing RouterPolicy message-route
smoke path:

```text
POST /api/dev/message-route-smoke
```

The endpoint is disabled by default and returns `404` unless
`JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE` is truthy.

## Contract

- `assume_public_simple` is server-side only through
  `JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE`.
- `run_local_responder` is request-controlled but additionally server-gated by
  `JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER`.
- model, endpoint, and timeout are server-side only:
  `JARVISOS_DEV_MESSAGE_ROUTE_MODEL`,
  `JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT`,
  `JARVISOS_DEV_MESSAGE_ROUTE_TIMEOUT_S`.
- request body forbids extra fields.
- message length cap is `12000`.
- response projection reuses `_safe_cli_result(result)`.
- endpoint response adds only `trace_id` and `audit_ref=null`.
- `input_obj`, full RouterPolicy decision, raw audit notes, memory/retrieval
  data, provider metadata, and tool payloads are not returned.
- `input_source` is dropped from endpoint responses.

## Observed Results

| Check | Result |
|---|---|
| import safety | no model call, responder build, or smoke call at import |
| disabled default | `404`, no smoke call, no responder build |
| benign default | no execution without server-side `assume_public_simple` |
| local responder | requires request flag and server env gate |
| hard gates | hard-gated messages did not execute |
| operational gates | provider/tool/MCP/browser/terminal intents did not execute |
| unsupported fields | rejected by request schema |
| internal exception | safe `500` with `internal_error` and coarse `error_type` |
| side effects | no DB, event, artifact, memory, or retrieval writes observed |
| frontend | unchanged |

## Tests

```text
cd backend; .\.venv\Scripts\python -m pytest tests\test_dev_message_route_smoke.py -q
42 passed

cd backend; .\.venv\Scripts\python -m pytest -q
367 passed

python -m unittest tests.test_router_policy_message_route_smoke
84 tests OK

python -m unittest tests.test_router_policy_hint_bridge_probe
15 tests OK

python -m unittest tests.test_router_policy_local_route_probe
11 tests OK

python -m unittest tests.test_router_policy_decision_probe
14 tests OK

python -m unittest tests.test_router_policy_semantic_validator
40 tests OK

python -m unittest discover -s tests
330 tests OK
```

## Boundary

C1 is a dev smoke endpoint, not production chat. It does not approve production
UI, memory runtime, retrieval runtime, provider routing, tool/MCP/browser/
terminal execution, live Qwen Phase B exposure, or BlueRev runtime behavior.

Known residual risk: the dev endpoint must not be enabled on a LAN- or
internet-exposed backend.

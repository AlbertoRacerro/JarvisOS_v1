# 1G-B2-F3-C1-R1 - Safe Validation Boundary

## Summary

C1-R1 moves request-body parsing and Pydantic validation for
`POST /api/dev/message-route-smoke` behind the dev gate. Disabled requests now
return the disabled safe response before JSON parsing or schema validation.
Enabled invalid JSON and schema-invalid requests return a safe validation-error
projection.

## Boundary

- validation strategy: `manual_parse_after_dev_gate`
- global `RequestValidationError` handler added: no
- manual validation exception type: `pydantic.ValidationError`
- route generates one `trace_id` per request
- adapter accepts the route `trace_id`
- adapter no longer generates an internal C1 trace id
- internal adapter/runtime exceptions preserve the route `trace_id`
- `_safe_cli_result` remains the response projection boundary
- `assume_public_simple` remains server-side only
- local responder remains server-gated
- live Qwen Phase B remains unexposed

## Observed Results

| Check | Result |
|---|---|
| disabled schema-invalid request | safe disabled `404` |
| enabled oversized sensitive message | safe `validation_error`, no raw secret |
| enabled unsupported extra field | safe `validation_error` |
| enabled malformed JSON | safe `validation_error` |
| enabled empty body | safe `validation_error` |
| validation failure path | `422`, not `internal_error` |
| fixed trace id | same id across disabled, validation, normal, responder, and internal-error paths |
| internal adapter exception | safe `500`, no exception message |

## Tests

```text
cd backend
.\.venv\Scripts\python -m pytest tests\test_dev_message_route_smoke.py -q
52 passed

.\.venv\Scripts\python -m pytest -q
377 passed

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

python -m json.tool reports/router_policy/1G-B2-F3-C1-R1/router_policy_dev_message_route_validation_boundary_summary.json
valid JSON
```

## Residual Risk

C1-R1 remains a dev smoke endpoint, not production chat. It does not approve
production UI, memory runtime, retrieval runtime, provider routing,
tool/MCP/browser/terminal execution, live Qwen Phase B exposure, or BlueRev
runtime behavior.

The disabled dev endpoint response still exposes limited server config state
through fields such as `assume_public_simple_used`. A future cleanup should make
disabled responses more inert if stricter endpoint-hiding is required.

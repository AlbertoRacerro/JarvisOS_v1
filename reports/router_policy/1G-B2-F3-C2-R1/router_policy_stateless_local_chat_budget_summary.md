# 1G-B2-F3-C2-R1 - Local Chat Budget And A4 Truncation Metadata

## Summary

C2-R1 explicitly crosses the A4 local responder boundary to expose measured
local responder output truncation without duplicating Ollama POST logic.

The existing A4 public API remains stable:

```text
build_local_responder(...) -> Callable[[str], str]
call_local_ollama_generate(...) -> str
```

The new metadata helper shares the same validation, payload construction, POST,
response parse, and output bounding path.

## Budget

- local-chat prompt char limit: `32000`
- local-chat output char limit: `16000`
- no extra `4000` char cap in the local-chat layer
- recent clean history is selected within the prompt budget
- omitted clean turns are reported in `context_filter`

The prompt budget is a conservative char-based adapter limit, not the model
token context window and not long-term memory.

## Truncation Semantics

`response_truncated=false` means JarvisOS/local responder did not slice the
returned response due to `max_output_chars`. It does not guarantee the model's
answer is semantically complete.

## A4 Boundary

| Field | Value |
|---|---|
| A4 modified | true |
| boundary crossing declared | true |
| localhost-only invariants preserved | true |
| validation before POST preserved | true |
| existing public API preserved | true |
| duplicate Ollama POST logic | false |
| metadata path uses same validation path | true |

## Tests

```text
cd backend
.\.venv\Scripts\python -m pytest tests\test_dev_local_chat.py -q
19 passed

python -m unittest tests.test_router_policy_local_responder
20 tests OK

.\.venv\Scripts\python -m pytest tests\test_dev_message_route_smoke.py -q
52 passed

.\.venv\Scripts\python -m pytest -q
396 passed

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
337 tests OK

python -m json.tool reports/router_policy/1G-B2-F3-C2-R1/router_policy_stateless_local_chat_budget_summary.json
valid JSON
```

## Residual Risks

C2-R1 does not add streaming, continuation, pagination, a backend response
buffer, model-token-window metering, persistent memory, retrieval, provider
routing, frontend UI, or production chat.

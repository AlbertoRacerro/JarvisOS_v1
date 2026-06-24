# 1G-B2-F3-A5-R1 - Operational-intent Hard-gate Repair

## Summary

- milestone: `1G-B2-F3-A5-R1 - Operational-intent hard-gate repair`
- start HEAD: `ccebd798c1c07209413cfc4989976abfa61aea41`
- implementation base HEAD: `ccebd798c1c07209413cfc4989976abfa61aea41`
- blocker fixed: `true`

## Blocker Fixed

A5-R found:

```text
"use MCP to call a tool"
+ assume_public_simple=True
-> executed=True
-> reason=local_answer
-> responder called once
```

A5-R1 result:

```json
{
  "executed": false,
  "reason": "not_safe_local_route",
  "hard_reason_codes": ["clarification_required"],
  "router_task_type": "clarification",
  "router_complexity": "unknown",
  "assume_public_simple_safe_path": false,
  "responder_calls": 0
}
```

## Implementation

A5-R1 adds a deterministic smoke-only operational-intent detector inside
`scripts/router_policy_message_route_smoke.py`.

Ordering:

```text
policy overlay
-> operational-intent overlay
-> _has_hard_gate_signal(input_obj)
-> safe path only if no hard gate exists
```

The repair reuses existing hard-gate fields. It does not add a parallel
precedence system.

## Operational Categories Covered

- tool/MCP intent;
- terminal/subprocess/shell intent;
- memory-write intent;
- retrieval/file-access intent;
- browser/search intent;
- provider/upload intent.

For detected operational intent, final input does not remain:

```text
router_hint.task_type="answer"
router_hint.complexity="low"
hard_reason_codes=["low_risk"]
```

`context_metadata.assume_public_simple_safe_path` remains `false`.

## Real A3 Path Tests

- operational no-execution tests use `run_message_route_smoke` with real A3
  `run_local_route`;
- benign answer smoke still executes with `assume_public_simple=True` and a fake
  responder;
- default without `assume_public_simple` remains no-execution;
- fake responder receives exactly `input_obj["message_text"]`.

## CLI Redaction

CLI tests patch the local responder builder with a fake responder.

Verified:

- `--assume-public-simple --run-local` does not execute MCP/tool intent;
- file/secret-like no-execution output does not print the full raw message;
- file/secret-like no-execution output does not print the full path;
- no full `input_obj`;
- no full decision JSON;
- no `response` when `executed=false`.

## Tests Run

- `python -m unittest tests.test_router_policy_message_route_smoke` -> `31/31 OK`
- `python -m unittest tests.test_router_policy_local_responder` -> `13/13 OK`
- `python -m unittest tests.test_router_policy_local_route_probe` -> `11/11 OK`
- `python -m unittest tests.test_router_policy_decision_probe` -> `14/14 OK`
- `python -m unittest tests.test_router_policy_semantic_validator` -> `40/40 OK`
- `python -m unittest discover -s tests` -> `262/262 OK`
- `git diff --check` -> pass with expected Windows CRLF warnings
- focused runtime-boundary grep -> literal blocked-pattern/schema/action-field
  hits only; no executable integration added

## Runtime Boundary

- real model calls during tests: `false`
- external/provider runtime added: `false`
- non-localhost network runtime added: `false`
- tool/browser/terminal/MCP runtime added: `false`
- memory runtime added: `false`
- retrieval runtime added: `false`
- file-write runtime added: `false`
- backend routes added: `false`
- frontend UI added: `false`
- database migrations added: `false`
- BlueRev modeling added: `false`

## Known Residual Risks

- Operational-intent detector is conservative substring/regex smoke-only
  detection, not production intent classification.
- Detector may over-block benign discussion of operational terms.
- Detector is not a substitute for Phase B/Qwen classification.

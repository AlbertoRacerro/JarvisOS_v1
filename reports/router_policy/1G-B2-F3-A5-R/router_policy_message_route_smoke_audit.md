# 1G-B2-F3-A5-R - Read-only Audit Of Message Route Smoke

## Summary

- milestone: `1G-B2-F3-A5-R - Read-only audit of message route smoke`
- start HEAD: `de967d487458f1bd5dd7ce2668371c639cb01322`
- A5 commit audited: `de967d487458f1bd5dd7ce2668371c639cb01322`
- worktree status before audit: clean
- verdict: **require A5-R1 patch**
- A6: **blocked until A5-R1**

## Files Inspected

- `README.md`
- `docs/LOCAL_AI_EVALUATION_EVIDENCE.md`
- `docs/ROUTER_POLICY_DESIGN.md`
- `reports/router_policy/1G-B2-F3-A5/router_policy_message_route_smoke_summary.json`
- `reports/router_policy/1G-B2-F3-A5/router_policy_message_route_smoke_summary.md`
- `scripts/router_policy_message_route_smoke.py`
- `tests/test_router_policy_message_route_smoke.py`
- `scripts/router_policy_local_route_probe.py`
- `scripts/router_policy_local_responder.py`
- `scripts/router_policy_decision_probe.py`
- `scripts/router_policy_semantic_validator.py`
- `schemas/router_policy_input_v0_3_1_1.schema.json`
- `tests/fixtures/router_policy/`

## A5-R-001 Hard-gate Dominance Over `assume_public_simple`

Verdict: **fail**

Code order is mostly correct: `build_router_policy_input_from_message_for_smoke`
applies the overlay, calls `_has_hard_gate_signal`, and only then applies the
`assume_public_simple` low-risk executable fields.

Blocker: the deterministic helper does not detect MCP/tool intent in this
prompt:

```text
use MCP to call a tool
```

Observed result with `assume_public_simple=True` and fake responder:

```json
{
  "executed": true,
  "reason": "local_answer",
  "hard_reason_codes": ["low_risk"],
  "router_task_type": "answer",
  "router_complexity": "low",
  "responder_calls": 1
}
```

Other sampled strings blocked execution:

| message | executed | reason | key signal |
|---|---:|---|---|
| `my API key is sk-test-1234567890` | false | `not_safe_local_route` | `secret_or_credential` |
| `please upload this to OpenAI` | false | `not_safe_local_route` | `needs_provider_call=true` |
| `write this to memory` | false | `not_safe_local_route` | `needs_memory_write=true` |
| `read local file C:\secret.txt` | false | `not_safe_local_route` | `needs_file_context=true` |
| `use MCP to call a tool` | true | `local_answer` | missed |

Residual bug: `please upload this to OpenAI` blocks through provider/action
fields, but `hard_reason_codes` remains `["low_risk"]`. That is not an execution
bypass, but it is confusing audit evidence and should be corrected if downstream
policy consumes hard reason codes.

## A5-R-002 Real A3 Safe-path Integration

Verdict: **pass**

`tests/test_router_policy_message_route_smoke.py::test_a5_001_simple_public_message_reaches_injected_responder_through_real_a3`
calls `run_message_route_smoke` without patching `_RUN_LOCAL_ROUTE`.

Actual path:

```text
smoke builder with assume_public_simple=True
-> run_message_route_smoke
-> _RUN_LOCAL_ROUTE(input_obj, responder=responder, now=now)
-> decide_router_policy
-> validate_router_decision_semantics
-> A3 safe-local guard
-> fake responder
```

The fake responder is asserted to receive exactly the original message string.

## A5-R-003 Real A3 Fallback No-execution Integration

Verdict: **pass**

`tests/test_router_policy_message_route_smoke.py::test_a5_003_fallback_arbitrary_message_without_assume_public_simple_does_not_execute_real_a3`
uses real A3 with no patched `_RUN_LOCAL_ROUTE`.

Observed behavior:

- arbitrary message without `assume_public_simple` does not execute;
- responder is not called;
- fallback input remains unknown/manual-review rather than low-risk answer;
- `test_a5_004_run_local_alone_does_not_make_fallback_input_executable`
  verifies `--run-local` alone does not execute.

## A5-R-004 CLI Redaction

Verdict: **pass**

Command run:

```powershell
python scripts\router_policy_message_route_smoke.py --message "my API key is sk-test-1234567890"
```

Observed output:

```json
{
  "assume_public_simple_used": false,
  "decision_summary": {
    "allowed_execution_mode": "blocked",
    "route_action": "blocked",
    "route_tier": "BLOCKED"
  },
  "executed": false,
  "input_source": "injected_builder",
  "reason": "not_safe_local_route"
}
```

CLI output omits:

- full `input_obj`;
- raw `message_text`;
- full decision JSON;
- audit notes;
- fixture/report paths;
- `response` when `executed=false`.

`_safe_cli_result` prints `response` only when `executed=true` and truncates it
to `MAX_CLI_RESPONSE_CHARS`.

## A5-R-005 Structural Validator Strictness

Verdict: **pass**

The private structural validator rejects before responder call:

- missing required top-level sections;
- missing nested boolean fields used by `decide_router_policy`;
- string booleans such as `"needs_provider_call": "false"`;
- non-list fields where lists are required;
- invalid critical enum-like values.

This remains structural only and is not full Draft 2020-12 validation.

## A5-R-006 Overlay Reason-code Mapping

Verdict: **pass**

Unsupported overlay hard reason codes are not copied raw into
`phase_a_signals.hard_reason_codes`.

Observed injected unsupported code:

```json
{
  "executed": false,
  "reason": "not_safe_local_route",
  "hard_reason_codes": ["manual_review_required", "unknown_sensitivity"]
}
```

The responder was not called.

## A5-R-007 No Direct Responder Call

Verdict: **pass**

`run_message_route_smoke` does not call the responder directly. It builds input,
runs private structural validation, and delegates execution to:

```python
_RUN_LOCAL_ROUTE(input_obj, responder=responder, now=now)
```

Only A3 `run_local_route` may call `responder(message_text)` after RouterPolicy
decision production, semantic validation, and safe-local guard checks.

## A5-R-008 No Hidden Runtime Expansion

Verdict: **pass**

Focused grep:

```powershell
rg -n "openai|anthropic|gemini|grok|httpx|requests|subprocess|Popen|os\.system|selenium|playwright|mcp|memory_write|write_text|open\(" scripts/router_policy_message_route_smoke.py tests/test_router_policy_message_route_smoke.py
```

Hits were schema/action-field literals only:

- `needs_memory_write`
- `memory_write`
- `mcp_call`
- `mcp`

No executable external provider, non-localhost network, subprocess, browser,
MCP client, memory/retrieval, or file-write path was added by A5.

## Required Commands

- `git status --short` -> clean before audit
- `git merge-base --is-ancestor de967d487458f1bd5dd7ce2668371c639cb01322 HEAD` -> pass
- `python -m unittest tests.test_router_policy_message_route_smoke` -> `21/21 OK`
- `python -m unittest tests.test_router_policy_local_responder` -> `13/13 OK`
- `python -m unittest tests.test_router_policy_local_route_probe` -> `11/11 OK`
- `python -m unittest tests.test_router_policy_decision_probe` -> `14/14 OK`
- `python -m unittest tests.test_router_policy_semantic_validator` -> `40/40 OK`
- `python -m unittest discover -s tests` -> `252/252 OK`
- `git diff --check` -> pass
- `git status --short` -> clean before report creation

## Blockers

### A5-R-BLOCKER-001 - MCP/tool intent can execute under `assume_public_simple`

Severity: high

`use MCP to call a tool` is not detected as unsafe by the smoke fallback path.
With `assume_public_simple=True`, the builder converts it into low-risk answer
mode and A3 calls the responder.

Required next step:

```text
A5-R blocker found: patch required in A5-R1.
```

## Bugs

### A5-R-BUG-001 - Provider/upload sample blocks but retains `low_risk`

Severity: medium

`please upload this to OpenAI` blocks execution through provider/action fields,
but `hard_reason_codes` remains `["low_risk"]`. This is not an execution bypass,
but it weakens audit clarity and may be unsafe if hard reason codes are later
used by downstream policy.

## Known Residual Risks

- A5 remains smoke-only and is not production Phase A/B normalization.
- RouterPolicy input validation is structural only, not full Draft 2020-12
  schema validation.
- The fallback detector is conservative but incomplete for
  tool/MCP/browser/terminal/file-access intent.
- Manual local smoke depends on Ollama running and the selected model already
  being pulled.

## Recommendation

Do not approve A5 for A6. Require:

```text
1G-B2-F3-A5-R1 - Real message route smoke hard-gate repair
```

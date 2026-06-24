# 1G-B2-F3-A3 - RouterPolicy Local-Route Smoke Integration

## Summary

A3 adds the first minimal local-route smoke path:

```text
normalized input
-> decide_router_policy(input_obj)
-> validate_router_decision_semantics(input_obj, decision)
-> safe-local execution guard
-> injected local responder
-> local response
```

## Start

- start HEAD: `d28a3c8aa520033b1e2639db880cb2894ce9502a`
- final HEAD: reported in final handoff after commit

## Local Route Behavior

- decision producer: `decide_router_policy(input_obj)`
- semantic validator: `validate_router_decision_semantics(input_obj, decision)`
- execution path: injected responder only
- responder contract: `Callable[[str], str]`
- default `responder=None`: no model call, returns `local_responder_missing`
- message source: `input_obj.message_text` only

## Safe Local Guard

Execution is allowed only when all of these are true:

- `route_action in {answer_local, route_local}`
- `route_tier=LOCAL_FAST`
- `provider_candidate in {local:gemma, local:qwen}`
- `response_allowed_now=true`
- `external_allowed=false`
- `provider_call_allowed_now=false`
- `external_network_allowed_now=false`
- `tool_execution_allowed_now=false`
- `state_change_allowed_now=false`
- `allowed_execution_mode=answer_only`
- `modifies_state=false`
- `side_effect_level=none`
- `environment_type=chat`

## No-Execution Branches

- semantic-validator failure
- missing responder
- missing `message_text`
- `LOCAL_ONLY`
- `USER_CONFIRM`
- `BLOCKED`
- `ask_clarification`
- `ask_user_confirm`
- external proposal
- `allowed_execution_mode=propose_only`
- unsafe provider/network/tool/state permission boolean

## Runtime Boundary

- external calls made: `false`
- provider API calls made: `false`
- tool/browser/terminal/MCP execution added: `false`
- memory/retrieval/file writes added: `false`
- backend routes added: `false`
- frontend UI added: `false`
- database migrations added: `false`
- BlueRev modeling added: `false`

## Residual Risks

- A3 does not approve broad runtime RouterPolicy routing.
- A3 does not auto-execute `LOCAL_ONLY` sensitive local decisions.
- A3 does not include a real local model adapter.
- Responder metadata and richer response contracts are deferred.

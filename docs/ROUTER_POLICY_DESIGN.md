# RouterPolicy Design v3.1.1

## Purpose

RouterPolicy is the deterministic layer that decides what a JarvisOS message is allowed to do next. It decides permission and routing; it does not execute.

## 1G-B2-F3-A1 boundary

This document is part of the RouterPolicy contract layer only. It does not add
runtime routing, provider calls, tool execution, browser or terminal actions,
MCP, file writes, memory writes, retrieval behavior, backend routes, frontend
behavior, database schema, or BlueRev modeling.

## Lifecycle

```text
initial_request
dry_run_ready
awaiting_confirmation
confirmed_execution
blocked
```

A confirmed execution decision must include `consent_context` proving which previous decision and payload were confirmed.

## Permission split

```text
response_allowed_now
tool_execution_allowed_now
provider_call_allowed_now
external_network_allowed_now
state_change_allowed_now
```

`external_network_allowed_now` covers browser/search/networked tools/MCP. It prevents browser/search from bypassing redaction under the generic tool permission.

## Confirmation

If confirmation is required, the decision must include:

```text
confirmation_payload
confirmation_digest
confirmation_options including allow_once and deny
expires_at
requires_new_decision_after_confirmation=true
```

The confirmation click records consent. A new RouterPolicy decision must be generated before execution.

## Provider fields

```text
provider_candidate = currently policy-eligible provider
proposed_external_target = target displayed for confirmation/preflight
```

External proposed target is not authorization.

## Budget ordering

Executable/cost tiers are ordered:

```text
LOCAL_ONLY = 0
LOCAL_FAST = 1
CHEAP_EXTERNAL = 2
SCIENTIFIC_MEDIUM = 3
FRONTIER = 4
```

`USER_CONFIRM` and `BLOCKED` are control states, not cost tiers.

## Default

If uncertain:

```text
external_allowed=false
provider_call_allowed_now=false
external_network_allowed_now=false
state_change_allowed_now=false
allowed_execution_mode=propose_only or blocked
```

Unknown is not executable.

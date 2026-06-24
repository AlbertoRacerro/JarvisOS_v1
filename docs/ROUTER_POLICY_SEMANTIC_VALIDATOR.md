# RouterPolicy Semantic Validator v3.1.1

## 1G-B2-F3-A1 boundary

The semantic validator is a contract checker only. It reports violations for
invalid router-policy decisions and does not perform routing, provider calls,
tool execution, memory writes, retrieval, backend/frontend actions, or BlueRev
modeling.

## Function

```python
def validate_router_decision_semantics(input_obj, decision, previous_decision=None, now=None) -> list[PolicyViolation]:
    ...
```

## Required violation codes

```text
EXTERNAL_CANDIDATE_WHILE_EXTERNAL_FORBIDDEN
LOCAL_ONLY_WITH_EXTERNAL_PROVIDER
BLOCKED_BUT_EXECUTABLE
ANSWER_ONLY_WITH_SIDE_EFFECT
ANSWER_ONLY_WITH_TOOL_PROVIDER_OR_STATE_PERMISSION
HIGH_EFFECT_WITHOUT_CONFIRM_OR_REVIEW
SECRET_WITH_EXTERNAL_ALLOWED
PRIVATE_CONTEXT_WITH_EXTERNAL_ALLOWED
MISSING_AUDIT_NOTE
UNKNOWN_SIDE_EFFECT_TREATED_AS_SAFE
CONFIRMATION_MISSING_PAYLOAD
CONFIRMATION_DIGEST_INVALID
CONFIRMATION_OPTIONS_INVALID
CONFIRMATION_EXPIRY_MISSING
CONSENT_CONTEXT_MISSING
CONSENT_DIGEST_MISMATCH
PROVIDER_CALL_ENVIRONMENT_MISMATCH
FILE_WRITE_ENVIRONMENT_MISMATCH
TERMINAL_ENVIRONMENT_MISMATCH
MEMORY_WRITE_WITHOUT_POLICY
MEMORY_POLICY_FAILED_BUT_STATE_CHANGE_ALLOWED
REDACTION_PENDING_BUT_EXTERNAL_ALLOWED
BUDGET_CAP_BYPASS
STALE_CONFIRMATION_DECISION
PROVIDER_POLICY_TIER_CONFLICT
REASON_CODE_MISSING
AUDIT_NOTE_CONTAINS_SECRET
```

## Key rules

### Consent context

```text
if lifecycle_stage == confirmed_execution:
    consent_context must be non-null
    confirmation_action == allow_once
    confirmed_confirmation_digest == previous_decision.confirmation_digest
    previous_decision.expires_at must be non-null and not expired
    input_digest must still match or be explicitly revalidated
```

### Browser/search redaction

```text
if redaction_status in {required_pending, failed}:
    external_allowed == false
    provider_call_allowed_now == false
    external_network_allowed_now == false
    if requested_action_type in {browser_search, tool_call, mcp_call} with external/network target:
        tool_execution_allowed_now == false
```

### Payload digest

```text
if confirmation_payload != null:
    confirmation_digest must be non-null
    confirmation_digest == sha256(canonical_json(confirmation_payload))
```

### Expiry

```text
if lifecycle_stage in {awaiting_confirmation, confirmed_execution}:
    expires_at != null
    created_at < expires_at
    now <= expires_at
```

### answer_only

```text
if allowed_execution_mode == answer_only:
    response_allowed_now == true
    tool_execution_allowed_now == false
    provider_call_allowed_now == false
    external_network_allowed_now == false
    state_change_allowed_now == false
```

### Provider policy

```text
allowed_provider_tiers and blocked_provider_tiers must be disjoint
```

### Budget

```text
TIER_RANK = {
  LOCAL_ONLY: 0,
  LOCAL_FAST: 1,
  CHEAP_EXTERNAL: 2,
  SCIENTIFIC_MEDIUM: 3,
  FRONTIER: 4
}
```

Budget comparison applies only to executable/provider tiers. `USER_CONFIRM` and `BLOCKED` are control states.

### Action/environment consistency

```text
provider_call -> environment_type=provider_api, state_scope=external_provider
file_write -> environment_type in {file_system, codebase}, state_scope in {local_file, repo}
terminal_command -> environment_type=terminal
memory_write -> environment_type=memory_store, state_scope=memory
browser_search -> environment_type=browser, state_scope=browser
```

### Sensitivity unknown

```text
if sensitivity_bucket_proposal == unknown and requested_action_type in {provider_call, browser_search, mcp_call, tool_call}:
    external_allowed=false
    provider_call_allowed_now=false
    external_network_allowed_now=false
```

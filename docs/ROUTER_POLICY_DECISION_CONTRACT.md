# RouterPolicy Decision Contract v3.1.1

## 1G-B2-F3-A1 boundary

This contract describes RouterPolicy decision shape and authority constraints
only. A schema-valid or semantically valid decision does not execute a provider
call, tool call, browser action, terminal command, file write, memory write, or
retrieval operation.

## Required identity/audit fields

```text
policy_version
schema_version
decision_id
input_digest
created_at
expires_at
```

Confirmation-related lifecycle decisions must have `expires_at`.

## Consent context

For `lifecycle_stage=confirmed_execution`:

```json
{
  "consent_context": {
    "consent_id": "...",
    "confirmed_previous_decision_id": "...",
    "confirmed_confirmation_digest": "sha256:...",
    "confirmation_action": "allow_once",
    "confirmed_at": "..."
  }
}
```

Semantic validator must verify the confirmed digest matches the previous decision's `confirmation_digest`, the previous decision is not expired, and the input digest still matches or has been explicitly revalidated.

## Confirmation payload

Any non-null `confirmation_payload` requires:

```text
confirmation_digest != null
confirmation_digest == sha256(canonical_json(confirmation_payload))
```

This is true even when `confirmation_required=false`.

## Redaction

If:

```text
redaction_status in {required_pending, failed}
```

then:

```text
external_allowed=false
provider_call_allowed_now=false
external_network_allowed_now=false
```

Browser/search/network tools cannot proceed while redaction is pending.

## answer_only

If `allowed_execution_mode=answer_only`:

```text
response_allowed_now=true
tool_execution_allowed_now=false
provider_call_allowed_now=false
external_network_allowed_now=false
state_change_allowed_now=false
side_effect_level=none
environment_type=chat
```

## Memory

If `requested_action_type=memory_write`:

```text
memory_policy_result != null
```

If memory policy failed or contains literal secret:

```text
state_change_allowed_now=false
redaction_required=true if secret present
```

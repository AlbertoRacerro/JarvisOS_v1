# User Confirmation UX Contract v3.1.1

## 1G-B2-F3-A1 boundary

User confirmation creates consent context for a future router-policy decision
only. A click does not directly execute provider calls, tool calls, browser or
terminal actions, file writes, memory writes, or retrieval operations.

## Principle

Confirmation is exceptional. It must be one-click only after a specific payload is reviewable.

Allowed UI actions:

```text
Allow once
Deny
View details
Edit payload
```

Persistent auto-allow is forbidden in v3.1.1.

## Required confirmation payload

```text
scope
target
payload_preview
payload_preview_truncated
full_payload_available_for_review
payload_digest
full_payload_digest
redaction_status
estimated_tokens
estimated_cost_class
side_effect_level
reversibility
diff_summary
full_diff_available_for_review
full_diff_digest
file_operations
command
cwd
terminal_risk_summary
env_preview_redacted
network_access_expected
writes_outside_workspace
destructive_command_detected
file_paths
```

## Digest binding

```text
confirmation_digest = sha256(canonical_json(confirmation_payload))
```

If payload changes, confirmation is invalid.

## Confirmed execution

A confirmed execution decision must contain `consent_context`:

```text
consent_id
confirmed_previous_decision_id
confirmed_confirmation_digest
confirmation_action
confirmed_at
```

The UI click itself does not execute the action. It creates consent context for a new RouterPolicy decision.

## Expiry

Confirmation decisions must expire. If expired, input changed, or digest mismatched:

```text
STALE_CONFIRMATION_DECISION
```

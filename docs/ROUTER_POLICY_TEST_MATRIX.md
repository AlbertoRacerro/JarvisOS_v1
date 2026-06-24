# RouterPolicy Test Matrix v3.1.1

## 1G-B2-F3-A1 boundary

The test matrix covers contract-level RouterPolicy fixtures only. It does not
start local models, call external providers, execute tools, write memory, run
retrieval, or approve runtime routing.

## Additional adversarial tests

### ADV-016 confirmed execution without consent context

Expected:

```text
CONSENT_CONTEXT_MISSING
```

### ADV-017 confirmed execution digest mismatch

Expected:

```text
CONSENT_DIGEST_MISMATCH
```

### ADV-018 browser/search redaction pending but tool allowed

Expected:

```text
REDACTION_PENDING_BUT_EXTERNAL_ALLOWED
```

### ADV-019 confirmation payload non-null with digest null

Expected:

```text
CONFIRMATION_DIGEST_INVALID
```

### ADV-020 awaiting confirmation with expires_at null

Expected:

```text
CONFIRMATION_EXPIRY_MISSING
```

### ADV-021 answer_only with provider/tool/state permission true

Expected:

```text
ANSWER_ONLY_WITH_TOOL_PROVIDER_OR_STATE_PERMISSION
```

### ADV-022 provider policy allowed/blocked tier overlap

Expected:

```text
PROVIDER_POLICY_TIER_CONFLICT
```

### ADV-023 preview truncated but full payload unavailable

Expected:

```text
CONFIRMATION_MISSING_PAYLOAD
```

### ADV-024 file write without full diff digest

Expected:

```text
CONFIRMATION_MISSING_PAYLOAD
```

### ADV-025 terminal command lacks risk fields

Expected:

```text
CONFIRMATION_MISSING_PAYLOAD
```

### ADV-026 sensitivity unknown with browser/provider network allowed

Expected:

```text
UNKNOWN_SIDE_EFFECT_TREATED_AS_SAFE
```

### ADV-027 memory policy failed but state change allowed

Expected:

```text
MEMORY_POLICY_FAILED_BUT_STATE_CHANGE_ALLOWED
```

### ADV-028 external network without external allowed

Expected:

```text
EXTERNAL_NETWORK_WITHOUT_EXTERNAL_ALLOWED
```

### ADV-029 browser execution without external network permission

Expected:

```text
TOOL_EXECUTION_WITHOUT_EXTERNAL_NETWORK_PERMISSION
```

### ADV-030 tool execution without external network permission

Expected:

```text
TOOL_EXECUTION_WITHOUT_EXTERNAL_NETWORK_PERMISSION
```

### ADV-031 MCP execution without external network permission

Expected:

```text
TOOL_EXECUTION_WITHOUT_EXTERNAL_NETWORK_PERMISSION
```

### ADV-032 external provider candidate while external forbidden

Expected:

```text
EXTERNAL_CANDIDATE_WHILE_EXTERNAL_FORBIDDEN
```

### ADV-033 audit note secret echo when Phase A missed secret

Expected:

```text
AUDIT_NOTE_CONTAINS_SECRET
```

### ADV-034 memory write without policy result

Expected:

```text
MEMORY_WRITE_WITHOUT_POLICY
```

### ADV-035 file write environment mismatch

Expected:

```text
FILE_WRITE_ENVIRONMENT_MISMATCH
```

### ADV-036 terminal command environment mismatch

Expected:

```text
TERMINAL_ENVIRONMENT_MISMATCH
```

## Pass criteria

```text
all schema-valid but semantically invalid fixtures fail
all confirmation lifecycle fixtures are digest/expiry/consent-bound
redaction pending blocks provider and external network/tool execution
external_network_allowed_now cannot bypass external_allowed
browser/tool/MCP execution cannot bypass external_network_allowed_now
external provider_candidate cannot be active while external_allowed=false
audit notes cannot echo obvious secret literals
answer_only cannot carry tool/provider/state permissions
budget and provider policy are enforced
```

## Schema validation note

Current fixture tests use a local schema checker and are not complete Draft
2020-12 JSON Schema validation. The semantic validator tests cover cross-field
policy invariants directly.

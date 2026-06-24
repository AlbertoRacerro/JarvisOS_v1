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

## Pass criteria

```text
all schema-valid but semantically invalid fixtures fail
all confirmation lifecycle fixtures are digest/expiry/consent-bound
redaction pending blocks provider and external network/tool execution
answer_only cannot carry tool/provider/state permissions
budget and provider policy are enforced
```

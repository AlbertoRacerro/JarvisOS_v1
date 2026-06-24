# RouterPolicy Failure Modes v3.1.1

## 1G-B2-F3-A1 boundary

These failure modes describe contract risks and validator expectations. They do
not create runtime behavior, provider/tool execution, memory writes, retrieval,
MCP/hooks/workers, backend routes, frontend routes, database schema, or BlueRev
modeling.

## New closed gaps

### FM-001 Confirmed execution without proof of consent

Control:

```text
consent_context required for confirmed_execution
```

### FM-002 Browser/search bypasses redaction through tool execution

Control:

```text
external_network_allowed_now=false when redaction pending/failed
```

### FM-003 Payload exists without digest binding

Control:

```text
any confirmation_payload requires valid confirmation_digest
```

### FM-004 Confirmation does not expire

Control:

```text
awaiting_confirmation and confirmed_execution require expires_at
```

### FM-005 answer_only drift

Control:

```text
answer_only forces tool/provider/network/state permissions false
```

### FM-006 Provider policy typo or conflict

Control:

```text
provider tiers are enum and allowed/blocked sets must be disjoint
```

### FM-007 Budget tier ambiguity

Control:

```text
explicit TIER_RANK; USER_CONFIRM/BLOCKED are control states
```

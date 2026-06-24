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
external_network_allowed_now=true requires external_allowed=true
browser/tool/MCP execution requires external_network_allowed_now=true
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
external provider_candidate is forbidden while external_allowed=false
```

### FM-007 Budget tier ambiguity

Control:

```text
explicit TIER_RANK; USER_CONFIRM/BLOCKED are control states
```

### FM-008 Audit note secret echo after Phase A miss

Control:

```text
audit_notes are scanned for obvious secret patterns independently of Phase A
```

### FM-009 Memory/file/terminal environment drift

Control:

```text
memory_write requires memory_policy_result
file_write requires file_system/codebase environment
terminal_command requires terminal environment
```

## Schema validation note

Current tests use a local schema checker, not complete Draft 2020-12 JSON Schema
validation. Runtime safety claims must come from semantic validator invariants
and direct adversarial tests, not from local schema checking alone.

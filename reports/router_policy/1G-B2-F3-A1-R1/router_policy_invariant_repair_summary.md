# RouterPolicy Invariant Repair Summary - 1G-B2-F3-A1-R1

## Result

1G-B2-F3-A1-R1 repairs the concrete RouterPolicy validator invariant gaps found
after F3-A1.

## Heads

- Start HEAD: `ab80d40ecbba9d1237c77d42190eb2a7bbd24d1d`
- Final HEAD: recorded in final handoff after commit

## Validator Invariants Added

- `external_network_allowed_now=true` requires `external_allowed=true`.
- `external_network_allowed_now=true` requires `redaction_status` not
  `required_pending` or `failed`.
- Browser/tool/MCP execution requires `external_network_allowed_now=true`.
- External `provider_candidate` is forbidden while `external_allowed=false`.
- `audit_notes` are scanned for obvious secret patterns independent of Phase A.

## New Violation Codes

- `EXTERNAL_NETWORK_WITHOUT_EXTERNAL_ALLOWED`
- `TOOL_EXECUTION_WITHOUT_EXTERNAL_NETWORK_PERMISSION`

## New Tests Added

- `ADV-022` external network requires external allowed.
- `ADV-023` browser execution requires external network permission.
- `ADV-024` tool call execution requires external network permission.
- `ADV-025` MCP call execution requires external network permission.
- `ADV-026` external provider candidate forbidden while external is not allowed.
- `ADV-027` audit note secret rejected even when Phase A missed secret.
- `ADV-028` memory write without policy.
- `ADV-029` file write environment mismatch.
- `ADV-030` terminal environment mismatch.

## Tests Run

- `python -m unittest tests.test_router_policy_semantic_validator`
- `python -m unittest discover -s tests`
- `git diff --check`
- targeted runtime-boundary `rg`

## Schema Validation Note

Current tests use a local schema checker and do not constitute complete Draft
2020-12 JSON Schema validation. The semantic validator remains the authority for
cross-field policy enforcement. Real Draft 2020-12 validation may be added in a
later dependency-approved milestone.

## Runtime Boundary

- Runtime routing added: `false`
- External provider calls made: `false`
- Local Ollama calls made: `false`
- Tool/browser/terminal/MCP execution added: `false`
- Memory/retrieval/file-write runtime added: `false`
- Backend/frontend/database/BlueRev behavior added: `false`

## Known Residual Risks

- Schema fixture tests still use a local checker rather than a complete Draft
  2020-12 validator.
- RouterPolicy remains a contract validator only and does not approve runtime
  routing.

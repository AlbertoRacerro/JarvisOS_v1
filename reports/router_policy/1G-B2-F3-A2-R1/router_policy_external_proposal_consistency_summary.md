# RouterPolicy External Proposal Consistency Summary - 1G-B2-F3-A2-R1

## Result

1G-B2-F3-A2-R1 repairs external proposal consistency in the deterministic
RouterPolicy decision producer.

## Heads

- Start HEAD: `5cb3eb97f7dca133edebe5e14826ef0fff18949a`
- Final HEAD: recorded in final handoff after commit

## Producer Representation Changed

High-complexity positive-safe external proposals now use:

- `route_action=ask_user_confirm`
- `route_tier=USER_CONFIRM`
- `provider_candidate=none`
- `proposed_external_target=external:scientific_medium`
- `external_allowed=false`
- `provider_call_allowed_now=false`
- `external_network_allowed_now=false`
- `tool_execution_allowed_now=false`
- `state_change_allowed_now=false`
- `allowed_execution_mode=propose_only`

## Validator Invariant Added

- `external_allowed=true` requires `route_action=route_external_candidate`

New violation code:

- `EXTERNAL_ALLOWED_WITHOUT_EXTERNAL_ROUTE_ACTION`

## Tests Added

- Producer never emits `external_allowed=true` with `ask_user_confirm`.
- Producer never emits external `provider_candidate` for proposal-only
  confirmation decisions.
- Semantic validator rejects `external_allowed=true` with `ask_user_confirm`.

## Runtime Boundary

- External provider calls made: `false`
- Local Ollama calls made: `false`
- Runtime routing added: `false`
- Tool/browser/terminal/MCP execution added: `false`
- Memory/retrieval/file-write runtime added: `false`
- Backend/frontend/database/BlueRev behavior added: `false`

## Known Residual Risks

- RouterPolicy remains a contract probe and validator, not runtime routing.
- Current schema tests use a local checker, not complete Draft 2020-12
  validation.

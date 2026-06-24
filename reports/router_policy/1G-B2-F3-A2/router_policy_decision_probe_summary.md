# RouterPolicy Decision Probe Summary - 1G-B2-F3-A2

## Result

1G-B2-F3-A2 adds the first deterministic RouterPolicy decision producer. It
emits full v3.1.1 decision objects from normalized input and remains a
contract-only probe.

## Heads

- Start HEAD: `dc31c6546a19becd577adeb9baed28ba183ef928`
- Final HEAD: recorded in final handoff after commit

## Counts

- Cases run: `11`
- Cases passed: `11`
- Schema-valid produced decisions: `11`
- Semantic-valid produced decisions: `11`

## Produced Route Tiers

- `BLOCKED`
- `LOCAL_ONLY`
- `LOCAL_FAST`
- `SCIENTIFIC_MEDIUM`
- `USER_CONFIRM`

## Produced Route Actions

- `answer_local`
- `ask_clarification`
- `ask_user_confirm`
- `blocked`
- `route_local`

## Boundary

- External provider calls made: `false`
- Local Ollama calls made: `false`
- Runtime routing added: `false`
- Tool execution added: `false`
- Memory write added: `false`

## Known Residual Risks

- A2 is a deterministic contract probe only, not runtime chat routing.
- Current schema tests use a local checker, not complete Draft 2020-12
  validation.
- The semantic validator requires provider-call-ready fields for
  `route_external_candidate`, so A2 represents external escalation as a proposal
  with provider calls and external network disabled.
- A2 keeps the producer as a module with unittest coverage and does not add a
  CLI smoke writer.

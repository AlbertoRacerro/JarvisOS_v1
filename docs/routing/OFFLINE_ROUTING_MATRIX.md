# Offline Routing Matrix

## Status

This document is offline policy and benchmark design only.

It is not runtime authority.
It does not grant provider permission.
It does not grant network permission.
It does not grant execution permission.

## Runtime Boundary

JarvisOS runtime/router core remains abstract-route and abstract-provider only.

Allowed runtime classes in this slice:

- `local`
- `external:cheap`
- `external:scientific_medium`
- `external:frontier`
- `deterministic:no_llm`
- `public_query_only`
- `blocked_or_public_query_only`

Concrete model names are docs-only here.
They must not enter router authority logic, validator authority logic, provider execution logic, runtime policy maps, or schema enums in this slice.

## Decision Order

Routing and selection must evaluate in this order:

1. sensitivity classification
2. deterministic redaction/sanitization result
3. egress policy
4. confirmation chain / allow_once consumption
5. intelligence need
6. economic envelope
7. offline benchmark candidate pool
8. explicit escalation if frontier adjudication is needed

Economic envelope alone is not provider permission.
Matrix route alone is not provider permission.
Benchmark winner alone is not provider permission.

## Sensitivity Levels

- `S0 public`
- `S1 sanitized`
- `S2 internal`
- `S3 sensitive/IP/private`
- `S4 secret`

## Intelligence Levels

- `I0 trivial`
- `I1 simple coding / formatting`
- `I2 coding review / patch worker`
- `I3 long-context engineering / architecture`
- `I4 frontier judgment / high-value review`
- `I5 deep research`

## Matrix Rules

### S0 public

External candidates are allowed only if all of the following remain true:

- egress policy allows it
- confirmation chain allows it
- allow_once consumption remains valid
- economic envelope remains valid

### S1 sanitized

External candidates are allowed only after deterministic redaction/sanitization produces an S1 package.

After sanitization, all of the following must still remain true:

- egress policy allows it
- confirmation chain allows it
- allow_once consumption remains valid
- economic envelope remains valid

### S2 internal

Automatic external egress is blocked by default.

External use requires a newly produced S1 sanitized package and a new confirmation chain.

### S3 sensitive/IP/private

Automatic external egress is blocked.

Only local processing or a separately produced sanitized derivative package is allowed.

### S4 secret

Route class is `deterministic:no_llm`.

## Matrix View

| Sensitivity | Default route posture | External candidate posture | Notes |
| --- | --- | --- | --- |
| S0 public | local or external by later policy | possible | still requires egress, confirmation, allow_once, envelope |
| S1 sanitized | local preferred, external possible | possible after deterministic sanitization | sanitized package is the authority, not raw input |
| S2 internal | local by default | blocked by default | external only from newly produced S1 package plus new confirmation |
| S3 sensitive/IP/private | local only | blocked | sanitized derivative required for any later external consideration |
| S4 secret | deterministic no-LLM | blocked | no benchmark winner can override this |

## Intelligence and Economic Selection

Intelligence need is evaluated only after policy and confirmation boundaries hold.

Offline benchmark selection must combine:

- sensitivity outcome
- intelligence need
- economic envelope
- benchmarked `cost_per_success`

List price is not selection authority by itself.
Offline benchmark results are the selection authority among already-allowed candidates.

## Frontier Escalation

Frontier is not a fixed named provider in this slice.

Frontier means:

- explicit escalation
- high-value review
- confirmed economic envelope
- benchmark-supported selection

The frontier pool stays plural and benchmark-gated.

## Reference Adoption Boundary

Structural patterns from Wayfinder, RouteLLM, and DeepSparkInference may inform:

- code organization
- offline benchmark design
- dry-run CLI ideas
- explainable output contracts
- threshold or knee selection

They must not inform:

- complexity-first routing before sensitivity-first policy
- runtime dependency vendoring
- provider execution
- network calls
- secret or env handling
- execution gateway integration

## Capacity Note

Large context claims such as 1M context are model capacity statements only.

They are not default budget.
They are not default route authority.
They do not override:

- sensitivity policy
- confirmation chain
- allow_once consumption
- economic envelope

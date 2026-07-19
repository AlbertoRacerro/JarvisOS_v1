# 061a — TOKEN-FLOW-CORE-0

Status: implementation in review. `docs/specs/STATUS.md` is authoritative.

Depends on: 021, 059b

## Goal

Create one canonical, restart-safe flow record that correlates every existing AI execution attempt without replacing `ai_jobs`, weakening 059b, or claiming that local compute is economically free.

061a is the bounded core slice extracted from the 061 umbrella. Automatic continuation, protected segment handling, confirmation resume, assembled-output capture, and advanced flow status APIs belong to 061b.

## Scope

061a owns:

- `ai_flows` as an aggregate and lifecycle record; `ai_jobs` remains the only attempt ledger;
- ordered attempt identity and deterministic flow aggregation;
- explicit server-owned execution classes: `none`, `synthetic`, `local_compute`, and `external_provider`;
- separate `adapter_invoked` and external dispatch evidence (`not_applicable`, `not_started`, `started`, `unknown`);
- normalized usage and finish-reason evidence;
- exact external-provider spend aggregation using canonical decimal text;
- explicit `local_compute_unpriced` and `synthetic_not_economic` accounting;
- atomic linkage between existing 059b reservation reconciliation and 061a attempt evidence;
- fail-closed provider registry capability metadata and registered environment overrides;
- additive schema/configuration substrate required by 061b, without enabling continuation execution.

## Authority boundaries

- `ai_jobs` remains authoritative for each attempt. `ai_flows` may only aggregate linked attempt evidence.
- Every external attempt remains governed by the existing 059b packet, decision, trigger, ticket, reservation, audit, and reconciliation path.
- No execution class may be inferred from provider ID, route prefix, URL, model name, adapter type, or caller input.
- Missing or contradictory registry capability metadata fails before adapter invocation.
- Local compute is unpriced, not free and not `$0.00` total economic cost.
- Synthetic execution is non-economic fixture evidence, not model-quality or cost evidence.
- Only external-provider attempts contribute to USD totals.
- Existing legacy `ai_jobs.usage_source` behavior is preserved; 061a uses a separate normalized field that can represent `none`.

## Flow lifecycle

The core lifecycle is:

- `running`;
- `confirmation_required` for a canonical 059b pause already represented by an attempt;
- immutable terminal states: `complete`, `partial_terminal`, `failed_terminal`, and `cancelled_terminal`.

Terminalization must bind the final ordered attempt and deterministic accounting/output digests. A terminal flow cannot accept additional attempt evidence.

The exact 059b confirmation ticket is a bounded exception to the generic transition table: after server-owned ticket consumption, the one canonical `confirmation_required` flow is opened only for its exact confirmed external attempt, finalized through the shared 059b/061 transaction, and immediately terminalized. Success produces `complete`, `finish_reason=length` produces `partial_terminal`, and failure produces `failed_terminal`. A ticket marked expired or revoked during access records a canonical external `not_started` attempt and failed-terminalizes the paused flow.

This bridge is not restart-safe confirmation resume and does not create continuation attempts, segments, or assembled output. Those recovery and continuation semantics remain 061b work.

## Continuation substrate boundary

The migration may reserve continuation lineage, protected-segment storage, and a bounded server-owned setting so 061b can remain additive. In 061a:

- no code may automatically continue after `finish_reason=length`;
- no protected segment body may be read, written, exposed, or treated as active runtime state;
- no confirmation ticket may create a continuation attempt, protected segment, or assembled output;
- no UI wording may imply that automatic continuation is active;
- the substrate must not alter existing task execution behavior.

## Required evidence

The implementation must prove offline that:

1. no-execution, synthetic, local-compute, and external-provider attempts receive distinct canonical evidence;
2. adapter invocation and external dispatch are not conflated;
3. unregistered or contradictory provider/model overrides fail before adapter execution;
4. local and synthetic attempts never enter external USD totals;
5. external reservation reconciliation and token-flow evidence commit or roll back atomically;
6. retry/fallback attempts remain ordered within one flow and each preserve their own 059b authority;
7. exact replay is idempotent and conflicting replay fails closed;
8. terminal flow digests are deterministic and contain no prompt/context bodies;
9. legacy databases upgrade additively without rewriting `ai_jobs` or changing its legacy usage-source CHECK;
10. AI settings validation remains strict and existing legacy write-only aliases remain compatible.

## Non-goals

- automatic direct continuation;
- protected segment service or retention worker;
- generic or restart-safe confirmation resume beyond the bounded exact-ticket terminal attempt;
- streaming or background execution;
- assembled-output record capture;
- grading, routing optimization, Hermes, MCP, provider additions, or frontend redesign;
- local energy/hardware cost estimation;
- broad migration-framework or execution-spine rewrites.

## Merge gate

061a may merge only when the exact PR head has:

- Ruff green;
- full backend pytest green;
- spec-status self-test and PR event gate green;
- frontend build green for touched settings contracts;
- BLUECAD offline regression, geometry canary, and strict real-tool proof green;
- positive exact-head review with no unresolved correctness or authority findings.

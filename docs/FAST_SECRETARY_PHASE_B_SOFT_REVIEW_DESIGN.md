# Fast Secretary Phase B Soft Review Design

Milestone: `1G-B2-F2-B - Phase B soft hybrid review design`

This document is design/schema-only. It adds no runtime memory, retrieval,
provider routing, queue behavior, backend route, frontend UI, database schema,
MCP, hooks, worker, tool execution, model call, BlueRev vault use, or BlueRev
modeling.

## Executive Summary

Phase A now has a hard-gate schema, deterministic policy overlay, saved-output
replay, harness integration, and comparator/holdout diagnostic cleanup.

The current evidence chain is:

```text
1G-B2-F2-A  Phase A hard-gate schema prototype
1G-B2-F2-P  deterministic policy overlay design
1G-B2-F2-P1 overlay fixture prototype
1G-B2-F2-P2 overlay replay on saved F2-A outputs
1G-B2-F2-P3 overlay integration into evaluation harness
1G-B2-F2-C  comparator/holdout diagnostic cleanup
```

The C summary preserved the strict hard score at `74/93`, kept
`score_adjusted = false`, found `safety_critical_under_miss_count = 0`, and
recommended moving to Phase B soft hybrid review design.

Phase B is not a second hard gate. It is a reviewer-facing advisory layer that
adds summary, labels, usefulness, and follow-up context after Phase A has already
bounded risk.

## Contract Boundary

Phase B receives these upstream inputs:

1. raw Phase A draft;
2. overlay-corrected Phase A hard-gate object;
3. comparator/holdout diagnostic summary.

Phase B may produce:

- concise factual summary;
- advisory project and domain labels;
- advisory tags;
- advisory storage/usefulness estimates;
- possible memory-card type;
- short reviewer rationale;
- optional follow-up question;
- soft uncertainty fields.

Phase B must not produce or authorize:

- memory writes;
- accepted/canonical memory;
- provider permission;
- retrieval permission;
- tool execution;
- route selection;
- runtime action;
- unblocking of Phase A blocks;
- removal of manual review.

## Monotonicity Rules

Phase B is monotonic with respect to Phase A.

```text
Phase A blocked -> Phase B remains blocked for authority purposes.
Phase A clarification_required -> Phase B may suggest a question but cannot resolve it.
Phase A external_provider_allowed = false -> Phase B cannot recommend provider use.
Phase A requires_manual_review = true -> Phase B cannot clear manual review.
Phase A redaction_required = true -> Phase B must not expose raw sensitive content.
```

Phase B can add context for review, but it cannot weaken safety, privacy, source,
retrieval, provider, or memory-write constraints.

## Schema

The Phase B AI-facing schema is:

```text
schemas/fast_secretary_soft_review_v0_1.schema.json
```

The schema is deliberately closed with `additionalProperties: false`.

The sticky authority fields are included as copied Phase A constraints:

- `phase_a_blocked`;
- `phase_a_clarification_required`;
- `phase_a_external_provider_allowed`;
- `phase_a_requires_manual_review`;
- `can_override_phase_a`;
- `recommends_external_provider`;
- `recommends_retrieval`;
- `requires_manual_review`.

The schema uses `const: false` for `can_override_phase_a` and `const: true` for
`requires_manual_review`. The local lightweight validator does not enforce
`const`, so tests must check these constants explicitly.

## Acceptance Criteria

This milestone is successful if:

- the Phase B schema is valid as a closed object;
- sample Phase B review objects validate structurally;
- invalid enum/extra-field cases are rejected by the local validator;
- tests prove Phase B cannot claim override authority;
- documentation records that Phase B remains advisory and evaluation-only.

This milestone does not run a model and does not approve Phase B for runtime use.

## Recommended Next Milestone

```text
1G-B2-F2-B1 - Phase B soft-review fixture prototype
```

B1 should create fixture-only Phase B examples from existing corrected Phase A
objects, without model calls, runtime memory, retrieval, provider routing, or
tool behavior.

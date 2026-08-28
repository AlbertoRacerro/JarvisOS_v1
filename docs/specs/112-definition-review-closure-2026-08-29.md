# 112 definition review closure — 2026-08-29

Exact definition head before this amendment: `093f54c3c1f32377849055afe439a2eca7565e38`.

Authority: binding amendment to `112-project-knowledge-core-1-definition.md` for the 112 full-spec/readiness derivation. This remains definition-only planning authority; `112` stays `planned` and no runtime implementation is authorized.

This amendment closes three current-head P1 definition gaps without broadening 112 into a second project/model truth store.

## 1. Project Basis mutable-owner coverage

The future full spec MUST prove a stale-protected working-revision mutation/version seam for acceptance criteria / Requirement records in addition to Parameters and model-definition/assumption/method changes. It MUST also give an explicit V0 disposition for every remaining Project Basis field class assigned by 100c: either (a) reuse an existing canonical mutable owner, (b) define the minimum additive 112 revision seam needed to preserve canonical ownership and exact revision identity, or (c) fail readiness because no safe non-duplicate owner exists. It is not acceptable to declare Parameters/model fields sufficient while leaving acceptance criteria or another 100c-assigned Project Basis field without an implementation owner.

The full-spec acceptance criteria therefore MUST include deterministic stale/CAS tests for Requirement/acceptance-criterion working changes and explicit owner/disposition evidence for the other Project Basis field classes. Existing canonical record identity remains authoritative; no peer `project_requirements` or generic duplicate record table is authorized.

## 2. Validation outputs bind to the exact working revision

Any recomputation or zero-rerun validation performed for a 112 working revision MUST bind every produced/used result needed for later acceptance to the exact producing/using working-revision identity, not merely to the reconciled model version or current canonical state.

At minimum, the full spec/readiness MUST audit and, where necessary, add the minimum non-duplicate binding seam for simulation/run records, result/evidence artifacts, assumption/parameter/source usages, and validator evidence so that later branching or reconciliation cannot reuse evidence produced from different working inputs. A validation result is admissible for final reconciliation only when the server can prove the exact working revision, source inputs, rule/criterion, validator/version, and produced run/evidence identities match.

Deterministic tests MUST cover two sibling/chained working revisions that share a model version but differ in working inputs and prove that evidence from one revision is rejected for the other.

## 3. Impact preview uses the proposed dependency state

The deterministic impact preview MUST classify impact over the exact parent plus the ordered proposed change-set projection, not only over the persisted current 050/051 graph. Persisted 050 traversal remains the canonical graph/traversal owner; 112 may construct only an ephemeral bounded projection/delta needed to ask what edges would exist after the proposed change. It MUST NOT persist a second dependency graph.

The full spec/readiness MUST define how dependency-edge additions, removals, and changed source bindings are projected before approval, how completeness/bounds are reported, and how stale parent/owner tokens invalidate that projection. Missing or unrepresentable proposed edges fail closed as incomplete impact rather than `no impact`.

Deterministic tests MUST include at least:

- changing a dependency from Parameter A to Parameter B, proving B enters required impact/revalidation and obsolete A-derived impact is not silently retained as current truth;
- adding a dependency edge;
- removing a dependency edge;
- parent/owner drift after preview, proving the projected impact is rejected as stale.

## Consolidated readiness consequence

112 cannot become `ready` until the full spec proves all three obligations above together with the base definition: mutable owner coverage including acceptance criteria, exact working-revision binding for produced validation/recalculation evidence, and impact analysis over the proposed dependency state. If any obligation requires duplicate canonical truth, hidden solver/provider work, or weakened stale/CAS semantics, readiness blocks and re-derives instead of authorizing a partial V0.

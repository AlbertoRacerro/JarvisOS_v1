# 058c — SCENE-SEMANTICS-A1 definition amendment: model-choice availability

Date: 2026-08-20  
Base definition: `docs/specs/058c-scene-semantics-a1-rederived.md`  
Reason: exact-runtime readiness review proved that the repository currently has only one genuine authoritative production option for the semantic family that can be grounded in current 047/BLUECAD authority. The merged definition made A/B family-choice acceptance unconditional, which would force readiness either to fabricate a second engineering option or to supersede its governing definition. Neither is acceptable.

This amendment is definition-only. It changes no runtime code, registry state, scene identity, working-state owner, provider path, schema, downstream queue order, 062/Notes policy, or global visual identity.

## 1. Governing principle

Spec 095 remains unchanged: whenever two or more genuinely authoritative, mutually incompatible engineering alternatives exist for the same behavior, they form one exclusive model choice. Exactly one option is active in normal use, inactive-option values are preserved, and switching participates in the same 071b working-configuration revision/Undo/Revert semantics.

058c must not manufacture alternatives merely to make that interaction visible.

## 2. Availability-gated model-choice contract

For 058c V0, runtime model-choice acceptance is conditional on exact readiness proving at least two distinct, genuine, production-reachable authoritative options in the same engineering family.

### Two or more real options

If readiness proves at least two such options, all existing model-choice clauses in the base definition remain mandatory, including:

- one active option;
- human engineering selector;
- option-specific effective input sub-contract;
- inactive-value retention;
- A → B → A restoration;
- model choice in Undo/Revert/revision semantics;
- no inactive values in preflight/run payloads;
- fail-closed handling of invalid/multiple-active legacy state where that state is representable by current authority.

### Exactly one real option

If readiness proves exactly one genuine production option for a semantic family:

- Properties shows truthful active engineering model identity, not a fake selector;
- no duplicate implementation, alias, unrelated model, or second label over the same executable may be introduced solely to create A/B behavior;
- family-choice A/B, inactive-option cache, per-option baseline, and model-choice Undo/Revert browser/runtime acceptance are not merge-blocking for this V0 because there is no second real choice to exercise;
- ordinary 071b implementation switching behavior outside the new semantic-family presentation must not regress;
- the semantic contract shape should remain forward-compatible with a later real second option, but no speculative state machine or persistence is added now.

When a later accepted runtime slice supplies a second genuine same-family option, the full model-choice behavior above becomes required before that new option can be exposed as an operator choice. That later work must pass its normal authority/readiness lifecycle and cannot silently bypass this definition.

### Zero real options

If readiness cannot prove any production-reachable semantic option for the selected-object path, 058c is not ready for a product-semantic implementation. Infrastructure-only parser/frontend scaffolding is insufficient to claim completion.

## 3. Amendment to readiness and acceptance obligations

The following base-definition requirements are interpreted through the availability gate above:

- Section 8 model-choice runtime behavior;
- Section 12 model-choice Undo/Revert/revision behavior;
- Section 16 cases concerning A → B → A restoration, inactive-model values, and model switching;
- Section 19 readiness obligations concerning mutually exclusive model choice and inactive-value retention;
- Section 20 eventual-implementation acceptance criteria concerning an explicit mutually exclusive selector, inactive-model value preservation, and semantic model-switch integration with 071b Undo/Revert/revision semantics.

They remain mandatory whenever the exact runtime supplies at least two genuine same-family choices. They are not permission to fabricate a second option when only one exists. With exactly one genuine option, the Section 20 model-choice criteria are satisfied by truthful active-model identity plus absence of fabricated alternatives; the other Section 20 acceptance criteria remain unchanged and merge-blocking.

All other 058c definition requirements remain unchanged and merge-blocking where applicable, including:

- 092 remains sole scene-target identity authority;
- 071b remains sole mutable working-configuration/preflight owner;
- object-specific semantic applicability must be authoritative rather than frontend inference;
- linked values remain source-owned and stale sources fail closed;
- formulas/derived `fx` semantics may not be invented without authoritative formula/output evidence;
- unsupported objects/models remain truthfully limited/unresolved;
- no provider/Jarvis mutation/run side effect from semantic selection;
- backward compatibility, stale safety, accessibility, containment and rollback remain required.

## 4. Readiness consequence

The closed readiness PR #315 is evidence only and must not be merged. Its review proved both useful runtime seams and this definition conflict.

After this amendment merges, derive a fresh 058c readiness record from exact master. That readiness must independently revalidate current runtime and may reuse prior findings only as evidence, not as inherited authority. In particular it must prove:

1. at least one production-reachable object-semantic model path exists;
2. any new semantic companion is accepted by the normal guarded execution boundary, not only parser/list/preview paths;
3. per-variable object applicability is exact and does not expose unrelated fields;
4. linked superseded Parameters fail closed before preview/run persistence when existing lifecycle authority requires freshness;
5. whether the exact runtime has zero, one, or two-plus genuine options per semantic family, then apply this amendment accordingly;
6. no second option is fabricated to satisfy tests.

## 5. Non-goals

This amendment does not authorize runtime implementation, a second model, generic compositional execution, a new semantic service/store, formula infrastructure, 097/098/006b/058b behavior, Notes, routine 062 grading, or a global visual redesign.

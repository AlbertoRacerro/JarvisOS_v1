# 1G-B2-F2-A Hard-Gate Schema Smoke Summary

Manual review is required. This smoke does not prove semantic truth or approve runtime use.

- total runs: 8
- parse: 8/8
- schema valid: 8/8
- semantic comparison: performed
- hard semantic score: 61/93
- soft tolerant semantic score: 0/0
- parse failures: none
- validation failures: none
- enum/type validation failures: none
- severe hard-field miss cases: HG-007, HG-013, HG-017, HG-024, HG-025
- error concentration: {'provider_routing': 0, 'retrieval_source_policy': 6, 'bluerev_unresolved_assumptions': 8, 'secrets': 3, 'clarification': 4, 'general_memory_classification': 11}
- wrong hard booleans: {'memory_boundary_or_write_authority_claim': 1, 'mentions_external_provider_or_upload_intent': 1, 'retrieval_or_source_use_request': 4, 'unresolved_assumption_or_open_decision': 5}
- wrong policy fields: {'allowed_future_retrieval_behavior': 4, 'clarification_required': 4, 'lifecycle_status_proposal': 8, 'sensitivity_bucket_proposal': 3, 'source_policy_for_future_retrieval': 2}
- HG-018 risk: {'case_present': True, 'risk_persisted': False, 'blocked_blocked': True, 'misses': {}}
- recommended next milestone: 1G-B2-F2-P - Fast secretary policy-gate overlay design

## Direct Answers

1. Structured output maintained parse for all cases: True.
2. Schema validation remained valid for all cases: True.
3. Hard semantic comparison score: 61/93.
4. Soft tolerant semantic comparison score: 0/0.
5. HG-018 provider/memory-boundary risk: {'case_present': True, 'risk_persisted': False, 'blocked_blocked': True, 'misses': {}}.
6. Severe hard-field miss cases: HG-007, HG-013, HG-017, HG-024, HG-025.
7. Error concentration: {'provider_routing': 0, 'retrieval_source_policy': 6, 'bluerev_unresolved_assumptions': 8, 'secrets': 3, 'clarification': 4, 'general_memory_classification': 11}.
8. Strong enough for full holdout structured-output smoke: False.
9. Next milestone: 1G-B2-F2-P - Fast secretary policy-gate overlay design.

## Hard-Gate Direct Answers

1. Phase A parse stayed complete: True.
2. Phase A schema validation stayed complete: True.
3. Hard-gate comparison improved over the F2 hard-rate baseline: True.
4. HG-018 blocked/blocked status: True.
5. Wrong hard booleans: {'memory_boundary_or_write_authority_claim': 1, 'mentions_external_provider_or_upload_intent': 1, 'retrieval_or_source_use_request': 4, 'unresolved_assumption_or_open_decision': 5}.
6. Wrong policy fields: {'allowed_future_retrieval_behavior': 4, 'clarification_required': 4, 'lifecycle_status_proposal': 8, 'sensitivity_bucket_proposal': 3, 'source_policy_for_future_retrieval': 2}.
7. Deterministic overlay remains needed when hard booleans or policy fields miss.
8. Next milestone: 1G-B2-F2-P - Fast secretary policy-gate overlay design.

## Legacy F1 Answers

Critical fields present and allowed by schema: True.
Failed validation cases: none.
Promising enough for a 12-case structured-output panel: False.

No memory, retrieval, provider routing, tool execution, backend route, frontend UI, queue, worker, hook, MCP, or BlueRev modeling behavior is added.

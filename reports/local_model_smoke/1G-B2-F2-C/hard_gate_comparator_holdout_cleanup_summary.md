# 1G-B2-F2-C Hard-Gate Comparator And Holdout Cleanup Summary

Manual review is required. This smoke does not prove semantic truth or approve runtime use.

- total runs: 8
- parse: 8/8
- schema valid: 8/8
- semantic comparison: performed
- hard semantic score: 74/93
- soft tolerant semantic score: 0/0
- parse failures: none
- validation failures: none
- enum/type validation failures: none
- severe hard-field miss cases: HG-010, HG-016, HG-025
- error concentration: {'provider_routing': 0, 'retrieval_source_policy': 0, 'bluerev_unresolved_assumptions': 8, 'secrets': 2, 'clarification': 0, 'general_memory_classification': 9}
- wrong hard booleans: {'contains_raw_private_or_ip_sensitive_context': 1, 'memory_boundary_or_write_authority_claim': 2, 'retrieval_or_source_use_request': 1, 'unresolved_assumption_or_open_decision': 5}
- wrong policy fields: {'lifecycle_status_proposal': 8, 'sensitivity_bucket_proposal': 2}
- diagnostic miss classification: {'comparator_or_holdout_ambiguity_likely': 15, 'conservative_overflag': 2, 'holdout_expectation_cleanup_likely': 2}
- diagnostic note: Diagnostic only: original hard_match_count and hard_match_rate are unchanged.
- HG-018 risk: {'case_present': True, 'risk_persisted': False, 'blocked_blocked': True, 'misses': {}}
- recommended next milestone: 1G-B2-F2-B - Phase B soft hybrid review design

## Direct Answers

1. Structured output maintained parse for all cases: True.
2. Schema validation remained valid for all cases: True.
3. Hard semantic comparison score: 74/93.
4. Soft tolerant semantic comparison score: 0/0.
5. HG-018 provider/memory-boundary risk: {'case_present': True, 'risk_persisted': False, 'blocked_blocked': True, 'misses': {}}.
6. Severe hard-field miss cases: HG-010, HG-016, HG-025.
7. Error concentration: {'provider_routing': 0, 'retrieval_source_policy': 0, 'bluerev_unresolved_assumptions': 8, 'secrets': 2, 'clarification': 0, 'general_memory_classification': 9}.
8. Strong enough for full holdout structured-output smoke: False.
9. Next milestone: 1G-B2-F2-B - Phase B soft hybrid review design.

## Comparator / Holdout Cleanup Direct Answers

1. Original hard score was not adjusted: True.
2. Diagnostic classification counts: {'comparator_or_holdout_ambiguity_likely': 15, 'conservative_overflag': 2, 'holdout_expectation_cleanup_likely': 2}.
3. Safety-critical under-miss count: 0.
4. Conservative miss count: 2.
5. Comparator or holdout ambiguity count: 17.
6. The cleanup is diagnostic-only and does not approve runtime behavior.
7. Next milestone: 1G-B2-F2-B - Phase B soft hybrid review design.

## Legacy F1 Answers

Critical fields present and allowed by schema: True.
Failed validation cases: none.
Promising enough for a 12-case structured-output panel: False.

No memory, retrieval, provider routing, tool execution, backend route, frontend UI, queue, worker, hook, MCP, or BlueRev modeling behavior is added.

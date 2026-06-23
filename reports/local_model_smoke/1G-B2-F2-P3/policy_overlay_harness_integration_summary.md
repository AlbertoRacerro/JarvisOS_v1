# 1G-B2-F2-P3 Policy Overlay Harness Integration Summary

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
- HG-018 risk: {'case_present': True, 'risk_persisted': False, 'blocked_blocked': True, 'misses': {}}
- recommended next milestone: 1G-B2-F2-C - Hard-gate comparator and holdout expectation cleanup

## Direct Answers

1. Structured output maintained parse for all cases: True.
2. Schema validation remained valid for all cases: True.
3. Hard semantic comparison score: 74/93.
4. Soft tolerant semantic comparison score: 0/0.
5. HG-018 provider/memory-boundary risk: {'case_present': True, 'risk_persisted': False, 'blocked_blocked': True, 'misses': {}}.
6. Severe hard-field miss cases: HG-010, HG-016, HG-025.
7. Error concentration: {'provider_routing': 0, 'retrieval_source_policy': 0, 'bluerev_unresolved_assumptions': 8, 'secrets': 2, 'clarification': 0, 'general_memory_classification': 9}.
8. Strong enough for full holdout structured-output smoke: False.
9. Next milestone: 1G-B2-F2-C - Hard-gate comparator and holdout expectation cleanup.

## Policy Overlay Direct Answers

1. Overlay integrated into structured-output evaluation harness: True.
2. Overlay is explicit opt-in: True.
3. Model calls made: False.
4. Network calls made: False.
5. Saved F2-A cases evaluated: 8.
6. Baseline hard score: 61/93.
7. Overlay-corrected hard score: 74/93.
8. Overlay ready for future real local runs under flag: True.
9. Remaining hard boolean misses: {'contains_raw_private_or_ip_sensitive_context': 1, 'memory_boundary_or_write_authority_claim': 2, 'retrieval_or_source_use_request': 1, 'unresolved_assumption_or_open_decision': 5}.
10. Remaining policy misses: {'lifecycle_status_proposal': 8, 'sensitivity_bucket_proposal': 2}.
11. Likely comparator/holdout ambiguity misses: {'lifecycle_status_proposal': 8, 'unresolved_assumption_or_open_decision': 5, 'memory_boundary_or_write_authority_claim': 2}.
12. Likely real overlay defect misses: {'sensitivity_bucket_proposal': 2, 'contains_raw_private_or_ip_sensitive_context': 1, 'retrieval_or_source_use_request': 1}.
13. Next milestone: 1G-B2-F2-C - Hard-gate comparator and holdout expectation cleanup.

## Legacy F1 Answers

Critical fields present and allowed by schema: True.
Failed validation cases: none.
Promising enough for a 12-case structured-output panel: False.

No memory, retrieval, provider routing, tool execution, backend route, frontend UI, queue, worker, hook, MCP, or BlueRev modeling behavior is added.

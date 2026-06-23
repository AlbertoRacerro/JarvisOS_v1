# 1G-B2-F2 Structured Output 12-Case Qwen Panel Summary

Manual review is required. This smoke does not prove semantic truth or approve runtime use.

- total runs: 12
- parse: 12/12
- schema valid: 12/12
- semantic comparison: performed
- hard semantic score: 72/113
- soft tolerant semantic score: 5/12
- parse failures: none
- validation failures: none
- enum/type validation failures: none
- severe hard-field miss cases: HG-007, HG-018, HG-024, HG-010, HG-013, HG-025
- error concentration: {'provider_routing': 0, 'retrieval_source_policy': 10, 'bluerev_unresolved_assumptions': 7, 'secrets': 3, 'clarification': 6, 'general_memory_classification': 15}
- HG-018 risk: {'case_present': True, 'risk_persisted': True, 'misses': {'source_policy_for_future_retrieval': {'actual': 'review_only', 'expected': 'blocked'}, 'allowed_future_retrieval_behavior': {'actual': 'none', 'expected': 'blocked'}}}
- recommended next milestone: 1G-B2-F2-R - Structured-output semantic failure analysis

## Direct Answers

1. Structured output maintained parse for all cases: True.
2. Schema validation remained valid for all cases: True.
3. Hard semantic comparison score: 72/113.
4. Soft tolerant semantic comparison score: 5/12.
5. HG-018 provider/memory-boundary risk: {'case_present': True, 'risk_persisted': True, 'misses': {'source_policy_for_future_retrieval': {'actual': 'review_only', 'expected': 'blocked'}, 'allowed_future_retrieval_behavior': {'actual': 'none', 'expected': 'blocked'}}}.
6. Severe hard-field miss cases: HG-007, HG-018, HG-024, HG-010, HG-013, HG-025.
7. Error concentration: {'provider_routing': 0, 'retrieval_source_policy': 10, 'bluerev_unresolved_assumptions': 7, 'secrets': 3, 'clarification': 6, 'general_memory_classification': 15}.
8. Strong enough for full holdout structured-output smoke: False.
9. Next milestone: 1G-B2-F2-R - Structured-output semantic failure analysis.

## Legacy F1 Answers

Critical fields present and allowed by schema: True.
Failed validation cases: none.
Promising enough for a 12-case structured-output panel: False.

No memory, retrieval, provider routing, tool execution, backend route, frontend UI, queue, worker, hook, MCP, or BlueRev modeling behavior is added.

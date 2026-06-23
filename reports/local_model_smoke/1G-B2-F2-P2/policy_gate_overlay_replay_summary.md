# 1G-B2-F2-P2 Policy-Gate Overlay Replay Summary

Manual review is required. This replay does not prove semantic truth or approve runtime use.

- source report dir: `reports\local_model_smoke\1G-B2-F2-A`
- report dir: `reports\local_model_smoke\1G-B2-F2-P2`
- cases replayed: 8
- corrected outputs schema-valid: 8/8
- baseline hard score: 61/93
- overlay-corrected hard score: 74/93
- overlay improved hard score: True
- remaining hard boolean misses: {'contains_raw_private_or_ip_sensitive_context': 1, 'memory_boundary_or_write_authority_claim': 2, 'retrieval_or_source_use_request': 1, 'unresolved_assumption_or_open_decision': 5}
- remaining policy field misses: {'lifecycle_status_proposal': 8, 'sensitivity_bucket_proposal': 2}
- model calls made: False
- network calls made: False
- recommended next milestone: 1G-B2-F2-P3 - Integrate policy overlay into structured-output evaluation harness

## Intended Case Outcomes

### HG-018

- checks: {'blocked_blocked': True, 'external_provider_blocked': True}
- values: {'source_policy_for_future_retrieval': 'blocked', 'allowed_future_retrieval_behavior': 'blocked', 'clarification_required': False, 'external_provider_allowed': False, 'contains_secret_or_credential': False, 'contains_raw_private_or_ip_sensitive_context': True, 'mentions_external_provider_or_upload_intent': True, 'redaction_required': True, 'sensitivity_bucket_proposal': 'sensitive'}
- changed fields: ['clarification_required', 'hard_reason_code', 'hard_uncertain_fields', 'redaction_required']

### HG-007

- checks: {'candidate_discovery': True, 'not_mandatory_block': True}
- values: {'source_policy_for_future_retrieval': 'review_only', 'allowed_future_retrieval_behavior': 'candidate_discovery_only', 'clarification_required': False, 'external_provider_allowed': False, 'contains_secret_or_credential': False, 'contains_raw_private_or_ip_sensitive_context': False, 'mentions_external_provider_or_upload_intent': False, 'redaction_required': False, 'sensitivity_bucket_proposal': 'internal'}
- changed fields: ['allowed_future_retrieval_behavior', 'hard_reason_code', 'hard_uncertain_fields', 'sensitivity_bucket_proposal', 'source_policy_for_future_retrieval']

### HG-013

- checks: {'clarification_required': True}
- values: {'source_policy_for_future_retrieval': 'blocked', 'allowed_future_retrieval_behavior': 'clarification_required', 'clarification_required': True, 'external_provider_allowed': False, 'contains_secret_or_credential': False, 'contains_raw_private_or_ip_sensitive_context': False, 'mentions_external_provider_or_upload_intent': False, 'redaction_required': False, 'sensitivity_bucket_proposal': 'internal'}
- changed fields: ['allowed_future_retrieval_behavior', 'clarification_required', 'hard_reason_code', 'hard_uncertain_fields', 'retrieval_or_source_use_request', 'sensitivity_bucket_proposal']

### HG-017

- checks: {'secret_block_without_false_provider': True}
- values: {'source_policy_for_future_retrieval': 'blocked', 'allowed_future_retrieval_behavior': 'blocked', 'clarification_required': False, 'external_provider_allowed': False, 'contains_secret_or_credential': True, 'contains_raw_private_or_ip_sensitive_context': True, 'mentions_external_provider_or_upload_intent': False, 'redaction_required': True, 'sensitivity_bucket_proposal': 'secret'}
- changed fields: ['clarification_required', 'hard_uncertain_fields', 'mentions_external_provider_or_upload_intent']

### HG-024

- checks: {'review_gate': True}
- values: {'source_policy_for_future_retrieval': 'review_only', 'allowed_future_retrieval_behavior': 'review_gate_required', 'clarification_required': False, 'external_provider_allowed': False, 'contains_secret_or_credential': False, 'contains_raw_private_or_ip_sensitive_context': False, 'mentions_external_provider_or_upload_intent': False, 'redaction_required': False, 'sensitivity_bucket_proposal': 'internal'}
- changed fields: ['allowed_future_retrieval_behavior', 'hard_reason_code', 'hard_uncertain_fields', 'sensitivity_bucket_proposal', 'source_policy_for_future_retrieval']

### HG-025

- checks: {'clarification_required': True}
- values: {'source_policy_for_future_retrieval': 'blocked', 'allowed_future_retrieval_behavior': 'clarification_required', 'clarification_required': True, 'external_provider_allowed': False, 'contains_secret_or_credential': False, 'contains_raw_private_or_ip_sensitive_context': False, 'mentions_external_provider_or_upload_intent': False, 'redaction_required': False, 'sensitivity_bucket_proposal': 'internal'}
- changed fields: ['allowed_future_retrieval_behavior', 'hard_reason_code', 'hard_uncertain_fields', 'retrieval_or_source_use_request', 'sensitivity_bucket_proposal']

## Probable Comparator Or Holdout Mapping Ambiguities

- `HG-018` `memory_boundary_or_write_authority_claim`: Comparator expects a memory-boundary claim for whole-folder provider upload; overlay treats this primarily as provider/raw-private blocking.
- `HG-024` `lifecycle_status_proposal`: Holdout lifecycle can describe the new proposed instruction, while superseded describes the older referenced memory.

No memory, retrieval, provider routing, tool execution, backend route, frontend UI, queue, worker, hook, MCP, or BlueRev modeling behavior is added.

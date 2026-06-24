# 1G-B2-F2-B5-C-R2 Target-Based Provider Export Repair Summary

Manual review is required. This deterministic report does not prove semantic truth or approve runtime use.

- total cases: 16
- passed cases: 16/16
- failed cases: 0
- local Ollama calls made: False
- external provider calls made: False
- network calls made: False
- runtime approved: False
- semantic truth scored: False

## Acceptance

- provider_as_topic_en_it_provider_export_false: True
- bare_contrastive_provider_as_topic_en_it_provider_export_false: True
- elided_export_en_it_provider_export_true: True
- explicit_compound_export_en_it_provider_export_true: True
- positive_export_en_it_provider_export_true: True
- phase_b_provider_topic_preserved: True
- phase_b_inconsistent_boolean_guarded: True

## Phase A Cases

- `provider_topic_en_pricing`: provider/export=False, reason=`low_risk`, policy=`not_applicable`, passed=True
- `provider_topic_en_architecture`: provider/export=False, reason=`low_risk`, policy=`not_applicable`, passed=True
- `provider_topic_it_comparison`: provider/export=False, reason=`low_risk`, policy=`not_applicable`, passed=True
- `provider_topic_it_provider_note`: provider/export=False, reason=`low_risk`, policy=`not_applicable`, passed=True
- `self_email_topic_en`: provider/export=False, reason=`low_risk`, policy=`not_applicable`, passed=True
- `self_email_topic_it`: provider/export=False, reason=`low_risk`, policy=`not_applicable`, passed=True
- `bare_contrastive_topic_en`: provider/export=False, reason=`low_risk`, policy=`not_applicable`, passed=True
- `bare_contrastive_topic_it`: provider/export=False, reason=`low_risk`, policy=`not_applicable`, passed=True
- `elided_export_en`: provider/export=True, reason=`provider_or_upload_intent`, policy=`blocked`, passed=True
- `elided_export_it`: provider/export=True, reason=`provider_or_upload_intent`, policy=`blocked`, passed=True
- `explicit_compound_export_en`: provider/export=True, reason=`provider_or_upload_intent`, policy=`blocked`, passed=True
- `explicit_compound_export_it`: provider/export=True, reason=`provider_or_upload_intent`, policy=`blocked`, passed=True
- `positive_export_en`: provider/export=True, reason=`provider_or_upload_intent`, policy=`blocked`, passed=True
- `positive_export_it`: provider/export=True, reason=`provider_or_upload_intent`, policy=`blocked`, passed=True

## Phase B Cases

- `phase_b_provider_topic_preservation`: class=`none`, effective=`local_ai`/`source_card`/`high`, clamps=0, passed=True
- `phase_b_inconsistent_boolean_guard`: class=`local_ip_sensitive_memory`, effective=`local_ai`/`source_card`/`high`, clamps=1, passed=True

## Risk Note

B5-C-R2 intentionally requires a destination preposition for elided contrastive provider exports. Bare contrastive provider mentions are ambiguous and should not be forced to provider/export intent by deterministic regex. Future ambiguous export intent should route to clarification_required / USER_CONFIRM rather than another broad regex rule.

No runtime memory writes, runtime retrieval, provider routing, external provider calls, backend routes/API, frontend UI, DB schema/migration, tool execution, MCP/hooks/workers, BlueRev modeling behavior, or Qwen/Ollama calls are added.

# 1G-B2-F2-B5-C-R Compound Provider-Negation Repair Summary

- total trap cases: 11
- passed trap cases: 11
- failed trap cases: 0
- local Ollama calls made: False
- external provider calls made: False
- network calls made: False
- runtime approved: False
- semantic truth scored: False

| id | raw/private | provider/export | hard reason | policy | passed |
|---|---:|---:|---|---|---:|
| simple_en_local_only_negation | True | False | low_risk | not_applicable | True |
| simple_it_local_only_negation | True | False | low_risk | not_applicable | True |
| compound_en_negated_then_positive_export | True | True | provider_or_upload_intent | blocked | True |
| compound_it_negated_then_positive_export | True | True | provider_or_upload_intent | blocked | True |
| positive_en_export | True | True | provider_or_upload_intent | blocked | True |
| positive_it_export | True | True | provider_or_upload_intent | blocked | True |
| redaction_only_no_provider | True | False | low_risk | not_applicable | True |
| conditional_en_provider_export | True | True | provider_or_upload_intent | blocked | True |
| conditional_it_provider_export | True | True | provider_or_upload_intent | blocked | True |
| elided_en_export | True | True | provider_or_upload_intent | blocked | True |
| elided_it_export | True | True | provider_or_upload_intent | blocked | True |

B5-C-R repairs compound provider-negation and elided export-verb cases. The detector remains deterministic and conservative, but regex/clause logic is still not a full semantic parser. Ambiguous export intent should eventually route to clarification/review rather than being treated as safe by default.

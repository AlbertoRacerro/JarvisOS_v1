# 1G-B2-B Fast Secretary Recipe Ablation Summary

Manual review is required. This ablation does not prove semantic truth.

- total runs: 24
- MICRO_RULES v0.2 over MICRO v0.1: see pack_comparisons in JSON
- LITE_RULES v0.2 over LITE v0.1: see pack_comparisons in JSON
- best parse stability: {'context_pack_label': 'micro_rules_v0_2', 'model': 'qwen3:8b', 'runs': 3, 'json_parse_passes': 3, 'timeouts': 0, 'hard_matches': 23, 'hard_total': 24, 'soft_exact_matches': 14, 'soft_tolerant_matches': 15, 'soft_total': 15, 'critical_gate_failures': 0, 'manual_review_required': True}
- best hard score: {'context_pack_label': 'micro_rules_v0_2', 'model': 'qwen3:8b', 'runs': 3, 'json_parse_passes': 3, 'timeouts': 0, 'hard_matches': 23, 'hard_total': 24, 'soft_exact_matches': 14, 'soft_tolerant_matches': 15, 'soft_total': 15, 'critical_gate_failures': 0, 'manual_review_required': True}
- best soft tolerant score: {'context_pack_label': 'micro_rules_v0_2', 'model': 'qwen3:8b', 'runs': 3, 'json_parse_passes': 3, 'timeouts': 0, 'hard_matches': 23, 'hard_total': 24, 'soft_exact_matches': 14, 'soft_tolerant_matches': 15, 'soft_total': 15, 'critical_gate_failures': 0, 'manual_review_required': True}
- recommended next expanded profile: {'context_pack_label': 'micro_rules_v0_2', 'model': 'qwen3:8b', 'runs': 3, 'json_parse_passes': 3, 'timeouts': 0, 'hard_matches': 23, 'hard_total': 24, 'soft_exact_matches': 14, 'soft_tolerant_matches': 15, 'soft_total': 15, 'critical_gate_failures': 0, 'manual_review_required': True}

| pack | model | parse | hard | soft exact | soft tolerant | gate failures |
| --- | --- | --- | --- | --- | --- | --- |
| lite_rules_v0_2 | gemma4:12b-it-qat | 0/3 | 0/24 | 0/15 | 0/15 | 3 |
| lite_rules_v0_2 | qwen3:8b | 1/3 | 7/24 | 5/15 | 5/15 | 2 |
| lite_v0_1 | gemma4:12b-it-qat | 2/3 | 9/24 | 6/15 | 6/15 | 3 |
| lite_v0_1 | qwen3:8b | 2/3 | 15/24 | 8/15 | 9/15 | 1 |
| micro_rules_v0_2 | gemma4:12b-it-qat | 2/3 | 16/24 | 10/15 | 10/15 | 1 |
| micro_rules_v0_2 | qwen3:8b | 3/3 | 23/24 | 14/15 | 15/15 | 0 |
| micro_v0_1 | gemma4:12b-it-qat | 3/3 | 23/24 | 11/15 | 11/15 | 0 |
| micro_v0_1 | qwen3:8b | 3/3 | 20/24 | 11/15 | 11/15 | 0 |

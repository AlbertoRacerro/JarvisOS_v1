# 1G-B2-C Qwen Secretary Context Optimization Summary

Manual review is required. This ablation does not prove semantic truth.

## Direct Answers

1. Best parse stability: tie among `micro_v0_1`, `micro_rules_v0_2`, and `qwen_hybrid_v0_3` at 3/3 parses.
2. Best hard score: `qwen_hybrid_v0_3` with 24/24 hard matches.
3. Best soft tolerant score: `micro_rules_v0_2` with 15/15 soft tolerant matches.
4. Best critical gate performance: `qwen_hybrid_v0_3`, `micro_v0_1`, and `micro_rules_v0_2` had 0 gate failures; `qwen_hybrid_v0_3` wins after hard-score tie break.
5. Best score per approximate token: `micro_v0_1` with 37.634 hard matches per 1k tokens, 21.505 soft tolerant matches per 1k tokens, and 5.376 successful parses per 1k tokens.
6. Best content form for Qwen: hybrid.
7. Recommended default fast secretary pack: `qwen_hybrid_v0_3`.

- total runs: 21
- MICRO_RULES v0.2 over MICRO v0.1: see pack_comparisons in JSON
- LITE_RULES v0.2 over LITE v0.1: see pack_comparisons in JSON
- best parse stability: {'context_pack_label': 'micro_rules_v0_2', 'context_pack_path': 'docs\\context_packs\\JARVISOS_FAST_SECRETARY_MICRO_RULES_v0_2.md', 'context_pack_char_count': 5356, 'context_pack_approx_token_estimate': 1339, 'model': 'qwen3:8b', 'runs': 3, 'json_parse_passes': 3, 'timeouts': 0, 'hard_matches': 23, 'hard_total': 24, 'soft_exact_matches': 14, 'soft_tolerant_matches': 15, 'soft_total': 15, 'critical_gate_failures': 0, 'manual_review_required': True, 'hard_matches_per_1k_tokens': 17.177, 'soft_tolerant_matches_per_1k_tokens': 11.202, 'successful_parse_per_1k_tokens': 2.24}
- best hard score: {'context_pack_label': 'qwen_hybrid_v0_3', 'context_pack_path': 'docs\\context_packs\\JARVISOS_FAST_SECRETARY_QWEN_HYBRID_v0_3.md', 'context_pack_char_count': 5028, 'context_pack_approx_token_estimate': 1257, 'model': 'qwen3:8b', 'runs': 3, 'json_parse_passes': 3, 'timeouts': 0, 'hard_matches': 24, 'hard_total': 24, 'soft_exact_matches': 13, 'soft_tolerant_matches': 14, 'soft_total': 15, 'critical_gate_failures': 0, 'manual_review_required': True, 'hard_matches_per_1k_tokens': 19.093, 'soft_tolerant_matches_per_1k_tokens': 11.138, 'successful_parse_per_1k_tokens': 2.387}
- best soft tolerant score: {'context_pack_label': 'micro_rules_v0_2', 'context_pack_path': 'docs\\context_packs\\JARVISOS_FAST_SECRETARY_MICRO_RULES_v0_2.md', 'context_pack_char_count': 5356, 'context_pack_approx_token_estimate': 1339, 'model': 'qwen3:8b', 'runs': 3, 'json_parse_passes': 3, 'timeouts': 0, 'hard_matches': 23, 'hard_total': 24, 'soft_exact_matches': 14, 'soft_tolerant_matches': 15, 'soft_total': 15, 'critical_gate_failures': 0, 'manual_review_required': True, 'hard_matches_per_1k_tokens': 17.177, 'soft_tolerant_matches_per_1k_tokens': 11.202, 'successful_parse_per_1k_tokens': 2.24}
- best critical gate performance: {'context_pack_label': 'qwen_hybrid_v0_3', 'context_pack_path': 'docs\\context_packs\\JARVISOS_FAST_SECRETARY_QWEN_HYBRID_v0_3.md', 'context_pack_char_count': 5028, 'context_pack_approx_token_estimate': 1257, 'model': 'qwen3:8b', 'runs': 3, 'json_parse_passes': 3, 'timeouts': 0, 'hard_matches': 24, 'hard_total': 24, 'soft_exact_matches': 13, 'soft_tolerant_matches': 14, 'soft_total': 15, 'critical_gate_failures': 0, 'manual_review_required': True, 'hard_matches_per_1k_tokens': 19.093, 'soft_tolerant_matches_per_1k_tokens': 11.138, 'successful_parse_per_1k_tokens': 2.387}
- best score per approximate token: {'context_pack_label': 'micro_v0_1', 'context_pack_path': 'docs\\context_packs\\JARVISOS_FAST_SECRETARY_MICRO_v0_1.md', 'context_pack_char_count': 2230, 'context_pack_approx_token_estimate': 558, 'model': 'qwen3:8b', 'runs': 3, 'json_parse_passes': 3, 'timeouts': 0, 'hard_matches': 21, 'hard_total': 24, 'soft_exact_matches': 12, 'soft_tolerant_matches': 12, 'soft_total': 15, 'critical_gate_failures': 0, 'manual_review_required': True, 'hard_matches_per_1k_tokens': 37.634, 'soft_tolerant_matches_per_1k_tokens': 21.505, 'successful_parse_per_1k_tokens': 5.376}
- recommended next expanded profile: {'context_pack_label': 'qwen_hybrid_v0_3', 'context_pack_path': 'docs\\context_packs\\JARVISOS_FAST_SECRETARY_QWEN_HYBRID_v0_3.md', 'context_pack_char_count': 5028, 'context_pack_approx_token_estimate': 1257, 'model': 'qwen3:8b', 'runs': 3, 'json_parse_passes': 3, 'timeouts': 0, 'hard_matches': 24, 'hard_total': 24, 'soft_exact_matches': 13, 'soft_tolerant_matches': 14, 'soft_total': 15, 'critical_gate_failures': 0, 'manual_review_required': True, 'hard_matches_per_1k_tokens': 19.093, 'soft_tolerant_matches_per_1k_tokens': 11.138, 'successful_parse_per_1k_tokens': 2.387}

| pack | model | tokens | parse | hard | soft exact | soft tolerant | gate failures | hard/1k tok | soft tol/1k tok | parse/1k tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| micro_rules_v0_2 | qwen3:8b | 1339 | 3/3 | 23/24 | 14/15 | 15/15 | 0 | 17.177 | 11.202 | 2.24 |
| micro_v0_1 | qwen3:8b | 558 | 3/3 | 21/24 | 12/15 | 12/15 | 0 | 37.634 | 21.505 | 5.376 |
| qwen_examples_v0_3 | qwen3:8b | 1193 | 2/3 | 11/24 | 6/15 | 6/15 | 2 | 9.22 | 5.029 | 1.676 |
| qwen_hybrid_v0_3 | qwen3:8b | 1257 | 3/3 | 24/24 | 13/15 | 14/15 | 0 | 19.093 | 11.138 | 2.387 |
| qwen_output_strict_v0_3 | qwen3:8b | 858 | 2/3 | 14/24 | 7/15 | 7/15 | 1 | 16.317 | 8.159 | 2.331 |
| qwen_recipe_only_v0_3 | qwen3:8b | 1346 | 2/3 | 16/24 | 9/15 | 10/15 | 1 | 11.887 | 7.429 | 1.486 |
| qwen_recipe_table_v0_3 | qwen3:8b | 1118 | 2/3 | 16/24 | 10/15 | 10/15 | 1 | 14.311 | 8.945 | 1.789 |

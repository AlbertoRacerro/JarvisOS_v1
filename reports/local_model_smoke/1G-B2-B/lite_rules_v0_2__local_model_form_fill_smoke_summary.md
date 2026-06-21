# 1G-B2-A Local Model Form-Fill Smoke Summary

Manual review is required. This smoke run does not prove semantic truth.

- context pack: lite_rules_v0_2
- context pack path: docs\context_packs\JARVISOS_FAST_SECRETARY_LITE_RULES_v0_2.md
- context pack chars: 9456
- context pack approx tokens: 2364
- total runs: 6
- JSON parse passes: 1
- JSON parse failures: 5
- timeouts: 0
- errors: 0

| pack | model | case_id | json_parse | legacy_core | soft | hard | gate_failures | timeout | returncode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lite_rules_v0_2 | qwen3:8b | HG-001 | True | 8/9 | 5/5 exact, 5/5 tolerant | 7/8 | [] | False | 0 |
| lite_rules_v0_2 | qwen3:8b | HG-006 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| lite_rules_v0_2 | qwen3:8b | HG-016 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| lite_rules_v0_2 | gemma4:12b-it-qat | HG-001 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| lite_rules_v0_2 | gemma4:12b-it-qat | HG-006 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| lite_rules_v0_2 | gemma4:12b-it-qat | HG-016 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |

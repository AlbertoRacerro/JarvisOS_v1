# 1G-B2-A Local Model Form-Fill Smoke Summary

Manual review is required. This smoke run does not prove semantic truth.

- context pack: lite_v0_1
- context pack path: docs\context_packs\JARVISOS_FAST_SECRETARY_LITE_v0_1.md
- context pack chars: 6330
- context pack approx tokens: 1582
- total runs: 6
- JSON parse passes: 4
- JSON parse failures: 2
- timeouts: 0
- errors: 0

| pack | model | case_id | json_parse | legacy_core | soft | hard | gate_failures | timeout | returncode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lite_v0_1 | qwen3:8b | HG-001 | True | 7/9 | 5/5 exact, 5/5 tolerant | 7/8 | [] | False | 0 |
| lite_v0_1 | qwen3:8b | HG-006 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| lite_v0_1 | qwen3:8b | HG-016 | True | 8/9 | 3/5 exact, 4/5 tolerant | 8/8 | [] | False | 0 |
| lite_v0_1 | gemma4:12b-it-qat | HG-001 | True | 7/9 | 5/5 exact, 5/5 tolerant | 6/8 | ['useful_non_final_not_accepted_memory'] | False | 0 |
| lite_v0_1 | gemma4:12b-it-qat | HG-006 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| lite_v0_1 | gemma4:12b-it-qat | HG-016 | True | 2/9 | 1/5 exact, 1/5 tolerant | 3/8 | ['secret_implies_secret_blocked_blocked'] | False | 0 |

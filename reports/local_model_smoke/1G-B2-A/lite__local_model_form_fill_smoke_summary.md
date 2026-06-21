# 1G-B2-A Local Model Form-Fill Smoke Summary

Manual review is required. This smoke run does not prove semantic truth.

- context pack: lite
- context pack path: docs\context_packs\JARVISOS_FAST_SECRETARY_LITE_v0_1.md
- context pack chars: 6330
- context pack approx tokens: 1582
- total runs: 6
- JSON parse passes: 5
- JSON parse failures: 1
- timeouts: 0
- errors: 0

| pack | model | case_id | json_parse | legacy_core | soft | hard | gate_failures | timeout | returncode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lite | qwen3:8b | HG-001 | True | 8/9 | 5/5 | 7/8 | [] | False | 0 |
| lite | qwen3:8b | HG-006 | False | 0/9 | 0/5 | 0/8 | ['json_not_parsed'] | False | 0 |
| lite | qwen3:8b | HG-016 | True | 8/9 | 3/5 | 8/8 | [] | False | 0 |
| lite | gemma4:12b-it-qat | HG-001 | True | 9/9 | 5/5 | 8/8 | [] | False | 0 |
| lite | gemma4:12b-it-qat | HG-006 | True | 5/9 | 5/5 | 8/8 | [] | False | 0 |
| lite | gemma4:12b-it-qat | HG-016 | True | 7/9 | 2/5 | 8/8 | [] | False | 0 |

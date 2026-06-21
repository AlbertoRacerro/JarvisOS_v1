# 1G-B2-A Local Model Form-Fill Smoke Summary

Manual review is required. This smoke run does not prove semantic truth.

- context pack: full
- context pack path: docs\context_packs\JARVISOS_FAST_SECRETARY_FULL_v0_3.md
- context pack chars: 17422
- context pack approx tokens: 4356
- total runs: 6
- JSON parse passes: 2
- JSON parse failures: 4
- timeouts: 0
- errors: 0

| pack | model | case_id | json_parse | legacy_core | soft | hard | gate_failures | timeout | returncode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full | qwen3:8b | HG-001 | True | 7/9 | 4/5 | 7/8 | [] | False | 0 |
| full | qwen3:8b | HG-006 | False | 0/9 | 0/5 | 0/8 | ['json_not_parsed'] | False | 0 |
| full | qwen3:8b | HG-016 | True | 9/9 | 5/5 | 8/8 | [] | False | 0 |
| full | gemma4:12b-it-qat | HG-001 | False | 0/9 | 0/5 | 0/8 | ['json_not_parsed'] | False | 0 |
| full | gemma4:12b-it-qat | HG-006 | False | 0/9 | 0/5 | 0/8 | ['json_not_parsed'] | False | 0 |
| full | gemma4:12b-it-qat | HG-016 | False | 0/9 | 0/5 | 0/8 | ['json_not_parsed'] | False | 0 |

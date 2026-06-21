# 1G-B2-A Local Model Form-Fill Smoke Summary

Manual review is required. This smoke run does not prove semantic truth.

- context pack: micro_v0_1
- context pack path: docs\context_packs\JARVISOS_FAST_SECRETARY_MICRO_v0_1.md
- context pack chars: 2230
- context pack approx tokens: 558
- total runs: 6
- JSON parse passes: 6
- JSON parse failures: 0
- timeouts: 0
- errors: 0

| pack | model | case_id | json_parse | legacy_core | soft | hard | gate_failures | timeout | returncode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| micro_v0_1 | qwen3:8b | HG-001 | True | 7/9 | 4/5 exact, 4/5 tolerant | 6/8 | [] | False | 0 |
| micro_v0_1 | qwen3:8b | HG-006 | True | 6/9 | 4/5 exact, 4/5 tolerant | 6/8 | [] | False | 0 |
| micro_v0_1 | qwen3:8b | HG-016 | True | 7/9 | 3/5 exact, 3/5 tolerant | 8/8 | [] | False | 0 |
| micro_v0_1 | gemma4:12b-it-qat | HG-001 | True | 7/9 | 4/5 exact, 4/5 tolerant | 7/8 | [] | False | 0 |
| micro_v0_1 | gemma4:12b-it-qat | HG-006 | True | 6/9 | 5/5 exact, 5/5 tolerant | 8/8 | [] | False | 0 |
| micro_v0_1 | gemma4:12b-it-qat | HG-016 | True | 7/9 | 2/5 exact, 2/5 tolerant | 8/8 | [] | False | 0 |

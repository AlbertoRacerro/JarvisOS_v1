# 1G-B2-C Local Model Form-Fill Smoke Summary

Manual review is required. This smoke run does not prove semantic truth.

- context pack: qwen_examples_v0_3
- context pack path: docs\context_packs\JARVISOS_FAST_SECRETARY_QWEN_EXAMPLES_v0_3.md
- context pack chars: 4773
- context pack approx tokens: 1193
- total runs: 3
- JSON parse passes: 2
- JSON parse failures: 1
- timeouts: 0
- errors: 0

| pack | model | case_id | json_parse | legacy_core | soft | hard | gate_failures | timeout | returncode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen_examples_v0_3 | qwen3:8b | HG-001 | True | 8/9 | 5/5 exact, 5/5 tolerant | 8/8 | [] | False | 0 |
| qwen_examples_v0_3 | qwen3:8b | HG-006 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| qwen_examples_v0_3 | qwen3:8b | HG-016 | True | 2/9 | 1/5 exact, 1/5 tolerant | 3/8 | ['secret_implies_secret_blocked_blocked'] | False | 0 |

# 1G-B2-D-R Local Model Form-Fill Smoke Summary

Manual review is required. This smoke run does not prove semantic truth.

- context pack: qwen_hybrid_parse_safe_v0_4
- context pack path: docs\context_packs\JARVISOS_FAST_SECRETARY_QWEN_HYBRID_PARSE_SAFE_v0_4.md
- context pack chars: 4940
- context pack approx tokens: 1235
- total runs: 3
- JSON parse passes: 3
- JSON parse failures: 0
- timeouts: 0
- errors: 0

| pack | model | case_id | json_parse | legacy_core | soft | hard | gate_failures | timeout | returncode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen_hybrid_parse_safe_v0_4 | qwen3:8b | HG-006 | True | 9/9 | 5/5 exact, 5/5 tolerant | 8/8 | [] | False | 0 |
| qwen_hybrid_parse_safe_v0_4 | qwen3:8b | HG-018 | True | 5/9 | 5/5 exact, 5/5 tolerant | 4/8 | [] | False | 0 |
| qwen_hybrid_parse_safe_v0_4 | qwen3:8b | HG-022 | True | 9/9 | 5/5 exact, 5/5 tolerant | 8/8 | [] | False | 0 |

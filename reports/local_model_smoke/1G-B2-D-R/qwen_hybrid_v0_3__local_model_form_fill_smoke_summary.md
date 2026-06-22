# 1G-B2-D-R Local Model Form-Fill Smoke Summary

Manual review is required. This smoke run does not prove semantic truth.

- context pack: qwen_hybrid_v0_3
- context pack path: docs\context_packs\JARVISOS_FAST_SECRETARY_QWEN_HYBRID_v0_3.md
- context pack chars: 5028
- context pack approx tokens: 1257
- total runs: 3
- JSON parse passes: 0
- JSON parse failures: 3
- timeouts: 0
- errors: 0

| pack | model | case_id | json_parse | legacy_core | soft | hard | gate_failures | timeout | returncode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen_hybrid_v0_3 | qwen3:8b | HG-006 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-018 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-022 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |

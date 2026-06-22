# 1G-B2-D Local Model Form-Fill Smoke Summary

Manual review is required. This smoke run does not prove semantic truth.

- context pack: qwen_hybrid_v0_3
- context pack path: docs\context_packs\JARVISOS_FAST_SECRETARY_QWEN_HYBRID_v0_3.md
- context pack chars: 5028
- context pack approx tokens: 1257
- total runs: 12
- JSON parse passes: 9
- JSON parse failures: 3
- timeouts: 0
- errors: 0

| pack | model | case_id | json_parse | legacy_core | soft | hard | gate_failures | timeout | returncode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen_hybrid_v0_3 | qwen3:8b | HG-001 | True | 9/9 | 5/5 exact, 5/5 tolerant | 8/8 | [] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-006 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-016 | True | 8/9 | 4/5 exact, 5/5 tolerant | 8/8 | [] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-002 | True | 8/9 | 5/5 exact, 5/5 tolerant | 7/8 | [] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-005 | True | 8/9 | 3/5 exact, 3/5 tolerant | 8/8 | [] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-008 | True | 4/9 | 2/5 exact, 2/5 tolerant | 5/8 | [] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-009 | True | 7/9 | 5/5 exact, 5/5 tolerant | 6/8 | [] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-011 | True | 7/9 | 4/5 exact, 4/5 tolerant | 7/8 | [] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-017 | True | 8/9 | 4/5 exact, 4/5 tolerant | 8/8 | [] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-018 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-022 | False | 0/9 | 0/5 exact, 0/5 tolerant | 0/8 | ['json_not_parsed'] | False | 0 |
| qwen_hybrid_v0_3 | qwen3:8b | HG-028 | True | 6/9 | 5/5 exact, 5/5 tolerant | 5/8 | [] | False | 0 |

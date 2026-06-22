# 1G-B2-D Expanded Profiled Qwen Secretary Smoke Summary

Manual review is required. This smoke run does not prove semantic truth and
does not approve runtime use.

- total runs: 24
- model: `qwen3:8b`
- cases: `HG-001`, `HG-006`, `HG-016`, `HG-002`, `HG-005`, `HG-008`, `HG-009`, `HG-011`, `HG-017`, `HG-018`, `HG-022`, `HG-028`
- semantic truth scored: false
- manual review required: true

## Direct Answers

1. `qwen_hybrid_v0_3` did not maintain parse stability outside the optimized
   set. It parsed 9/12 and failed on `HG-006`, `HG-018`, and `HG-022`.
2. `qwen_hybrid_v0_3` did not maintain zero critical gate failures. It had 3
   gate failures, all caused by `json_not_parsed`.
3. `qwen_hybrid_v0_3` had the better hard score: 62/96 vs. 56/96.
4. Soft exact score was tied: both profiles scored 37/60.
5. Soft tolerant score was tied: both profiles scored 38/60.
6. `qwen_hybrid_v0_3` had the better score-per-token diagnostics.
7. Most concerning failures: `HG-006`, `HG-018`, and `HG-022`.
8. Keep `qwen_hybrid_v0_3` as the better profiled candidate, but do not promote
   beyond manual-review smoke use.
9. The profile is not ready for a larger 32-case run yet. Run
   `1G-B2-D-R - Qwen profile failure analysis` first.

## Profile Metrics

| pack | model | tokens | parse | hard | soft exact | soft tolerant | gate failures | hard/1k tok | soft tol/1k tok | parse/1k tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `micro_rules_v0_2` | `qwen3:8b` | 1339 | 8/12 | 56/96 | 37/60 | 38/60 | 4 | 41.822 | 28.379 | 5.975 |
| `qwen_hybrid_v0_3` | `qwen3:8b` | 1257 | 9/12 | 62/96 | 37/60 | 38/60 | 3 | 49.324 | 30.231 | 7.16 |

## Boundary

This report used no BlueRev vault, no 32-case run, no Gemma, no 14B/24B/31B
model, no external provider, and no runtime memory/retrieval/provider/tool
behavior.

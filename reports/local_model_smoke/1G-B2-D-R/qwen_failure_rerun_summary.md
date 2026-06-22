# 1G-B2-D-R Qwen Failure Rerun Summary

Manual review is required. This rerun does not prove semantic truth and does
not approve runtime use.

- total runs: 6
- model: `qwen3:8b`
- cases: `HG-006`, `HG-018`, `HG-022`
- semantic truth scored: false
- manual review required: true

## Direct Answers

1. `qwen_hybrid_v0_3` failed because Qwen emitted thinking/prose plus malformed
   JSON-like text with split strings and duplicated fragments.
2. The failures are mainly model/pack output issues, not clean parser issues.
3. Dominant cause: output discipline and local generation formatting
   instability; table/example structure may have contributed.
4. `micro_rules_v0_2` failed similarly on `HG-018` and `HG-022` in 1G-B2-D.
5. Parser-only repair is not justified because it would require heuristic repair
   of malformed model text.
6. `qwen_hybrid_parse_safe_v0_4` is justified.
7. v0.4 fixed the targeted parse/gate failures in the narrow rerun.
8. Recommended next milestone: `1G-B2-E - Full holdout Qwen secretary smoke run`.

## Rerun Metrics

| pack | model | tokens | parse | hard | soft exact | soft tolerant | gate failures | hard/1k tok | soft tol/1k tok | parse/1k tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen_hybrid_v0_3` | `qwen3:8b` | 1257 | 0/3 | 0/24 | 0/15 | 0/15 | 3 | 0.0 | 0.0 | 0.0 |
| `qwen_hybrid_parse_safe_v0_4` | `qwen3:8b` | 1235 | 3/3 | 20/24 | 15/15 | 15/15 | 0 | 16.194 | 12.146 | 2.429 |

## Remaining Risk

`HG-018` still missed hard provider/memory-boundary fields under v0.4. The next
full holdout smoke run must remain manual-review only and should track this
semantic boundary risk explicitly.

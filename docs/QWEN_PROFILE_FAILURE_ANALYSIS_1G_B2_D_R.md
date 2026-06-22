# Qwen Profile Failure Analysis 1G-B2-D-R

Milestone: `1G-B2-D-R - Qwen profile failure analysis`

This analysis is manual-review smoke evidence only. It does not prove semantic
truth and does not approve runtime use.

## Scope

Inputs inspected:

- `reports/local_model_smoke/1G-B2-D/`
- `docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_HYBRID_v0_3.md`
- `docs/context_packs/JARVISOS_FAST_SECRETARY_MICRO_RULES_v0_2.md`
- `scripts/local_model_form_fill_smoke.py`
- `tests/test_local_model_form_fill_smoke.py`
- `docs/LOCAL_MODEL_FORM_FILL_SMOKE_HARNESS.md`
- `docs/LOCAL_AI_EVALUATION_EVIDENCE.md`
- `README.md`

No BlueRev vault, 32-case run, Gemma run, larger Qwen model, external provider,
runtime memory, retrieval runtime, Context Pack Broker runtime, tool execution,
or BlueRev modeling behavior was used.

## Failure Classification

| pack | case | raw file | result file | category | visually recoverable JSON | parser should recover | likely cause | shortest safe mitigation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen_hybrid_v0_3` | `HG-006` | `reports/local_model_smoke/1G-B2-D/qwen_hybrid_v0_3__qwen3_8b__HG-006__raw.txt` | `reports/local_model_smoke/1G-B2-D/qwen_hybrid_v0_3__qwen3_8b__HG-006__result.json` | `extra_prose_before_json`, `unescaped_quote_or_backslash`, `unterminated_string` | yes | no | pack/model output discipline | parse-safe pack |
| `qwen_hybrid_v0_3` | `HG-018` | `reports/local_model_smoke/1G-B2-D/qwen_hybrid_v0_3__qwen3_8b__HG-018__raw.txt` | `reports/local_model_smoke/1G-B2-D/qwen_hybrid_v0_3__qwen3_8b__HG-018__result.json` | `extra_prose_before_json`, `unescaped_quote_or_backslash`, `schema_shape_mismatch` | yes | no | pack/model output discipline | parse-safe pack |
| `qwen_hybrid_v0_3` | `HG-022` | `reports/local_model_smoke/1G-B2-D/qwen_hybrid_v0_3__qwen3_8b__HG-022__raw.txt` | `reports/local_model_smoke/1G-B2-D/qwen_hybrid_v0_3__qwen3_8b__HG-022__result.json` | `extra_prose_before_json`, `unterminated_string`, `invalid_enum_fragment` | yes | no | pack/model output discipline | parse-safe pack |

The raw outputs were not timeouts or refusals. They started with Qwen thinking
text and then emitted a JSON-like object. The object was often visually
recoverable, but it contained malformed fragments such as split strings,
duplicated partial values, and enum/tag fragments split across lines.

Examples of the failure pattern:

- `HG-018`: duplicated summary fragment around `GPT-5.5`.
- `HG-022`: split tag fragment around `not_de` / `not_decided`.
- `HG-006`: split `domain_tags` and a newline inside `brief_rationale`.

## Parser Diagnosis

A parser-only fix is not justified for this milestone.

The parser already strips terminal control sequences, extracts JSON objects
from prose, and normalizes newlines inside JSON strings. The failed outputs
were malformed beyond clean extraction. Adding heuristic repair for duplicated
tokens or broken enum fragments could make invalid model output look accepted
and could hide semantic boundary failures.

The failure is mainly a model/pack output issue:

- the pack used headings, a routing table, and a minimal example;
- Qwen emitted thinking/prose despite JSON-only instructions;
- streamed terminal artifacts and line wrapping produced invalid JSON-like text;
- the baseline `micro_rules_v0_2` also failed on `HG-018` and `HG-022`, so the
  issue is not unique to the hybrid pack.

## Mitigation

Created:

```text
docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_HYBRID_PARSE_SAFE_v0_4.md
```

The v0.4 pack keeps the same semantic routing rules as v0.3 but changes the
shape:

- strict JSON-only instruction first;
- explicit start/end character rule;
- no routing table;
- no example block;
- no long explanatory sections;
- same enum set and semantic routing defaults.

No parser hardening was added.

## Narrow Rerun

Rerun scope:

```text
model: qwen3:8b
packs: qwen_hybrid_v0_3, qwen_hybrid_parse_safe_v0_4
cases: HG-006, HG-018, HG-022
total: 6 local Ollama runs
```

Reports:

- `reports/local_model_smoke/1G-B2-D-R/qwen_failure_rerun_summary.json`
- `reports/local_model_smoke/1G-B2-D-R/qwen_failure_rerun_summary.md`

Rerun result:

| pack | parse | hard | soft exact | soft tolerant | gates | tokens | hard/1k tok | soft tol/1k tok | parse/1k tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen_hybrid_v0_3` | 0/3 | 0/24 | 0/15 | 0/15 | 3 | 1257 | 0.0 | 0.0 | 0.0 |
| `qwen_hybrid_parse_safe_v0_4` | 3/3 | 20/24 | 15/15 | 15/15 | 0 | 1235 | 16.194 | 12.146 | 2.429 |

The v0.4 pack fixed the targeted parse/gate failures in the narrow rerun.

## Remaining Risk

`HG-018` still had hard-field misses under v0.4 despite parsing cleanly:

- expected sensitive/blocked handling for raw JarvisOS memory folder provider
  intent;
- actual output treated it as internal `review_only`/`none` with
  `local_senior_model`.

This is a semantic boundary issue, not a parse failure. It must remain
manual-review evidence and should be watched in the full holdout smoke run.

## Direct Answers

1. `qwen_hybrid_v0_3` failed because Qwen emitted thinking/prose plus malformed
   JSON-like objects with split strings and duplicated fragments.
2. Failures are mainly model/pack output issues, not clean parser issues.
3. The dominant cause is output discipline and local generation formatting
   instability. Table/example structure may have contributed by encouraging
   explanatory formatting.
4. `micro_rules_v0_2` failed similarly on `HG-018` and `HG-022`, while it parsed
   `HG-006`.
5. Parser-only repair is not justified because it would require heuristic
   correction of malformed model text.
6. `qwen_hybrid_parse_safe_v0_4` is justified.
7. v0.4 improved the failed cases in the narrow rerun: 3/3 parse, 0 gates,
   20/24 hard, and 15/15 soft tolerant.
8. Recommended next milestone:

```text
1G-B2-E - Full holdout Qwen secretary smoke run
```

The next run should use `qwen_hybrid_parse_safe_v0_4`, remain manual-review
only, and specifically watch provider/memory-boundary cases such as `HG-018`.

# Local Model Form-Fill Smoke Harness

Milestones:

- 1G-A - Local model form-fill smoke harness skeleton
- 1G-B1 - Installed local model form-fill smoke run
- 1G-B2-A - Fast secretary context pack compression and scoring refinement
- 1G-B2-B - Fast secretary recipe ablation
- 1G-B2-C - Qwen secretary context optimization

## Purpose

This document describes the local model form-fill smoke harness.

The harness is model-agnostic. Dry-run mode loads the holdout intake
generalization set, loads a local candidate-model config, validates both files,
selects cases, lists candidate models, and prints the planned smoke-run shape.

Real local mode is explicit and bounded behind `--run-local`. It calls only the
local Ollama CLI for selected installed models and selected holdout cases.

Context-pack mode is optional. When `--context-pack` is provided, the harness
adds the pack content to the prompt, records pack metadata in results, and uses
`--pack-label` in report filenames and summaries.

## Installed-Model-Only Policy

The candidate config uses only the installed Ollama model names supplied for
this milestone:

- `mistral-small3.2:24b`
- `qwen3:14b`
- `qwen3:8b`
- `gemma4:31b-it-qat`
- `gemma4:12b-it-qat`

The source config is:

```text
configs/local_model_candidates.example.json
```

All candidates default to:

```json
"enabled": false
```

Disabled-by-default keeps the skeleton from accidentally becoming a live model
runner.

## No-Pull And No-Install Policy

The harness must not install packages or fetch models.

Do not run:

- `ollama pull`
- `ollama serve`
- Ollama generation endpoints outside this harness
- external provider APIs
- package installers

The script uses Python standard library only.

## Dry-Run Boundary

Dry-run mode must not call Ollama.

It may:

- load JSONL holdout cases;
- validate the 32-case holdout structure;
- validate unique `case_id` values;
- validate required expected fields;
- load candidate config;
- validate candidate config schema;
- select holdout cases;
- list configured candidates;
- validate fake output records for tests.

It must not:

- call a provider or model API;
- open network connections;
- score real model quality;
- execute retry logic;
- write memory;
- run retrieval;
- run Context Pack Broker behavior;
- execute tools;
- start BlueRev modeling.

If neither `--dry-run` nor `--run-local` is provided, the script exits nonzero.

## 1G-B1 Real Local Run Scope

1G-B1 allows exactly a narrow installed local model smoke run.

Selected models:

```text
qwen3:8b
gemma4:12b-it-qat
```

Selected cases:

```text
HG-001
HG-006
HG-016
```

Run command:

```powershell
python scripts/local_model_form_fill_smoke.py --run-local --models qwen3:8b,gemma4:12b-it-qat --case-ids HG-001,HG-006,HG-016 --timeout-seconds 180
```

The run writes reports under:

```text
reports/local_model_smoke/1G-B1/
```

Each model/case pair writes:

- one raw `.txt` file;
- one parsed/scored `.json` file.

The run also writes:

- `reports/local_model_smoke/1G-B1/local_model_form_fill_smoke_summary.json`
- `reports/local_model_smoke/1G-B1/local_model_form_fill_smoke_summary.md`

All results require manual review. Core-field exact matches are structural
comparison evidence only; they do not prove semantic truth, safety, memory
readiness, retrieval readiness, provider readiness, or BlueRev validity.

## 1G-B2-A Context Pack Comparison

1G-B2-A adds prepared Fast Secretary context packs:

- `docs/context_packs/JARVISOS_FAST_SECRETARY_MICRO_v0_1.md`
- `docs/context_packs/JARVISOS_FAST_SECRETARY_LITE_v0_1.md`
- `docs/context_packs/JARVISOS_FAST_SECRETARY_FULL_v0_3.md`

The comparison uses the same bounded models and cases as 1G-B1:

```text
qwen3:8b
gemma4:12b-it-qat

HG-001
HG-006
HG-016
```

Reports are written under:

```text
reports/local_model_smoke/1G-B2-A/
```

Summary files:

- `reports/local_model_smoke/1G-B2-A/micro__local_model_form_fill_smoke_summary.json`
- `reports/local_model_smoke/1G-B2-A/lite__local_model_form_fill_smoke_summary.json`
- `reports/local_model_smoke/1G-B2-A/full__local_model_form_fill_smoke_summary.json`

The 1G-B2-A result:

```text
MICRO: 6/6 JSON parse passes, 0 timeouts
LITE:  5/6 JSON parse passes, 0 timeouts
FULL:  2/6 JSON parse passes, 0 timeouts
```

The harness now separates:

- soft field scores;
- hard field scores;
- legacy core field scores;
- critical gate failures.

This is still smoke evidence only. It does not prove semantic truth or approve
runtime use.

## 1G-B2-B Recipe Ablation

1G-B2-B adds compact recipe variants without overwriting v0.1 packs:

- `docs/context_packs/JARVISOS_FAST_SECRETARY_MICRO_RULES_v0_2.md`
- `docs/context_packs/JARVISOS_FAST_SECRETARY_LITE_RULES_v0_2.md`

The v0.2 packs add compact case routing recipes for:

- JarvisOS memory boundary / architecture rules;
- BlueRev unresolved engineering assumptions;
- API key / credential / secret handling;
- output discipline for JSON-only responses.

The ablation matrix remains bounded:

```text
packs: micro_v0_1, micro_rules_v0_2, lite_v0_1, lite_rules_v0_2
models: qwen3:8b, gemma4:12b-it-qat
cases: HG-001, HG-006, HG-016
total: 24 local Ollama runs
```

Reports are written under:

```text
reports/local_model_smoke/1G-B2-B/
```

Summary files:

- `reports/local_model_smoke/1G-B2-B/recipe_ablation_summary.json`
- `reports/local_model_smoke/1G-B2-B/recipe_ablation_summary.md`

High-level result:

```text
micro_v0_1:       6/6 parse, 43/48 hard, 22/30 soft tolerant, 0 gates
micro_rules_v0_2: 5/6 parse, 39/48 hard, 25/30 soft tolerant, 1 gate
lite_v0_1:        4/6 parse, 24/48 hard, 15/30 soft tolerant, 4 gates
lite_rules_v0_2:  1/6 parse,  7/48 hard,  5/30 soft tolerant, 5 gates
```

Best profile for the next expanded run:

```text
micro_rules_v0_2 + qwen3:8b
```

That profile produced 3/3 parse, 23/24 hard, 15/15 soft tolerant, and 0
critical gate failures. This is still smoke evidence only.

## 1G-B2-C Qwen Secretary Context Optimization

1G-B2-C keeps the benchmark bounded to Qwen and the same three holdout cases.

New Qwen-focused packs:

- `docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_RECIPE_ONLY_v0_3.md`
- `docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_RECIPE_TABLE_v0_3.md`
- `docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_EXAMPLES_v0_3.md`
- `docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_HYBRID_v0_3.md`
- `docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_OUTPUT_STRICT_v0_3.md`

The optimization matrix:

```text
packs: micro_v0_1, micro_rules_v0_2, qwen_recipe_only_v0_3, qwen_recipe_table_v0_3, qwen_examples_v0_3, qwen_hybrid_v0_3, qwen_output_strict_v0_3
model: qwen3:8b
cases: HG-001, HG-006, HG-016
total: 21 local Ollama runs
```

Reports are written under:

```text
reports/local_model_smoke/1G-B2-C/
```

Summary files:

- `reports/local_model_smoke/1G-B2-C/qwen_context_optimization_summary.json`
- `reports/local_model_smoke/1G-B2-C/qwen_context_optimization_summary.md`

High-level result:

```text
micro_v0_1:                 3/3 parse, 21/24 hard, 12/15 soft tolerant, 0 gates, 558 tokens
micro_rules_v0_2:           3/3 parse, 23/24 hard, 15/15 soft tolerant, 0 gates, 1339 tokens
qwen_recipe_only_v0_3:      2/3 parse, 16/24 hard, 10/15 soft tolerant, 1 gate, 1346 tokens
qwen_recipe_table_v0_3:     2/3 parse, 16/24 hard, 10/15 soft tolerant, 1 gate, 1118 tokens
qwen_examples_v0_3:         2/3 parse, 11/24 hard,  6/15 soft tolerant, 2 gates, 1193 tokens
qwen_hybrid_v0_3:           3/3 parse, 24/24 hard, 14/15 soft tolerant, 0 gates, 1257 tokens
qwen_output_strict_v0_3:    2/3 parse, 14/24 hard,  7/15 soft tolerant, 1 gate, 858 tokens
```

Best default fast secretary pack for the next Qwen run:

```text
qwen_hybrid_v0_3
```

`micro_v0_1` remains the best score-per-token profile, but `qwen_hybrid_v0_3`
is the best balanced default because it reached 3/3 parse, 24/24 hard, 14/15
soft tolerant, and 0 critical gate failures.

## Dry-Run Behavior

Example:

```powershell
python scripts/local_model_form_fill_smoke.py --dry-run --include-disabled --max-cases 3
```

Dry-run output includes:

- holdout path;
- config path;
- loaded holdout case count;
- selected case IDs;
- configured candidate model IDs and Ollama names;
- enabled model count;
- note that inference is disabled in 1G-A;
- context pack metadata when `--context-pack` is provided;
- multiple context packs when `--context-packs` and `--pack-labels` are provided;
- expected future report path.

Dry-run mode does not write a report.

## Candidate Config

The candidate config records local model metadata only:

- `model_id`;
- `ollama_name`;
- `family_guess`;
- `installed`;
- `enabled`;
- `notes`.

The config is an example file. It is not runtime approval for any model.

## Unit Tests

Use `unittest`, not pytest:

```powershell
python -m unittest discover -s tests
```

The tests cover:

- real holdout JSONL loading;
- 32-case holdout count;
- unique `case_id` values;
- required expected fields;
- real candidate config loading;
- exact supplied installed model names;
- default-disabled candidates;
- explicit case-ID selection;
- fake output validation for valid, missing, and unknown case IDs.
- context pack loading and metadata;
- soft/hard score separation;
- legacy field compatibility;
- critical gate detection;
- dry-run with a context pack.
- v0.2 recipe pack loading;
- domain-tags-aware tolerant soft scoring;
- secret/security soft-domain tolerance;
- multi-pack label preservation;
- legacy v0.1 report compatibility.
- Qwen v0.3 pack loading;
- score-per-token diagnostics in summaries.

## Future 1G-B

After 1G-B2-C, the next milestone is:

```text
1G-B2-D - Expanded profiled Qwen secretary smoke run
```

1G-B2-D may decide whether to expand the profiled Qwen secretary smoke scope.
Any live run must remain local, explicit, bounded, auditable, and separate from
runtime memory, retrieval, provider routing, tool execution, and BlueRev
modeling.

## Milestone Boundary Confirmation

1G-B2-C adds Qwen-focused pack variants, score-per-token diagnostics, generated
local smoke reports, docs, and `unittest` coverage.

It adds no:

- backend routes or APIs;
- frontend code;
- database migration;
- runtime models;
- repository or storage classes;
- model inference outside the explicit local Ollama smoke command;
- Ollama model pull;
- Ollama model serve;
- Ollama generation call outside the explicit local smoke command;
- provider call;
- memory runtime;
- retrieval runtime;
- Context Pack Broker runtime;
- tool execution;
- hooks;
- MCP;
- worker or viewer;
- BlueRev modeling;
- external reference audit;
- vendored code.

This milestone does not start `1G-B2-D - Expanded profiled Qwen secretary smoke run`.

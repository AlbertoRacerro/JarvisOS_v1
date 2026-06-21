# Local Model Form-Fill Smoke Harness

Milestone: 1G-A - Local model form-fill smoke harness skeleton

## Purpose

This document describes the local model form-fill smoke harness skeleton.

The harness is model-agnostic and dry-run only in 1G-A. It loads the holdout
intake generalization set, loads a local candidate-model config, validates both
files, selects cases, lists candidate models, and prints the planned future
smoke-run shape.

It does not call any model.

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

1G-A must not install packages or fetch models.

Do not run:

- `ollama run`
- `ollama pull`
- `ollama serve`
- Ollama generation endpoints
- external provider APIs
- package installers

The script uses Python standard library only.

## No-Inference Boundary In 1G-A

`scripts/local_model_form_fill_smoke.py` is a dry-run harness skeleton.

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

- call Ollama;
- call a provider or model API;
- open network connections;
- score real model quality;
- execute retry logic;
- write memory;
- run retrieval;
- run Context Pack Broker behavior;
- execute tools;
- start BlueRev modeling.

If `--dry-run` is not provided, the script exits nonzero with:

```text
Only dry-run mode is implemented in 1G-A; no model inference is available.
```

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
- expected future report path.

The skeleton does not write a report in 1G-A.

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

## Future 1G-B

The next milestone is:

```text
1G-B - Installed local model form-fill smoke run
```

1G-B may decide whether and how to run installed local models. Any live run
must remain local, explicit, bounded, auditable, and separate from runtime
memory, retrieval, provider routing, tool execution, and BlueRev modeling.

## Milestone Boundary Confirmation

1G-A adds a config file, dry-run script, docs, and `unittest` tests only.

It adds no:

- backend routes or APIs;
- frontend code;
- database migration;
- runtime models;
- repository or storage classes;
- model inference;
- Ollama model pull;
- Ollama model serve;
- Ollama generation call;
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

This milestone does not start `1G-B - Installed local model form-fill smoke run`.

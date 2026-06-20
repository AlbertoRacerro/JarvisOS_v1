# 0E-D8 Local Gemma Runtime Adapter Dry Run

## 1. Executive Judgement

0E-D8 adds a bounded local runtime adapter dry run for Gemma-compatible local endpoints. It connects local model output only to the existing D7/D7B/D7C evaluation harness: strict schema validation, deterministic scoring, and local report aggregation.

This is not local Jarvis chat, not memory runtime, not file/database retrieval, not context broker runtime, not local gatekeeper enforcement, not provider routing, not external API use, and not BlueRev modeling.

## 2. Why D8 Is Runtime Dry-Run Only

D8 exists to test whether local Gemma 12B/31B can produce `GemmaEvalOutput` objects for golden cases. It is allowed because it helps measure whether Gemma can later support JarvisOS workflows. It is not a new product direction.

The D8 flow is:

```text
golden case
-> protocol prompt
-> local Gemma output
-> strict schema validation
-> deterministic scorer
-> local evaluation report
```

## 3. Supported Local Runtime Assumptions

Runtime discovery found Ollama processes on the local machine. D8 therefore supports a local OpenAI-compatible HTTP endpoint first, with a default compatible with Ollama's local endpoint shape:

```text
http://localhost:11434/v1/chat/completions
```

This same adapter can be pointed at a local LM Studio or llama.cpp OpenAI-compatible endpoint if it is explicitly configured and still passes localhost validation.

Automated tests mock all runtime calls. They do not require Ollama, LM Studio, llama.cpp, or any model server to be running.

## 4. Local-Only Endpoint Safety

The adapter accepts only:

- `http://localhost:...`
- `http://127.0.0.1:...`
- `http://[::1]:...`

It rejects:

- `https://...`
- external domains;
- private LAN IPs;
- URLs containing credentials;
- cloud provider URLs;
- any API-key based configuration.

No API key is required or used.

## 5. Adapter Design

The module lives in `backend/app/modules/local_ai/`.

Key files:

- `config.py`: local endpoint and model configuration with localhost-only validation.
- `adapter.py`: local OpenAI-compatible HTTP call wrapper.
- `prompt_builder.py`: D8 prompt builder from golden cases.
- `errors.py`: structured local failure codes.

The adapter returns structured results instead of raising raw HTTP/provider-style errors upward.

Failure codes include:

- `runtime_unavailable`
- `local_endpoint_invalid`
- `timeout`
- `invalid_json`
- `schema_invalid`
- `prose_instead_of_schema`
- `unexpected_local_http_error`

## 6. Prompt/Protocol Design

The prompt builder combines:

- the stable local operating-brain protocol;
- golden case input;
- provided context;
- `GemmaEvalOutput` schema;
- controlled context package vocabulary;
- JSON-only instruction;
- warnings not to include prose outside JSON.

The prompt does not include the golden expected answer, expected labels, `must_include`, `must_not_include`, expected decisions, or expected TODOs.

The protocol is documented in `docs/GEMMA_LOCAL_OPERATING_SYSTEM_PROTOCOL.md`.

## 7. Evaluation Runner Design

The runner lives at:

```text
backend/app/modules/local_ai_eval/run_gemma_eval.py
```

Example dry fake run:

```powershell
cd C:\Users\thera\Documents\JarvisOS_v1\backend
.\.venv\Scripts\python -m app.modules.local_ai_eval.run_gemma_eval --fake correct --limit 5
```

Example local Gemma run, if a compatible local server is already running:

```powershell
cd C:\Users\thera\Documents\JarvisOS_v1\backend
.\.venv\Scripts\python -m app.modules.local_ai_eval.run_gemma_eval --endpoint http://localhost:11434/v1/chat/completions --model gemma3:12b --limit 5
```

The runner always builds prompts from golden cases, validates output against `GemmaEvalOutput`, and runs `score_output`.

## 8. Failure Modes

D8 distinguishes:

- runtime unavailable;
- timeout;
- invalid JSON;
- prose instead of schema;
- schema invalid;
- scorer failure;
- critical scorer failure.

Schema-invalid output is not softened into success.

## 9. Report Format

The local report includes:

- `model_name`
- `runtime_endpoint`
- `case_count`
- `schema_valid_count`
- `passed_count`
- `critical_failure_count`
- `average_score`
- `failure_counts_by_category`
- `failure_counts_by_failure_code`
- `runtime_unavailable_count`
- `timeout_count`
- `invalid_json_count`
- `schema_invalid_count`
- per-case results

The current runner prints JSON to stdout. It does not write project files by default.

## 10. How To Run Manual Gemma Evaluation

1. Start a local model server that exposes an OpenAI-compatible local endpoint.
2. Keep the endpoint local, for example `http://localhost:11434/v1/chat/completions`.
3. Run a tiny limit first, such as `--limit 5`.
4. Inspect `schema_valid_count`, `passed_count`, `critical_failure_count`, and failure counts.
5. Do not treat manual impressions as evaluation results; use the scorer report.

## 11. What D8 Does Not Enable

D8 does not enable:

- local chat;
- conversation history;
- memory runtime;
- file/folder access;
- database retrieval;
- context broker runtime;
- local gatekeeper enforcement;
- autonomous tools;
- provider routing;
- external APIs;
- frontend UI;
- BlueRev modeling.

## 12. Recommended Next Milestone

Recommended next milestone:

```text
0E-D9 - Gemma 12B vs 31B Evaluation Run And Failure Diagnosis
```

D9 should run real local evaluations and diagnose failures as model weakness, missing context, prompt/protocol weakness, schema difficulty, task ambiguity, output length/token limits, runtime latency/timeout, or JSON compliance weakness.

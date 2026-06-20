# 0E-D9R Local Gemma Runtime And JSON Compliance Follow-Up

## 1. Executive Judgement

0E-D9R diagnosed the D9 failure without adding runtime features.

Decision:

```text
B. Compact schema works but full D7 schema is too heavy; proceed to staged schema design.
```

This decision applies mainly to `gemma4:31b-it-qat`. The 31B model can produce valid JSON and can satisfy a compact JSON schema when called through Ollama native structured output. However, the full D7 `GemmaEvalOutput` one-case probe still timed out under the current local setup, even with native schema output and a simplified prompt.

`gemma4:12b-it-qat` is weaker: it can emit a tiny direct JSON object, but it failed the compact schema probe in both OpenAI-compatible and native schema modes.

No evidence from D9R approves Gemma for local chat, memory runtime, context broker runtime, local gatekeeper enforcement, provider routing, autonomous tools, or BlueRev modeling.

## 2. Runtime Discovery

Local runtime:

```text
Ollama
```

Available Gemma models:

```text
gemma4:31b-it-qat
gemma4:12b-it-qat
```

Initial `ollama ps` output showed no loaded model.

Endpoints used:

```text
http://localhost:11434/v1/chat/completions
http://localhost:11434/api/chat
```

No external URLs, HTTPS endpoints, API keys, provider APIs, frontend routes, database tables, or persistent runtime features were added.

## 3. Models Tested

| Model | Tested |
| --- | --- |
| `gemma4:12b-it-qat` | yes |
| `gemma4:31b-it-qat` | yes |

## 4. Adapter Modes Tested

Two local modes were tested by diagnostic scripts only:

| Mode | Endpoint | Structured Output Mechanism |
| --- | --- | --- |
| OpenAI-compatible | `/v1/chat/completions` | `response_format: {"type": "json_object"}` |
| Ollama native chat | `/api/chat` | `format: "json"` or `format: <JSON schema>` |

No persistent native Ollama adapter was added to source code. D9R stayed CLI/report-only.

## 5. Minimal JSON Probe Results

### Verbose Minimal Prompt

A first minimal prompt using several JSON-only instruction lines returned empty content for both models and both adapter modes.

| Model | Mode | Valid JSON | Approx Latency |
| --- | --- | --- | ---: |
| 12B | OpenAI-compatible JSON object | no | 15.340s |
| 12B | Native `format: "json"` | no | 5.652s |
| 31B | OpenAI-compatible JSON object | no | 22.470s |
| 31B | Native `format: "json"` | no | 53.707s |

Diagnosis: the model/runtime can respond, but this prompt shape can produce empty content. This points away from the D7 schema alone and toward prompt/template sensitivity.

### Direct Minimal Prompt

A shorter direct prompt worked for both models:

```text
Return exactly this JSON object and nothing else: {"ok": true, "model_role": "local_probe", "schema_version": 1}
```

| Model | Mode | Valid JSON | Keys | Approx Latency |
| --- | --- | --- | --- | ---: |
| 12B | OpenAI-compatible JSON object | yes | `model_role`, `ok`, `schema_version` | 5.346s |
| 12B | Native `format: "json"` | yes | `model_role`, `ok`, `schema_version` | 5.463s |
| 31B | OpenAI-compatible JSON object | yes | `model_role`, `ok`, `schema_version` | 23.179s |
| 31B | Native `format: "json"` | yes | `model_role`, `ok`, `schema_version` | 54.919s |

Diagnosis: both models can emit strict JSON for a tiny direct task. The D9 failure is not simply "Gemma cannot emit JSON."

## 6. Compact Schema Probe Results

Compact schema fields:

```json
{
  "task_type": "classification",
  "state": "READY_LOCAL_RESPONSE",
  "selected_local_action": "LOCAL_ONLY",
  "confidence": 0.75,
  "reasons": ["local probe"],
  "schema_version": 1
}
```

| Model | Mode | Valid JSON | Compact Schema Valid | Exact Required Values | Approx Latency |
| --- | --- | --- | --- | --- | ---: |
| 12B | OpenAI-compatible JSON object | no | no | no | 6.476s |
| 12B | Native `format: <schema>` | no | no | no | 20.541s |
| 31B | OpenAI-compatible JSON object | no | no | no | 34.806s |
| 31B | Native `format: <schema>` | yes | yes | yes | 77.690s |

Diagnosis:

- Native Ollama schema output materially improves 31B compliance.
- Native schema output does not rescue 12B on compact schema.
- OpenAI-compatible `response_format` is weaker than native Ollama schema for this local setup.

## 7. Full D7 One-Case Probe Result

Full D7 case:

```text
conversation_continuity_001
```

Model:

```text
gemma4:31b-it-qat
```

Probes:

| Probe | Result | Approx Latency |
| --- | --- | ---: |
| Current D8 prompt + OpenAI-compatible JSON object | timeout | 182.429s |
| Current D8 prompt + native full schema | timeout | 182.652s |
| Simplified prompt + native full schema | timeout | 182.646s |

Diagnosis:

- Full D7 output is still too heavy for the current 31B local setup.
- Simplifying the wrapper prompt alone did not fix the full schema path.
- Native schema helps compact output, but not the full D7 schema at current output length/timeout/runtime speed.

## 8. Category Sample Result

Category sampling was not reached.

Reason:

- 12B failed compact schema.
- 31B passed compact native schema but timed out on full D7 one-case.

Running category samples would not be meaningful until a staged schema can complete one D7-like case.

## 9. 12B Diagnosis

12B can produce tiny direct JSON in both tested modes.

12B failed:

- verbose minimal JSON prompt;
- compact schema in OpenAI-compatible mode;
- compact schema in native Ollama schema mode;
- earlier D9 full D7 smoke subset.

Conclusion:

```text
12B can only be considered for very narrow local utility probes right now.
```

It should not be treated as a local operating-brain candidate.

## 10. 31B Diagnosis

31B can produce tiny direct JSON in both tested modes.

31B can satisfy the compact schema only with native Ollama schema output.

31B fails the current full D7 one-case path by timeout.

Conclusion:

```text
31B may be usable after staged schema and runtime optimization, but not with the full D7 schema in one pass.
```

## 11. Is The Current D8 Prompt Too Heavy?

Partly yes, but the prompt is not the only problem.

Evidence:

- A direct minimal prompt works.
- A more verbose minimal prompt can produce empty content.
- A simplified full-D7 prompt still timed out for 31B.

Therefore the issue is a combination of:

1. prompt/template sensitivity;
2. full schema/output size;
3. local 31B latency;
4. the OpenAI-compatible JSON hint being weaker than native Ollama schema mode.

## 12. Does Native Ollama Structured Output Improve Compliance?

Yes, but only within limits.

Native Ollama schema mode improved 31B compact schema compliance from failure to success.

It did not make 12B pass compact schema.

It did not make the full D7 one-case probe complete for 31B.

## 13. Failure Classification

| Area | Diagnosis |
| --- | --- |
| Runtime | 31B is too slow for full D7 under current settings |
| Prompt | direct prompts work better than verbose protocol prompts |
| Schema | full D7 schema is too heavy for one-pass local generation |
| Model | 12B appears too weak for compact operating-brain schema |
| Adapter | OpenAI-compatible JSON hint is weaker than native Ollama schema |

## 14. Recommended Next Milestone

Recommended next:

```text
0E-D10 - Staged Local Gemma Schema And Protocol Simplification
```

Scope:

- no chat;
- no memory runtime;
- no retrieval;
- no local gatekeeper;
- no provider routing;
- no frontend;
- no BlueRev modeling;
- no full 95-case run;
- design and test staged schemas before returning to D7 full output.

Suggested D10 stages:

1. Tiny strict JSON probe.
2. Compact local-action schema.
3. Sensitivity/classification-only schema.
4. Context-request-only schema.
5. Tool-grounding-only schema.
6. Only then reconsider full `GemmaEvalOutput`.

## 15. Report Artifacts

Local reports were written under the ignored directory:

```text
backend/local_eval_reports/
```

D9R reports:

```text
d9r_local_gemma_json_compliance_20260620_145202.json
d9r_local_gemma_direct_json_probe_20260620_145556.json
d9r_local_gemma_compact_schema_validation_20260620_145958.json
d9r_gemma31b_full_d7_one_case_probe_20260620_150312.json
```

These are local diagnostic artifacts, not product data.

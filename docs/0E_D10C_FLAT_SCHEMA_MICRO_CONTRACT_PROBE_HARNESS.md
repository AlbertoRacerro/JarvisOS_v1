# 0E-D10C Flat Schema Micro-Contract Probe Harness

## 1. Executive Judgement

0E-D10C replaced the misleading D10B-style Pydantic-schema probe path with a flat-schema, thinking-aware, lightweight-model-first probe harness.

Decision:

```text
B. 12B is viable only for narrow classification utilities, not broad local orchestration.
D. 31B is useful as occasional local heavy expert but too slow for routine orchestration.
E. Thinking/token-budget behavior must be controlled before any runtime integration.
F. FunctionGemma should remain future-track until tool catalog and dataset exist.
```

`gemma4:12b-it-qat` passed and repeated only the two classification-style contracts tested here: task classification and sensitivity classification. It failed context request, TODO extraction, decision extraction, and evidence selection because it exhausted the thinking budget and returned empty final content.

`gemma4:31b-it-qat` passed the limited comparison on task classification, context request, and sensitivity check, but with high latency.

## 2. Why D10C Replaces D10B-Style Probing

D10B passed raw Pydantic JSON Schema into Ollama `format` and reported all 16 cases as invalid JSON.

D10B-R showed that this was misleading:

- empty `message.content` can occur with non-empty `message.thinking`;
- `done_reason=length` can mean the model spent the output budget thinking;
- flat/direct schemas work better than raw Pydantic schema export;
- 12B and 31B can produce valid JSON when the prompt, schema, and output budget are aligned.

D10C therefore uses:

- hand-written flat schemas;
- no `$defs`;
- no `$ref`;
- no `anyOf`;
- direct prompts;
- `num_predict=512`;
- thinking-aware failure classification.

## 3. Flat Schema Strategy

The D10C harness lives at:

```text
backend/app/modules/local_ai_eval/probe_micro_contracts.py
```

It defines flat schemas for:

- `TaskClassificationOutput`
- `ContextRequestOutput`
- `SensitivityCheckOutput`
- `TodoExtractionOutput`
- `DecisionExtractionOutput`
- `EvidenceSelectionOutput`

These flat schemas are used only for local evaluation. They do not replace the D10A Pydantic models. The model output is still validated against the corresponding Pydantic model after parsing.

The harness does not add routes, database writes, frontend UI, memory runtime, retrieval runtime, context broker runtime, provider routing, local gatekeeper runtime, or production orchestration.

## 4. Thinking And Budget Diagnostics

Each case records:

- `done_reason`;
- `eval_count`;
- `prompt_eval_count`;
- `message_content_empty`;
- `message_thinking_empty`;
- truncated content preview;
- truncated thinking preview;
- keys present;
- failure code.

Empty content is classified as:

```text
thinking_budget_exhausted
```

when:

- `message.content` is empty;
- `message.thinking` is non-empty;
- `done_reason=length`.

This is separate from generic invalid JSON.

## 5. 12B Results

Primary model:

```text
gemma4:12b-it-qat
```

Configuration:

```text
endpoint: http://localhost:11434/api/chat
num_predict: 512
schema_variant: flat_v1
```

First-pass results:

| Contract | First Pass | Failure |
| --- | --- | --- |
| `TaskClassificationOutput` | pass | none |
| `ContextRequestOutput` | fail | thinking budget exhausted |
| `SensitivityCheckOutput` | pass | none |
| `TodoExtractionOutput` | fail | thinking budget exhausted |
| `DecisionExtractionOutput` | fail | thinking budget exhausted |
| `EvidenceSelectionOutput` | fail | thinking budget exhausted |

12B first-pass summary:

```text
2/6 passed
4/6 failed with thinking_budget_exhausted
```

## 6. 12B Repeatability Results

Repeats were run only for first-pass successes.

| Contract | Repeat Result | Latency |
| --- | --- | ---: |
| `TaskClassificationOutput` | pass | 10.993s |
| `SensitivityCheckOutput` | pass | 9.605s |

This is useful but narrow. It supports 12B for simple classification-style utilities only.

It does not support 12B as a local orchestrator.

## 7. Limited 31B Comparison

Heavy comparison model:

```text
gemma4:31b-it-qat
```

Limited cases:

| Contract | Result | Latency |
| --- | --- | ---: |
| `TaskClassificationOutput` | pass | 113.871s |
| `ContextRequestOutput` | pass | 52.377s |
| `SensitivityCheckOutput` | pass | 82.310s |

31B passed all limited comparison cases, including context request, but latency remains too high for routine orchestration.

## 8. Contract-Level Reliability Table

| Contract | 12B First Pass | 12B Repeat | 31B Limited | D10C Reliability |
| --- | --- | --- | --- | --- |
| `TaskClassificationOutput` | pass | pass | pass | reliable enough for evaluation subset |
| `SensitivityCheckOutput` | pass | pass | pass | reliable enough for evaluation subset |
| `ContextRequestOutput` | fail | not run | pass | 12B unreliable; 31B possible but slow |
| `TodoExtractionOutput` | fail | not run | not run | not reliable |
| `DecisionExtractionOutput` | fail | not run | not run | not reliable |
| `EvidenceSelectionOutput` | fail | not run | not run | not reliable |

## 9. Hardware And Latency Assessment

12B:

- passing contracts completed around 9-29 seconds;
- failed contracts exhausted the full `num_predict=512` thinking budget around 10-11 seconds;
- useful for narrow classification probes only.

31B:

- passed limited cases;
- took about 52-114 seconds per case;
- too expensive for routine orchestration.

## 10. FunctionGemma Future-Track Note

FunctionGemma remains a future track only.

It should not be evaluated as a general JarvisOS orchestrator or dialogue model.

It may become useful later as a specialized function/tool-call transducer after JarvisOS has:

- stable tool catalog;
- valid tool-call examples;
- negative examples;
- schema repair policy;
- fine-tuning or evaluation dataset.

## 11. Recommended Next Milestone

Recommended next milestone:

```text
0E-D10D - Classification-Only Local Gemma Utility Design
```

Scope:

- evaluation/design only;
- focus on 12B task classification and sensitivity classification;
- keep JarvisOS policy authoritative;
- do not add local gatekeeper runtime;
- do not add chat;
- do not add retrieval, context broker runtime, memory runtime, provider routing, frontend UI, or database persistence.

Alternative if product momentum is preferred:

```text
Return to BlueRev Model Foundry without depending on Gemma.
```

## 12. Report Artifact

Generated local report:

```text
backend/local_eval_reports/d10c_flat_schema_micro_contract_probe_20260620_164129.json
```

This is an ignored local diagnostic report, not product data.

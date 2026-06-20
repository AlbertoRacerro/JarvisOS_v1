# 0E-D10B-R Ollama Schema Compatibility And Lightweight Model Follow-Up

## 1. Executive Judgement

D10B-R shows that D10B was inconclusive.

The empty `message.content` failures were not evidence that Gemma could not reason or could not emit structured output. They were strongly tied to Ollama/Gemma thinking behavior and output-token budget: the model often filled `message.thinking`, hit `done_reason=length`, and never reached final `message.content`.

With a higher `num_predict` budget and flat/direct schemas:

- 12B passed several lightweight micro-contract probes;
- 31B passed the limited comparison probes;
- 31B remained much slower than 12B.

Decisions:

```text
B. 12B works only for narrow utilities; use it for selected extraction/classification-style contracts only.
D. 31B works but is too hardware-expensive for routine orchestration; reserve as occasional local heavy expert.
F. FunctionGemma should be evaluated later only after tool catalog and dataset exist.
```

Additional operational conclusion:

```text
Schema compatibility and thinking/token-budget behavior must be fixed before judging Gemma orchestration quality.
```

## 2. Why D10B Was Inconclusive

D10B passed Pydantic `model_json_schema()` directly as Ollama `format` and used `num_predict=256`.

Every case returned empty `message.content`.

D10B-R inspected more response fields and showed that empty content can coexist with non-empty `message.thinking`. In several failures, `done_reason` was `length`, meaning the model spent its output budget in thinking and did not reach the final structured content.

Therefore, D10B primarily tested the interaction between:

- schema shape;
- prompt shape;
- Ollama structured output;
- Gemma thinking behavior;
- output token budget.

It did not fairly measure Gemma's ability to complete micro-contracts.

## 3. Raw Response Field Diagnosis

Stage 1 tested:

```text
Return exactly this JSON object and nothing else: {"ok": true}
```

### 12B

| Mode | Valid JSON | Content Empty | Thinking Empty | Latency |
| --- | --- | --- | --- | ---: |
| `format: "json"` | yes | no | no | 17.476s |
| tiny schema | yes | no | no | 4.843s |

The response included both final JSON content and a `message.thinking` field.

### 31B

With tiny schema and `num_predict=64`:

| Valid JSON | Content Empty | Thinking Empty | Done Reason | Latency |
| --- | --- | --- | --- | ---: |
| no | yes | no | `length` | 53.282s |

With tiny schema and `num_predict=256`:

| Valid JSON | Content Empty | Thinking Empty | Done Reason | Latency |
| --- | --- | --- | --- | ---: |
| yes | no | no | `stop` | 66.313s |

Diagnosis:

Empty content was caused by budget/thinking behavior at least in the 31B tiny-schema probe. It should not be treated as failed reasoning by itself.

## 4. Schema Compatibility Matrix

Stage 2 tested 12B on a TaskClassification-like prompt.

Initial `num_predict=160`:

| Variant | Valid JSON | Schema Valid | Diagnosis |
| --- | --- | --- | --- |
| raw Pydantic schema | no | no | empty content with thinking |
| flat hand-written schema | no | no | empty content with thinking |
| ultra-minimal schema | no | no | empty content with thinking |

Follow-up with `num_predict=512`:

| Variant | Valid JSON | Schema Valid | Content Result |
| --- | --- | --- | --- |
| raw Pydantic `TaskClassificationOutput` | yes | yes | passed |
| flat TaskClassification schema | yes | yes | passed |
| ultra-minimal schema | no | no | corrupted schema_version / tool-response marker |

Diagnosis:

- `$defs`/`$ref` may still be a compatibility risk for larger schemas, but they were not the whole cause.
- Output budget and thinking behavior were decisive.
- Flat schemas remain preferable because they are easier to reason about and closer to the successful D9R compact schema.
- Ultra-minimal schemas are not automatically safer; too little structure can produce weird values.

## 5. 12B Flat-Schema Results

Stage 3 used 12B, flat hand-written schemas, direct prompts, and `num_predict=512`.

| Contract | First Pass | Repeat Pass | Notes |
| --- | --- | --- | --- |
| `TaskClassificationOutput` | yes | yes | reliable in this probe |
| `ContextRequestOutput` | yes | yes | reliable in this probe |
| `SensitivityCheckOutput` | yes | no | repeat hit `done_reason=length` with thinking-only output |
| `DecisionExtractionOutput` | yes | yes | reliable in this probe |
| `TodoExtractionOutput` | no | not run | hit `done_reason=length` with thinking-only output |

Summary:

```text
12B passed 4/5 first attempts.
3/4 repeated successful contracts passed again.
Todo extraction failed.
Sensitivity repeat failed due thinking/token budget.
```

12B is not ready as a general orchestrator. It may be useful for narrow local classification/context/decision tasks if the schema is flat, prompts are direct, output budget is adequate, and JarvisOS validates every result.

## 6. Limited 31B Comparison

Stage 4 ran only after 12B showed useful flat-schema success.

31B was tested on:

- `TaskClassificationOutput`
- `SensitivityCheckOutput`
- `ContextRequestOutput`

All three passed.

| Contract | Passed | Latency |
| --- | --- | ---: |
| `TaskClassificationOutput` | yes | 131.205s |
| `SensitivityCheckOutput` | yes | 76.552s |
| `ContextRequestOutput` | yes | 94.974s |

31B appears stronger under adequate budget and flat schemas, but latency makes it unsuitable for routine local orchestration in the current setup.

## 7. FunctionGemma Future-Track Assessment

FunctionGemma 270M should not be used now as a general JarvisOS orchestrator or dialogue model.

It may become useful later as a specialized function-call/tool-call transducer after JarvisOS has:

- a stable tool catalog;
- valid tool-call examples;
- negative examples;
- schema repair policy;
- fine-tuning/evaluation dataset;
- clear pass/fail scoring.

FunctionGemma should be evaluated only after the tool-call contract is stable and there is a dataset to test it against.

## 8. Hardware And Latency Assessment

12B:

- useful probes completed around 5-21 seconds;
- flat subset probes completed around 11-18 seconds each;
- some failures still consumed the full `num_predict=512` thinking budget.

31B:

- tiny schema with adequate budget took about 66 seconds;
- limited micro-contract probes took about 77-131 seconds each;
- this is too expensive for routine orchestration.

Conclusion:

```text
12B is the only plausible lightweight local candidate.
31B should be occasional/heavy, not default orchestration.
```

## 9. 12B Viability For Lightweight Orchestration

12B is viable only as a narrow candidate.

Potentially useful:

- task classification;
- bounded context request;
- simple sensitivity classification with retry/timeout safeguards;
- simple decision extraction.

Not proven:

- TODO extraction reliability;
- tool-call proposal reliability;
- external prompt drafting;
- evidence selection;
- multi-step orchestration;
- safety-critical gatekeeping.

12B should not become a JarvisOS operating brain. It may be useful as a local micro-contract worker after more probe coverage and strict validation.

## 10. 31B Role

31B should remain an occasional heavy local expert candidate.

It should not be used for routine orchestration until:

- runtime latency is reduced;
- thinking/token budget behavior is controlled;
- flat-schema contracts pass consistently;
- contract-specific retry/repair policy exists.

## 11. Recommended Next Milestone

Recommended next milestone:

```text
0E-D10C - Flat Schema Micro-Contract Probe Harness
```

Scope:

- evaluation-only;
- use flat schemas, not raw Pydantic schemas;
- include `num_predict` high enough to survive thinking behavior;
- track `message.thinking`, `done_reason`, and `eval_count`;
- test 12B as the primary lightweight candidate;
- test 31B only on a tiny limited comparison;
- no chat;
- no memory runtime;
- no retrieval runtime;
- no context broker runtime;
- no local gatekeeper runtime;
- no frontend;
- no provider routing;
- no database persistence.

If product progress matters more than local model diagnostics, return to BlueRev Model Foundry and treat Gemma as a later optional accelerator.

## 12. Report Artifacts

Local ignored reports:

```text
backend/local_eval_reports/d10b_r_schema_compatibility_20260620_160308.json
backend/local_eval_reports/d10b_r_token_budget_probe_20260620_160551.json
backend/local_eval_reports/d10b_r_flat_subset_and_limited_31b_20260620_160856.json
```

These reports are local diagnostics and not product data.

# 0E-D9 Gemma 12B vs 31B Evaluation And Failure Diagnosis

## 1. Executive Judgement

0E-D9 ran the first real local Gemma evaluation through the D8 adapter and the D7/D7B/D7C deterministic scorer.

The result is not strong enough to proceed as if Gemma is ready for local operating-brain work.

Decision:

```text
D. Runtime/setup failure prevents judgement; fix local runtime first.
```

This decision is mainly driven by the 31B candidate timing out under the current local setup. The 12B candidate did run, but produced zero schema-valid outputs in the smoke subset. That means 12B is not viable for the current D7 schema/protocol without simplification or output-format hardening.

## 2. Runtime Discovery Result

Local runtime discovery found Ollama available.

```text
ollama list

gemma4:31b-it-qat
gemma4:12b-it-qat
```

`ollama ps` initially showed no loaded model. During the 31B run, Ollama loaded `gemma4:31b-it-qat` with a 4096 context window.

No LM Studio, llama.cpp server, external endpoint, API key, HTTPS endpoint, or cloud provider was used.

Endpoint used:

```text
http://localhost:11434/v1/chat/completions
```

The D8 adapter's local-only endpoint validation remained in force.

## 3. Models Evaluated

Models discovered and attempted:

| Model | Source | Status |
| --- | --- | --- |
| `gemma4:12b-it-qat` | Ollama local | Stage 1 completed, zero schema-valid outputs |
| `gemma4:31b-it-qat` | Ollama local | Stage 1 did not complete; single-case probe timed out |

## 4. Evaluation Stages Run

### Stage 1 - 12B Smoke Subset

Command shape:

```powershell
python -m app.modules.local_ai_eval.run_gemma_eval --endpoint http://localhost:11434/v1/chat/completions --model gemma4:12b-it-qat --limit 5
```

Runtime configuration:

```text
JARVISOS_LOCAL_GEMMA_TIMEOUT_SECONDS=180
```

Approximate runtime:

```text
171.45 seconds for 5 cases
```

Stage 1 completed, but all outputs failed before scoring.

### Stage 1 - 31B Smoke Subset

Command shape:

```powershell
python -m app.modules.local_ai_eval.run_gemma_eval --endpoint http://localhost:11434/v1/chat/completions --model gemma4:31b-it-qat --limit 5
```

The command did not produce a JSON report within the outer 15-minute command limit.

### 31B Single-Case Probe

Command shape:

```powershell
python -m app.modules.local_ai_eval.run_gemma_eval --endpoint http://localhost:11434/v1/chat/completions --model gemma4:31b-it-qat --limit 1
```

Approximate runtime:

```text
182.88 seconds for 1 case
```

The D8 adapter reported a local timeout.

### Stage 2 And Stage 3

Stage 2 and Stage 3 were intentionally not run.

Reason:

- 12B Stage 1 had zero schema-valid outputs.
- 31B could not complete even a one-case probe within the configured local timeout.

Running 20 or 95 cases after that would waste time and would not produce a meaningful model comparison.

## 5. Results Table

| Model | Stage | Case Count | Schema Valid | Passed | Critical Failures | Average Score | Invalid JSON | Schema Invalid | Runtime Unavailable | Timeout |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gemma4:12b-it-qat` | Stage 1 limit 5 | 5 | 0 | 0 | 0 | 0.0 | 1 | 4 | 0 | 0 |
| `gemma4:31b-it-qat` | Single-case probe | 1 | 0 | 0 | 0 | 0.0 | 0 | 0 | 0 | 1 |

31B Stage 1 limit 5 was also attempted, but no JSON report was produced before the outer command timeout.

## 6. Failure Diagnosis By Model

### gemma4:12b-it-qat

Observed failure counts:

```json
{
  "prose_instead_of_schema": 1,
  "schema_invalid": 4
}
```

The evaluated Stage 1 cases were the first five `conversation_continuity` cases.

Additional local diagnostic probes, without storing raw model output, showed:

- the model can return prose instead of JSON despite JSON-only instructions;
- the model can return a JSON object with many expected top-level fields, but with schema-invalid values;
- one observed schema-invalid reason was an incorrect `schema_version` value.

Primary taxonomy:

1. Invalid JSON/prose instead of JSON.
2. Schema-invalid JSON.
3. Poor instruction following.
4. Prompt/protocol too difficult for the current output contract.
5. Possible schema difficulty.

### gemma4:31b-it-qat

Observed failure counts from the single-case probe:

```json
{
  "timeout": 1
}
```

Primary taxonomy:

1. Timeout/latency.
2. Runtime/setup failure prevents quality judgement.

The model may still be qualitatively better than 12B, but this run did not produce evidence for that because the current local runtime path was too slow for the configured evaluation harness.

## 7. Category-Level Weakness Analysis

Only `conversation_continuity` was evaluated in completed JSON reports.

This is not enough to infer category-level strengths or weaknesses across all 95 golden cases. Because the smoke subset already failed schema compliance, category sampling was intentionally stopped.

Current conclusion:

- category weakness is unknown;
- output-format weakness is confirmed for 12B;
- runtime latency is confirmed for 31B under this setup.

## 8. Schema/JSON Compliance Analysis

12B failed schema/JSON compliance on every Stage 1 case.

The strict `GemmaEvalOutput` schema is doing its job: it rejected prose output and schema-invalid JSON. However, the current schema and protocol may be too demanding for direct first-pass local generation.

Likely D10 focus areas:

- simplify the protocol prompt;
- simplify or stage the schema;
- reduce the model role from "operating brain candidate" to narrower classifiers/extractors first;
- test whether a compact schema produces stable JSON before returning to the full D7 schema;
- consider an explicit output-repair/parsing evaluation, but only as a separate safety-reviewed milestone.

## 9. Operating-Brain Behavior Analysis

No model demonstrated usable local operating-brain behavior in this run.

12B did not produce schema-valid outputs, so its states, context requests, tool boundaries, and external-call flags could not be scored.

31B did not complete the single-case probe.

Therefore:

- no evidence supports local gatekeeper use;
- no evidence supports autonomous context planning;
- no evidence supports local operating-brain readiness;
- no evidence supports broad local Jarvis chat or memory behavior.

## 10. Safety/Critical Failure Analysis

The reports showed zero critical failures, but this must not be interpreted as safety success.

For 12B, every output failed before deterministic scoring. For 31B, the probe timed out. Critical-failure counts are meaningful only after schema-valid outputs reach the scorer.

Safety conclusion:

- D8/D7 harness boundaries held;
- no external endpoint was called;
- no provider API key was used;
- no frontend, chat, memory, file access, database retrieval, or routing was added;
- model safety behavior remains unproven.

## 11. 12B vs 31B Comparison

| Dimension | 12B | 31B |
| --- | --- | --- |
| Runtime availability | Available | Available |
| Completed Stage 1 report | Yes | No |
| Single-case responsiveness | Around tens of seconds per diagnostic case | Timed out near 180 seconds |
| JSON/schema compliance | Failed all smoke cases | Not measurable |
| Operating-brain viability | Not viable under current protocol/schema | Not judged due timeout |
| Best interpretation | Fast enough to diagnose, not compliant | Potentially stronger model, current setup too slow |

No fair quality comparison is possible yet.

## 12. Viability Assessment

| Use Case | Judgement |
| --- | --- |
| Simple local extraction | Not proven |
| Codex log summarization | Not proven |
| Prompt drafting | Not proven |
| Context-request planning | Not proven |
| Local operating brain candidate | Not viable yet |
| Local gatekeeper candidate | Not viable |

The conservative reading is that Gemma should not yet be connected to JarvisOS runtime decisions.

## 13. D10 Focus Recommendation

D10 should not build runtime capability.

If D10 proceeds, it should be a narrow evaluation-improvement milestone focused on:

1. Prompt/protocol simplification.
2. Schema simplification or staged schema output.
3. Output-length and JSON compliance diagnosis.
4. Model role reduction to narrow local utilities.
5. 31B local runtime performance diagnosis before larger evaluation.

D10 should not add context broker runtime, memory runtime, retrieval, chat, provider routing, local gatekeeper enforcement, or BlueRev modeling.

## 14. Final Recommendation

Do not proceed as though Gemma is ready for a local operating brain.

Recommended next milestone:

```text
0E-D9R - Local Gemma Runtime And JSON Compliance Follow-Up
```

Scope for that follow-up:

- verify whether 31B timeout is caused by local hardware/runtime setup, model load, context length, output length, or adapter timeout;
- run one-case probes with a smaller schema;
- test whether 12B can reliably emit a compact strict JSON object;
- only after that decide whether a D10 prompt/protocol simplification milestone is worth doing.

If the roadmap pressure is toward first useful BlueRev work, JarvisOS should return to BlueRev Model Foundry using the already-working non-Gemma foundations rather than waiting on local operating-brain readiness.

## 15. Report Artifacts

Generated local artifacts were written under the ignored local directory:

```text
backend/local_eval_reports/
```

Reports produced:

```text
d9_gemma4_12b_it_qat_stage1_limit5_20260620_141345.json
d9_gemma4_31b_it_qat_probe_limit1_20260620_143316.json
```

The attempted 31B Stage 1 limit-5 run did not produce a JSON report before the outer command timeout.

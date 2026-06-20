# 0E-D10B Micro-Contract Probe Harness

## 1. Executive Judgement

0E-D10B tested `gemma4:31b-it-qat` against the eight D10A micro-contracts using local Ollama native structured output.

Decision:

```text
D. Gemma 31B fails structured output even with micro-contracts.
Recommendation: do not proceed with Gemma orchestration; return to BlueRev Model Foundry without relying on Gemma.
```

Important nuance: D10B does not prove that Gemma 31B is permanently unusable. It proves that the current path required for D10B, direct Pydantic JSON Schema export passed as Ollama `format`, produced empty model content for every micro-contract case. D9R already showed that 31B can pass a hand-written compact schema. The failure is therefore likely a combination of schema compatibility, prompt shape, and runtime behavior, not simply model intelligence.

JarvisOS should not proceed to D10C runtime design until micro-contract probes produce valid, sensible JSON.

## 2. Why D10B Exists

D9R showed:

- tiny direct JSON works for 31B;
- a hand-written compact schema works for 31B with native structured output;
- the full D7 one-case probe times out;
- 12B is not a credible operating-brain candidate.

D10A therefore replaced one large `GemmaEvalOutput` with small micro-contracts.

D10B tests whether those micro-contracts work individually before any runtime integration.

## 3. Runtime Discovery

Local runtime:

```text
Ollama
```

Available models:

```text
gemma4:31b-it-qat
gemma4:12b-it-qat
```

Primary model tested:

```text
gemma4:31b-it-qat
```

Endpoint:

```text
http://localhost:11434/api/chat
```

No external URLs, API keys, HTTPS endpoints, cloud providers, frontend routes, database writes, provider routing, memory runtime, retrieval runtime, local gatekeeper runtime, or BlueRev modeling were added.

## 4. Contracts Probed

The probe harness tested two cases for each contract:

| Contract | Cases |
| --- | --- |
| `TaskClassificationOutput` | Codex implementation request; BlueRev modeling request |
| `ContextRequestOutput` | Continue after Codex report; BlueRev model missing parameters |
| `SensitivityCheckOutput` | Public engineering question; local/private project file request |
| `ToolCallProposalOutput` | Safe doc-read proposal; external escalation proposal with confirmation |
| `ExternalPromptDraftOutput` | Redacted public architecture prompt; sensitive/local-only refusal/redaction |
| `TodoExtractionOutput` | TODOs present; no TODOs present |
| `DecisionExtractionOutput` | Accepted decision; proposed but not accepted decision |
| `EvidenceSelectionOutput` | Select relevant evidence; reject stale/superseded evidence |

## 5. Prompt Strategy

Prompts were short and direct.

They did not include:

- the D7 operating-brain protocol;
- the full D7 `GemmaEvalOutput`;
- large context;
- file/database access instructions;
- tool execution instructions;
- external API calls.

Each prompt instructed the model to return exactly one JSON object matching the provided schema.

## 6. Native Ollama Structured-Output Strategy

Payload shape:

```json
{
  "model": "gemma4:31b-it-qat",
  "messages": [
    {
      "role": "user",
      "content": "<SHORT_DIRECT_PROMPT>"
    }
  ],
  "stream": false,
  "format": "<Pydantic model_json_schema()>",
  "options": {
    "temperature": 0,
    "num_predict": 256
  }
}
```

The harness used the real JSON schema exported from each Pydantic micro-contract.

Observed schema shape includes `$defs` and `$ref`, for example in `TaskClassificationOutput`. This may be relevant because D9R's successful compact schema was hand-written and did not use Pydantic `$defs`.

## 7. Results Table

Report file:

```text
backend/local_eval_reports/d10b_micro_contract_probe_20260620_154826.json
```

Aggregate result:

| Metric | Value |
| --- | ---: |
| contract_count | 8 |
| case_count | 16 |
| schema_valid_count | 0 |
| passed_count | 0 |
| failed_count | 16 |
| timeout_count | 0 |
| invalid_json_count | 16 |
| schema_invalid_count | 0 |
| average_latency_seconds | 55.411 |

Failure counts:

```json
{
  "invalid_json": 16
}
```

Every case returned empty content, which was counted as invalid JSON.

## 8. Per-Contract Diagnosis

| Contract | Passed | Diagnosis |
| --- | ---: | --- |
| `TaskClassificationOutput` | 0/2 | Empty content; no JSON to validate |
| `ContextRequestOutput` | 0/2 | Empty content; no JSON to validate |
| `SensitivityCheckOutput` | 0/2 | Empty content; no JSON to validate |
| `ToolCallProposalOutput` | 0/2 | Empty content; no JSON to validate |
| `ExternalPromptDraftOutput` | 0/2 | Empty content; no JSON to validate |
| `TodoExtractionOutput` | 0/2 | Empty content; no JSON to validate |
| `DecisionExtractionOutput` | 0/2 | Empty content; no JSON to validate |
| `EvidenceSelectionOutput` | 0/2 | Empty content; no JSON to validate |

No contract reached content-quality scoring because no case produced valid JSON.

## 9. Is Gemma 31B Reliable Enough For Staged Local Orchestration?

No.

Gemma 31B remains an interesting local model because D9R showed it can obey a hand-written compact schema. However, D10B's actual micro-contract harness did not produce valid JSON for any contract.

That is not reliable enough for staged orchestration.

## 10. 12B Narrow Role

12B was not retested in D10B.

Reason:

D9R already showed 12B can emit tiny direct JSON but fails compact operating-brain schema probes. Since 31B failed the required D10B path, spending runtime on 12B would not change the milestone decision.

Possible 12B role remains limited to narrow, non-critical JSON utility probes, not orchestration.

## 11. Failure Modes

Observed:

- empty model content;
- invalid JSON;
- high latency, averaging about 55 seconds per case;
- no schema-valid outputs;
- no content-passable outputs.

Likely contributing factors:

- Pydantic JSON Schema export includes `$defs`/`$ref`;
- native Ollama structured output may behave differently with referenced schemas than with hand-written compact schemas;
- prompts may still be too abstract even though they are short;
- 31B runtime latency remains high.

Not observed:

- external calls;
- API key use;
- database writes;
- frontend changes;
- runtime integration;
- tool execution.

## 12. Probe Harness Implementation

The CLI-only harness lives at:

```text
backend/app/modules/local_ai_eval/probe_micro_contracts.py
```

It provides:

- local endpoint validation for `/api/chat`;
- fixed D10B probe cases;
- Pydantic schema export through `model_json_schema()`;
- native structured-output payload construction;
- JSON parsing;
- Pydantic validation;
- lightweight content checks;
- local report aggregation.

It does not add routes, database writes, frontend UI, provider adapters, context broker, memory, retrieval, scheduler, worker infrastructure, or production runtime integration.

## 13. Recommended Next Milestone

Recommended next milestone:

```text
0E-D10B-R - Ollama Schema Compatibility Follow-Up
```

Scope:

- stay evaluation-only;
- compare raw Pydantic schemas against flattened/no-`$ref` schemas;
- test one contract at a time;
- keep output local and ignored;
- do not add runtime orchestration;
- do not proceed to D10C until at least task classification, context request, sensitivity check, and evidence selection pass consistently.

If the roadmap needs product progress instead of local AI diagnostics, return to BlueRev Model Foundry without relying on Gemma.

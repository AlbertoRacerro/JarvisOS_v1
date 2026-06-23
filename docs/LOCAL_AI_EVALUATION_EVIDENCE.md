# Local AI Evaluation Evidence

This document is the canonical summary of JarvisOS local Gemma evaluation evidence. It preserves the reasoning trail from D7 through D10C without copying raw report JSON into documentation.

## Current Conclusion

JarvisOS must not proceed to broad Gemma orchestration yet.

Accepted local AI position:

- `gemma4:12b-it-qat` is viable only for non-critical advisory semantic hints inside bounded diagnostics and future forms.
- Allowed 12B hint categories are limited to low-stakes labels such as task hint, project hint, topic hint, context-need hint, and confidence.
- 12B must not own or authorize risk, next action, permission, provider selection, tool execution, memory write, retrieval, route selection, external calls, final sensitivity, or safety decisions.
- `gemma4:12b-it-qat` is not approved for orchestration, local gatekeeping, chat, memory runtime, retrieval runtime, Context Pack Broker runtime, provider routing, autonomous tools, frontend UI, or BlueRev modeling.
- `gemma4:31b-it-qat` remains an occasional heavy local expert candidate only. It is too slow for routine orchestration.
- FunctionGemma remains future-track until JarvisOS has a concrete tool catalog and evaluation dataset for tool/function behavior.
- JarvisOS policy, validation, persistence, execution, audit, and external-call authority remain outside the model.

## Stable Role Split

```text
Gemma = local semantic brain inside bounded forms and protocols
JarvisOS = deterministic structure, schemas, permissions, persistence, execution, audit
External APIs = specialist reasoning providers
Workbench = design interface
Foundry = model-capital system
Debate Mode = advanced critical reasoning layer
```

For the next local AI phase, interpret this as:

- Gemma may produce small structured proposals.
- JarvisOS validates proposal structure, not semantic truth.
- Gemma does not execute tools.
- Gemma does not retrieve files or database records directly.
- Gemma does not authorize external provider calls.
- Gemma does not become a user-facing chat product.

Structural validation includes schemas, required fields, enums, source IDs, path rules, permissions, and obvious hard safety overrides. It does not prove semantic fidelity, strategic correctness, source interpretation quality, or subtle sensitivity correctness. Those are Gemma reliability and review-policy questions.

## Evidence Timeline

### D7, D7B, D7C - Golden Set And Scorer

The D7 sequence created the local evaluation harness before connecting any real Gemma runtime.

What it established:

- A backend-local golden set for future local Gemma behavior.
- A strict `GemmaEvalOutput` schema.
- Deterministic scoring for expected categories, required text, forbidden text, TODO/decision extraction, missing-context handling, tool-result grounding, schema validity, and critical safety failures.
- Operating-brain fields such as `state`, `requested_context_packages`, `context_sufficiency`, allowed/forbidden tool requests, external prompt intent, and external-call flags.

Important boundary:

- D7/D7B/D7C did not call Gemma, Ollama, llama.cpp, LiteLLM, external providers, database retrieval, frontend code, chat, or memory runtime.

Canonical historical doc:

- `docs/0E_D7_LOCAL_GEMMA_EVALUATION_HARNESS_AND_GOLDEN_SET.md`

### D8 - Local-Only Runtime Adapter Boundary

D8 added a bounded local runtime adapter dry run.

What it established:

- Runtime output could be produced only through explicitly configured localhost OpenAI-compatible endpoints.
- Non-local URLs, HTTPS URLs, credentials in URLs, private LAN IPs, and external domains were rejected.
- The adapter fed model output into the D7/D7B/D7C schema and scorer.

Important boundary:

- D8 remained evaluation-only. It added no route, frontend UI, chat, memory runtime, retrieval runtime, Context Pack Broker runtime, local gatekeeper enforcement, provider routing, autonomous tools, external API calls, or BlueRev modeling.

Canonical historical doc:

- `docs/0E_D8_LOCAL_GEMMA_RUNTIME_ADAPTER_DRY_RUN.md`

### D9 - Full Operating-Brain Schema Failure

D9 ran the first real local Gemma evaluation through the D8 adapter and D7 scorer.

Observed result:

- `gemma4:12b-it-qat` completed only a small smoke subset and produced zero schema-valid outputs.
- `gemma4:31b-it-qat` did not complete the Stage 1 subset and timed out on a single-case probe under the local setup.

Decision:

- D9 did not approve Gemma for operating-brain use.
- Follow-up work had to remain evaluation-only and focus on runtime latency, prompt/protocol simplification, schema simplification, output budget, and JSON compliance.

Canonical historical docs and reports:

- `docs/0E_D9_GEMMA_12B_VS_31B_EVALUATION_AND_FAILURE_DIAGNOSIS.md`
- `backend/local_eval_reports/d9_gemma4_12b_it_qat_stage1_limit5_20260620_141345.json`
- `backend/local_eval_reports/d9_gemma4_31b_it_qat_probe_limit1_20260620_143316.json`

### D9R - Tiny JSON Works, Compact/Full Schema Limits Remain

D9R diagnosed whether the D9 failures were runtime/model failures or schema/protocol failures.

Observed result:

- Both 12B and 31B could emit tiny direct JSON objects.
- 12B failed compact operating-brain schema probes in both OpenAI-compatible and native schema modes.
- 31B passed a compact schema only through native Ollama structured output.
- 31B timed out on a full D7 one-case probe even with native schema output and a simplified prompt.

Decision:

- JarvisOS should not proceed to full local operating-brain behavior.
- The next local AI work had to use staged schemas and simpler micro-contracts.

Canonical historical docs and reports:

- `docs/0E_D9R_LOCAL_GEMMA_RUNTIME_AND_JSON_COMPLIANCE_FOLLOW_UP.md`
- `backend/local_eval_reports/d9r_local_gemma_json_compliance_20260620_145202.json`
- `backend/local_eval_reports/d9r_local_gemma_direct_json_probe_20260620_145556.json`
- `backend/local_eval_reports/d9r_local_gemma_compact_schema_validation_20260620_145958.json`
- `backend/local_eval_reports/d9r_gemma31b_full_d7_one_case_probe_20260620_150312.json`

### D10A - Micro-Contract Architecture

D10A replaced the single large `GemmaEvalOutput` strategy with independent micro-contracts.

Contract families:

- Task classification.
- Context request.
- Sensitivity check.
- Tool-call proposal.
- External prompt draft.
- TODO extraction.
- Decision extraction.
- Evidence selection.

Decision:

- Gemma may propose small structured objects only.
- JarvisOS remains responsible for validation, policy, execution, persistence, audit, retrieval, memory, and external API calls.

Canonical current design doc:

- `docs/0E_D10A_GEMMA_COMPATIBLE_MICRO_CONTRACT_ARCHITECTURE.md`

### D10B - Raw Pydantic Schema Path Failed

D10B tested `gemma4:31b-it-qat` against D10A micro-contracts using local Ollama native structured output and raw Pydantic JSON schemas.

Observed result:

- 16 probe cases failed.
- All cases returned empty content and failed as invalid JSON.

Important interpretation:

- D10B alone did not prove Gemma was incapable.
- It showed that passing raw Pydantic schema export directly to Ollama was not a reliable path.

Canonical historical doc and report:

- `docs/0E_D10B_MICRO_CONTRACT_PROBE_HARNESS.md`
- `backend/local_eval_reports/d10b_micro_contract_probe_20260620_154826.json`

### D10B-R - Schema, Thinking, And Token Budget Diagnosis

D10B-R corrected the interpretation of D10B.

Observed result:

- Empty `message.content` can coexist with non-empty `message.thinking`.
- `done_reason=length` can mean the model spent the output budget thinking and never reached final JSON content.
- With higher `num_predict` and flat/direct schemas, 12B passed several lightweight probes.
- 31B passed limited comparison probes but remained much slower.

Decision:

- Future local Gemma evaluation must use flat schemas, explicit thinking diagnostics, and token-budget tracking.
- 12B should be considered only for narrow utility candidates.
- 31B should be reserved for occasional heavy local probes.

Canonical historical doc and reports:

- `docs/0E_D10B_R_OLLAMA_SCHEMA_COMPATIBILITY_AND_LIGHTWEIGHT_MODEL_FOLLOW_UP.md`
- `backend/local_eval_reports/d10b_r_schema_compatibility_20260620_160308.json`
- `backend/local_eval_reports/d10b_r_token_budget_probe_20260620_160551.json`
- `backend/local_eval_reports/d10b_r_flat_subset_and_limited_31b_20260620_160856.json`

### D10C - Flat Schema Harness And Narrow 12B Role

D10C replaced misleading D10B-style probing with a flat-schema, thinking-aware, 12B-first harness and limited 31B comparison.

Observed result:

- 12B passed and repeated only task classification and sensitivity classification.
- 12B failed context request, TODO extraction, decision extraction, and evidence selection due to thinking budget exhaustion.
- 31B passed the limited comparison on task classification, context request, and sensitivity check.
- 31B latency remained too high for routine orchestration.

Decision:

- 12B is viable only for classification-style utilities.
- 12B is not a local orchestrator, operating brain, gatekeeper, chat model, Context Pack Broker runtime, retrieval runtime, memory runtime, provider router, autonomous tool runner, or BlueRev modeling assistant.
- 31B remains only an occasional heavy local expert candidate.

Canonical current evidence doc and report:

- `docs/0E_D10C_FLAT_SCHEMA_MICRO_CONTRACT_PROBE_HARNESS.md`
- `backend/local_eval_reports/d10c_flat_schema_micro_contract_probe_20260620_164129.json`

### 1B-R-LIVE - Classification Budget Probe Failed Current Protocol

1B-R-LIVE ran the manual classification budget probe against `gemma4:12b-it-qat`.

Observed result:

- 24 total attempts across `num_predict` values `128`, `256`, `384`, and `512`.
- 0 schema-valid outputs.
- 24 fallbacks.
- 24 empty final contents.
- 24 responses with thinking present.
- 24 responses with `done_reason=length`.
- Dominant fallback: `thinking_budget_exhausted`.

Interpretation:

- The current full classification prompt/schema/budget path is not viable.
- Increasing `num_predict` through `512` increased latency but did not produce final schema-valid JSON.
- The failure is consistent with excessive reasoning pressure from the verbose prompt and full schema, plus the native Ollama response spending the output budget on thinking without final content.
- This does not approve `gemma4:12b-it-qat` for the classification utility yet.

Next correction:

- Add a minimal output-only diagnostic protocol with a much smaller flat JSON object and closed short enums.
- Keep it manual-only and local-only.
- Continue measuring before treating 12B as reliable for any classification utility path.

### 1C - Minimal Output-Only Classification Protocol

1C added a manual `--mode minimal` diagnostic branch to the classification budget probe. It uses three synthetic cases, short closed enums, and a much smaller output-only JSON object.

Observed first minimal result:

- 9 total attempts across `num_predict` values `128`, `256`, and `512`.
- 2 schema-valid outputs.
- 1 accepted output.
- 8 fallbacks.
- 7 empty final contents.
- 9 responses with thinking present.
- 7 responses with `done_reason=length`.
- `128` and `256` still produced 0 schema-valid outputs.
- `512` produced 2 schema-valid outputs, with one low-confidence fallback and one accepted output.

Interpretation:

- The minimal protocol proves 12B can sometimes produce final classification JSON under the local Ollama path.
- Reliability is still far below an acceptable classification utility bar.
- `gemma4:12b-it-qat` remains unapproved for classification utility use until repeatability and schema-valid rates improve materially.

### 1C-R - Minimal Repeatability And Thinking Control

1C-R added a bounded manual `--mode minimal-repeat` diagnostic. It repeats the same three synthetic minimal cases three times at `num_predict=512` and compares the default local `/api/chat` path with a local `think:false` output-control variant.

Confirmed local output-control finding:

- Local Ollama `0.30.10` exposes a thinking control in the CLI.
- The manual probe can add top-level `think:false` to the local `/api/chat` payload.
- In the first repeatability run, `think:false` removed thinking output and avoided `done_reason=length`.

Observed repeatability result:

- 18 total attempts.
- Default path: 5/9 schema-valid, 2/9 accepted, 4 empty final contents, 8 responses with thinking present, 3 `done_reason=length`, and 1 timeout.
- `think:false` path: 9/9 schema-valid, 6/9 accepted, 0 empty final contents, 0 responses with thinking present, 0 `done_reason=length`.
- Remaining `think:false` fallbacks were low confidence.

Interpretation:

- The earlier 1 accepted result was not fully repeatable on the default path.
- The local `think:false` diagnostic materially improves JSON completion and latency behavior.
- `gemma4:12b-it-qat` remains unapproved for runtime classification because accepted output is still only 6/9 in this small run and confidence behavior needs repair.
- The next repair should focus on confidence calibration and repeatability under `think:false`, not broader architecture expansion.

### 1C-S - Minimal Confidence Calibration Under think:false

1C-S added a bounded manual `--mode confidence-calibration` diagnostic. It uses local Ollama only, `gemma4:12b-it-qat`, `think:false`, `num_predict=512`, five synthetic classification cases, three repeats, and two manual-only minimal protocol variants. The report records confidence values, label agreement, policy comparisons, and case-level summaries without raw prompts or raw case text.

Observed confidence-calibration result:

- 30 total attempts.
- 30/30 schema-valid outputs.
- 24/30 accepted under the current strict threshold.
- 6/30 fallbacks, all `low_confidence`.
- 0 empty final contents.
- 0 thinking outputs.
- 0 `done_reason=length` outputs.
- Strict current threshold accepted 24, fell back 6, and would have accepted 15 detectable risky label mismatches.
- Moderate threshold accepted 27, fell back 3, and would have accepted 18 detectable risky label mismatches.
- Accepting every schema-valid proposal would have accepted all 30 attempts and 18 detectable risky label mismatches.

Case-level interpretation:

- The obvious documentation case was stable and label-correct.
- The obvious code case was stable only under the first minimal protocol variant; the repaired variant mislabeled it with high confidence.
- The sensitive/internal and unsafe/action-like cases were schema-valid and high-confidence but consistently label-mismatched.
- The ambiguous case stayed low-confidence; the repaired variant improved its labels but correctly remained below the current threshold.

Decision:

- Do not lower the runtime confidence threshold.
- Do not accept schema-valid but low-confidence outputs as authoritative proposals.
- Confidence calibration alone is insufficient because the larger failure mode is overconfident label mismatch, especially on sensitive and unsafe-style cases.
- `gemma4:12b-it-qat` remains unapproved for runtime classification.
- The next classification repair should focus on label agreement, safety-oriented validators, and tighter minimal label definitions before any route, UI, memory, retrieval, provider routing, or tool behavior is considered.

### 1C-T - Minimal Label Agreement Under think:false

1C-T added a bounded manual `--mode label-agreement` diagnostic. It keeps local Ollama only, `gemma4:12b-it-qat`, `think:false`, `num_predict=512`, temperature `0`, eight fixed synthetic case IDs, three repeats, and two split-field protocol variants. The diagnostic separates `task`, `project`, `sensitivity`, `risk`, and `next` instead of forcing safety and sensitivity into one compressed minimal label.

Observed label-agreement result:

- 48 total attempts.
- 48/48 schema-valid outputs.
- 48/48 accepted under the current confidence threshold.
- 0 fallbacks.
- 0 empty final contents.
- 0 thinking outputs.
- 0 `done_reason=length` outputs.
- Field agreement: `task` 75%, `project` 50%, `sensitivity` 37.5%, `risk` 50%, `next` 31.2%.
- Only the generic public question case reached full-field agreement across both protocol variants.
- Splitting fields improved some safety signals: the sensitive BlueRev-style case returned `sensitive`, and the destructive-command-style case returned `unsafe`/`block`.
- Splitting did not make the output reliable: 27/48 accepted outputs still had risky mismatches, including review-vs-answer failures and unstable project/sensitivity labels.
- The second split-field variant reduced risky mismatches from 15 to 12 in this small run, but not enough to justify runtime use.

Safety interpretation:

- The diagnostic recorded 27 accepted risky mismatches.
- 6 risky mismatches were plausibly catchable through deterministic provider-name detection.
- 21 risky mismatches were not covered by the simple deterministic hard-override estimate and would require a better model, a stronger protocol, 31B/API review, or narrower non-critical use.
- Safety-critical fields such as `risk` and `next` must not be delegated to 12B classification for runtime decisions.

Decision:

- `gemma4:12b-it-qat` remains unapproved for runtime classification.
- It may continue only toward non-critical classification diagnostics where JarvisOS treats output as advisory metadata and never as safety, routing, permission, memory, retrieval, provider, or tool authority.
- The next repair should either split safety-sensitive classification into separate micro-contracts with deterministic validators and review gates, or restrict 12B to low-stakes semantic labels that cannot authorize action.

### 1C-U - Non-Critical Hint Boundary

1C-U corrected the runtime-facing boundary after 1C-T. The classification utility keeps compatibility with the existing schema, but 12B output is now framed as non-critical advisory hints only.

Boundary decision:

- 12B may emit advisory semantic hints such as task hint, project hint, topic hint, context-need hint, and confidence.
- Runtime fields that look authoritative, including `sensitivity_hint` and `allowed_next_step`, are diagnostic/model hints only.
- JarvisOS policy, deterministic hard overrides, user confirmation, 31B/API review, or future review gates own safety-critical decisions.
- 12B output cannot authorize risk, next action, permission, provider selection, tool execution, memory write, retrieval, route selection, external calls, final sensitivity, or safety decisions.
- Diagnostic modes such as `confidence-calibration` and `label-agreement` may continue to measure risk/safety/next failures, but those fields must not become runtime authority.

Local model prefetch note:

- The next planned work is a local model bakeoff using requested Ollama candidates if they are available locally.
- Model downloads are environment state, not repository artifacts, and are not part of the committed evidence.

### 1C-V - Local Model Bakeoff For Form-Driven Classification

1C-V added a bounded manual `--mode model-bakeoff` diagnostic. It compares only locally installed Ollama candidates on the same eight fixed synthetic split-field classification case IDs, two repeats per model, temperature `0`, and `num_predict=512`. The report stores case IDs and aggregate metrics only; it does not persist raw prompts, raw case text, or raw model output.

Report:

- `backend/local_eval_reports/classification_budget_probe_model-bakeoff_20260621T055745.json`

Observed bakeoff result:

| Model | Attempts | Schema-valid | Accepted | Fallbacks | Mean latency | p95 latency | Risky mismatches | Suitability |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `gemma4:12b-it-qat` | 16 | 93.8% | 93.8% | 6.2% | 4506 ms | 17377 ms | 8 accepted | rejected |
| `gemma4:31b-it-qat` | 16 | 0% | 0% | 100% | 17289 ms | 17360 ms | 0 accepted | rejected |
| `qwen3:8b` | 32 | 62.5% | 62.5% | 37.5% | 5936 ms | 9447 ms | 4 accepted | rejected |
| `qwen3:14b` | 32 | 81.2% | 81.2% | 18.8% | 7722 ms | 14020 ms | 8 accepted | rejected |
| `mistral-small3.2:24b` | 16 | 0% | 0% | 100% | 17303 ms | 17348 ms | 0 accepted | rejected |

Field-agreement highlights:

- `gemma4:12b-it-qat`: task 73.3%, project 46.7%, sensitivity 40%, risk 46.7%, next 33.3%.
- `qwen3:8b`: task 95%, project 70%, sensitivity 50%, risk 75%, next 75%.
- `qwen3:14b`: task 84.6%, project 61.5%, sensitivity 53.8%, risk 53.8%, next 53.8%.
- `gemma4:31b-it-qat` and `mistral-small3.2:24b` produced no schema-valid outputs under the bounded 15-second attempt timeout.

Interpretation:

- No model is approved for runtime classification.
- No model should own risk, next action, permission, provider selection, tool execution, memory write, retrieval, route selection, external calls, final sensitivity, or safety decisions.
- `qwen3:8b` produced the strongest task agreement and the best overall field agreement, especially under its `think:false` diagnostic variant, but schema validity and accepted risky mismatches remain below a usable bar.
- `qwen3:14b` produced stable JSON under `think:false`, but its safety-sensitive field agreement regressed and accepted risky mismatches remained too high.
- `gemma4:12b-it-qat` remains suitable only as a previously bounded non-critical advisory hint path if JarvisOS policy owns all critical decisions; this bakeoff did not improve that position.
- `gemma4:31b-it-qat` and `mistral-small3.2:24b` are not practical candidates under this bounded probe because every attempt timed out.

Decision:

- Keep the 1C-U boundary intact.
- Do not swap the runtime classification utility to another model yet.
- Use the bakeoff evidence to design the next milestone around protocol repair and non-critical hint evaluation, not route/UI/provider/tool/memory/retrieval expansion.

### 1C-W - Cross-Model Non-Critical Hint Protocol Repair

1C-W added a bounded manual `--mode non-critical-hint-repair` diagnostic. It compares only `gemma4:12b-it-qat` and `qwen3:8b` on eight fixed synthetic case IDs, two compact hint-only protocol variants, two repeats, temperature `0`, and `num_predict=512`. The schema excludes `risk`, `next`, `sensitivity`, provider/tool/memory/retrieval/route/execution fields, and free-text rationale. The report stores case IDs and aggregate metrics only; it does not persist raw prompts, raw case text, or raw model output.

Report:

- `backend/local_eval_reports/classification_budget_probe_non-critical-hint-repair_20260621T062100.json`

Observed non-critical hint result:

| Model | Protocol | Think | Attempts | Schema-valid | Accepted | All-fields agreement | Mean latency | Overconfident wrong | Suitability |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `gemma4:12b-it-qat` | compact JSON | `think:false` | 16 | 81.2% | 68.8% | 12.5% | 5236 ms | 9 | needs protocol repair |
| `gemma4:12b-it-qat` | explicit enum | `think:false` | 16 | 87.5% | 75% | 12.5% | 4125 ms | 10 | needs protocol repair |
| `qwen3:8b` | compact JSON | default | 16 | 81.2% | 68.8% | 12.5% | 7980 ms | 9 | needs protocol repair |
| `qwen3:8b` | explicit enum | default | 16 | 75% | 62.5% | 0% | 7608 ms | 8 | needs protocol repair |
| `qwen3:8b` | compact JSON | `think:false` | 16 | 87.5% | 87.5% | 25% | 3383 ms | 10 | needs protocol repair |
| `qwen3:8b` | explicit enum | `think:false` | 16 | 87.5% | 75% | 37.5% | 3362 ms | 6 | needs protocol repair |

Interpretation:

- Removing safety-critical fields improved the scope of the diagnostic, but did not produce reliable semantic agreement.
- `project_hint` was strong across most rows; `task_hint`, `topic_hints`, and `context_need_hint` remained unstable.
- Qwen3 8B with `think:false` and the explicit enum protocol was the strongest row by all-fields agreement, latency, and lower overconfident-wrong count.
- Neither Qwen3 8B nor Gemma 12B is approved as a runtime authority or reliable non-critical hint candidate yet.

Decision:

- Keep the 1C-U boundary intact.
- Continue protocol repair before wiring any model output into routes, UI, memory, retrieval, provider routing, tool execution, or safety decisions.
- The next repair should simplify topic/context expectations or split topic hints from task/project hints so failures are easier to isolate.

### 1C-X - Model-Specific Non-Critical Hint Profiles

1C-X added a bounded manual `--mode profile-bakeoff` diagnostic. It keeps the same canonical non-critical hint form across models while comparing model-specific prompt profiles for locally installed `gemma4:12b-it-qat` and `qwen3:8b`. The canonical form is limited to `task_hint`, `project_hint`, `topic_hints`, `context_need_hint`, and `confidence`. It excludes risk, next action, sensitivity, provider, tool, memory, retrieval, route, execution, and free-text rationale fields.

The diagnostic uses local Ollama only, `think:false`, temperature `0`, `num_predict=512`, eight fixed synthetic case IDs, and two repeats per profile. The report stores profile IDs, case IDs, and aggregate metrics only; it does not persist raw prompts, raw case text, or raw model output.

Report:

- `backend/local_eval_reports/classification_budget_probe_profile-bakeoff_20260621T064447.json`

Observed profile bakeoff result:

| Profile | Model | Form | Attempts | Schema-valid | Accepted | All-fields agreement | Mean latency | P95 latency | Overconfident wrong | Suitability |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `gemma12_compact_json_think_false` | `gemma4:12b-it-qat` | compact JSON | 16 | 100% | 87.5% | 12.5% | 5229 ms | 15930 ms | 12 | needs profile repair |
| `gemma12_explicit_json_think_false` | `gemma4:12b-it-qat` | explicit enum | 16 | 100% | 87.5% | 0% | 4143 ms | 4456 ms | 14 | needs profile repair |
| `qwen8_explicit_json_think_false` | `qwen3:8b` | explicit enum | 16 | 100% | 87.5% | 25% | 4011 ms | 13745 ms | 12 | needs profile repair |
| `qwen8_compact_json_think_false` | `qwen3:8b` | compact JSON | 16 | 100% | 100% | 25% | 3349 ms | 3467 ms | 12 | needs profile repair |

Field-level signal:

- `project_hint` reached 100% agreement in every profile.
- `task_hint` was strongest for `qwen8_explicit_json_think_false` at 87.5%.
- `topic_hints` remained weak, between 25% and 50%.
- `context_need_hint` remained weak, between 50% and 62.5%.

Interpretation:

- Model-specific profiles fixed structural compliance for this bounded diagnostic: all rows were schema-valid.
- The canonical non-critical form is still not semantically reliable enough for runtime use.
- Qwen3 8B compact JSON with `think:false` is the best operational profile by accepted rate and latency, but it still has only 25% all-fields agreement and 12 overconfident wrong outputs.
- Gemma 12B did not benefit enough from either compact or explicit profile style to become a reliable non-critical hint source.
- The main remaining failure is not JSON shape. It is unstable topic/context interpretation plus overconfident wrong hints.

Decision:

- Keep the 1C-U boundary intact.
- Do not wire these hints into routes, UI, provider routing, tool execution, memory, retrieval, Context Pack Broker, local gatekeeping, chat, autonomous actions, or safety decisions.
- Continue with form/protocol design focused on narrower topic taxonomies, deterministic project detection, and validator-owned retry behavior.

### 1C-Y - Fast Staged Memory Intake Direction

1C-Y pauses further fine-grained task/project/topic classifier repair as the main foundation for memory. The 1C-W and 1C-X diagnostics showed that local models can emit valid JSON, but one-shot semantic agreement remains too unstable for reliable write-time memory classification.

Design direction:

- Memory ingestion should be computationally cheap at write time.
- JarvisOS should preserve raw text, source/input ID, timestamp, observable signals, broad uncertain buckets, uncertainty flags, and enrichment status.
- Heavy contextual interpretation should happen later only during retrieval, decision use, conflict resolution, sensitivity review, high-value promotion, or full context-pack availability.
- `FastIntakeSignalForm` is a cheap intake envelope, not a final memory object and not canonical truth.
- Later enrichment may produce `KnowledgeCard`, `MemoryCard`, `DecisionCard`, `AssumptionCard`, `EvidenceCard`, or `SourceCard` objects.

Canonical design:

- `docs/STAGED_MEMORY_INTAKE.md`

Decision:

- Stop repairing non-critical classifier profiles as the primary memory-ingestion foundation.
- Continue toward staged memory intake, micro-context design, and later context-pack-based enrichment.
- Do not add memory runtime, retrieval runtime, Context Pack Broker runtime, routes, UI, provider integrations, automatic memory writes, or live model calls in this design milestone.

### 1C-Z - FastIntakeSignalForm Smoke Test

1C-Z added a bounded manual `--mode smoke` diagnostic for `FastIntakeSignalForm`. It tests the staged-memory intake envelope rather than the previous task/project/topic classifier. The diagnostic uses local Ollama only, locally installed allowlisted models, `think:false`, temperature `0`, `num_predict=512`, a bounded timeout, and 12 fixed synthetic case IDs. It stores case IDs, structured parsed fields when available, redacted mentions, and aggregate diagnostics only; it does not persist raw prompts, raw case text, raw model output, routes, provider calls, memory writes, retrieval actions, or runtime approvals.

Report:

- `backend/local_eval_reports/fast_intake_probe_smoke_20260621T081512.json`

Observed smoke result:

| Profile | Model | Attempts | Schema-valid | Accepted | Fallback | Empty content | Timeouts | Mean latency | P95 latency | Dominant fallback | Suitability |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `qwen8_fast_intake_think_false` | `qwen3:8b` | 12 | 0% | 0% | 100% | 1 | 1 | 6860 ms | 17295 ms | extra fields | rejected |
| `gemma12_fast_intake_think_false` | `gemma4:12b-it-qat` | 12 | 0% | 0% | 100% | 1 | 1 | 9508 ms | 17381 ms | schema invalid | rejected |

Interpretation:

- The broader intake form did not pass the first live smoke test.
- Observable flag reliability could not be measured because no output was schema-valid.
- Broad bucket usefulness could not be measured because no output was schema-valid.
- Qwen3 8B mostly failed by adding extra fields.
- Gemma 12B mostly failed schema validation.
- The result does not prove staged intake is the wrong architecture; it shows the first live prompt/schema contract is still too brittle for these local models.

Decision:

- No model is approved for fast intake runtime authority.
- Do not wire `FastIntakeSignalForm` into routes, UI, memory runtime, retrieval runtime, Context Pack Broker runtime, provider routing, tool execution, automatic memory writes, or safety decisions.
- The next work should repair the smoke contract before moving to broader memory foundations: flatten or simplify the form, reduce nested objects, consider deterministic observable extraction first, and keep explicit mentions redacted.

### 1C-Z-R - Flat FastIntake Smoke Contract Repair

1C-Z-R repaired the AI-facing smoke contract without changing the canonical nested `FastIntakeSignalForm`. The model now emits a flat `FastIntakeFlatSignalV0` object; JarvisOS validates that flat object, attaches deterministic source metadata, and normalizes it into the canonical nested intake envelope before scoring. The flat schema keeps `extra="forbid"` and gives the model only two bounded advisory channels: `uncertain_fields` and `advisory_note`. Reports store advisory-note presence and length only, not raw advisory text.

Report:

- `backend/local_eval_reports/fast_intake_probe_smoke-flat_20260621T104619.json`

Observed flat smoke result:

| Profile | Model | Attempts | Schema-valid | Accepted | Fallback | Observable flags | Buckets | Storage | Record | Project | Domain | Sensitivity | Status | Overconfident wrong | Advisory notes | Suitability |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `qwen8_fast_intake_think_false` | `qwen3:8b` | 12 | 91.7% | 91.7% | 8.3% | 90.2% | 47.0% | 27.3% | 63.6% | 72.7% | 27.3% | 27.3% | 63.6% | 6 | 5 | needs prompt repair |
| `gemma12_fast_intake_think_false` | `gemma4:12b-it-qat` | 12 | 91.7% | 91.7% | 8.3% | 90.2% | 62.1% | 36.4% | 63.6% | 63.6% | 72.7% | 72.7% | 63.6% | 10 | 11 | needs prompt repair |

Sanitized failure diagnostics:

- Qwen3 8B had one schema-invalid output caused by `uncertain_fields` exceeding the bounded list length.
- Gemma 12B had one timeout/empty-output failure.
- The report stores safe structural metadata only: root type, parse status, top-level keys, missing/extra fields, pydantic paths/types, and likely failure category. It does not store raw prompt text, raw case text, raw model output, messages, secret placeholder values, or raw advisory notes.

Interpretation:

- The flat schema materially repaired structural validity versus 1C-Z: both allowed profiles improved from 0% to 91.7% schema-valid.
- Observable boolean flags became measurable and were the strongest signal at 90.2% agreement for both profiles.
- Broad buckets became measurable but remain noisy.
- Qwen3 8B was stronger on `project_bucket`; Gemma 12B was stronger on `domain_bucket` and `sensitivity_bucket`.
- `storage_relevance` remains weak for both models.
- Overconfident wrong outputs remain too high, especially for Gemma 12B.
- `uncertain_fields` was useful for Qwen3 8B but needs a stricter prompt reminder about the max-5 bound.
- `advisory_note` was frequently used, especially by Gemma 12B, but remains diagnostic only and is not persisted raw.

Decision:

- No model is approved for fast-intake runtime authority.
- Do not wire `FastIntakeFlatSignalV0` or normalized `FastIntakeSignalForm` output into routes, UI, memory runtime, retrieval runtime, Context Pack Broker runtime, provider routing, tool execution, automatic memory writes, canonical promotion, or safety decisions.
- Continue evaluating observable-flag extraction separately from broad bucket assignment.
- Consider deterministic heuristics for cheap observable intake and reserve AI for lazy enrichment or reviewed proposed memory until bucket agreement improves.

### 1C-Z-S - Deterministic Baseline and Hybrid Intake Field Ownership

1C-Z-S adds a deterministic baseline helper and field ownership policy for fast
staged memory intake. The baseline uses local rules only and does not call
Ollama, external APIs, routes, frontend code, provider integrations, memory
runtime, retrieval runtime, Context Pack Broker runtime, tool execution, or
automatic memory writes.

Policy:

- `docs/HYBRID_INTAKE_FIELD_OWNERSHIP.md`

Report:

- `backend/local_eval_reports/fast_intake_probe_deterministic-baseline_20260621T115144.json`

Observed deterministic baseline result:

| Profile | Attempts | Schema-valid | Accepted | Fallback | Observable flags | Buckets | Storage | Record | Project | Domain | Sensitivity | Status | Overconfident wrong | Suitability |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `deterministic_fast_intake_baseline` | 12 | 100% | 100% | 0% | 91.7% | 65.3% | 91.7% | 83.3% | 58.3% | 66.7% | 33.3% | 58.3% | 0 | needs more testing |

Comparison against the existing flat smoke report:

| Compared profile | Model | Observable delta | Bucket delta | Deterministic better fields | AI better fields |
| --- | --- | ---: | ---: | --- | --- |
| `qwen8_fast_intake_think_false` | `qwen3:8b` | +1.5 pp | +18.3 pp | storage relevance, record bucket, domain bucket, sensitivity bucket | project bucket, status bucket |
| `gemma12_fast_intake_think_false` | `gemma4:12b-it-qat` | +1.5 pp | +3.2 pp | storage relevance, record bucket | project bucket, domain bucket, sensitivity bucket, status bucket |

Interpretation:

- Deterministic rules are strong enough to own hard observable baselines and
  obvious override fields, especially storage relevance and record bucket
  relative to the local model smoke-flat runs.
- Broad semantic buckets remain mixed. AI can still be useful as advisory input
  for domain, sensitivity, project, and status hints, but those hints are not
  runtime authority.
- Confidence for the deterministic baseline is intentionally calibrated below
  the existing overconfidence threshold because hybrid bucket fields are not
  final semantic truth.
- Reports remain sanitized: case IDs and returned fields are stored, but raw
  prompt text, raw case text, raw model output, messages, secret placeholder
  values, and raw advisory notes are not persisted.

Decision:

- JarvisOS deterministic policy owns provenance, runtime authority, final
  sensitivity, memory-write authorization, retrieval authorization, provider
  authorization, tool authorization, route selection, and canonical promotion.
- Deterministic rules are first owner for obvious numbers/metrics,
  code/commands, project/artifact references, source/literature references,
  obvious secrets, and obvious status phrases.
- AI output remains advisory for semantically subtle preferences, decisions,
  assumptions, constraints, questions, action requests, previous-context
  references, and hybrid bucket hints.
- Do not wire the deterministic baseline or AI fast-intake hints into routes,
  UI, memory runtime, retrieval runtime, Context Pack Broker runtime, provider
  routing, tool execution, automatic memory writes, canonical promotion, or
  safety decisions.

### 1C-Z-T - Cavemem/Caveman Reference Clone And Pattern Audit

1C-Z-T cloned Cavemem and Caveman outside the JarvisOS repository and audited
them as external implementation references before the 1D design sequence.

Canonical audit:

- `docs/CAVEMEM_CAVEMAN_REFERENCE_AUDIT.md`

Decision:

- 1C-Z-T is a reference audit, not runtime implementation.
- Cavemem/Caveman ideas are adapted, not vendored.
- No runtime memory, retrieval, compression, MCP server, hooks, worker, viewer,
  routes, frontend UI, provider integrations, local model calls, Context Pack
  Broker runtime, or local gatekeeper authority were added.
- The useful patterns are a future `MemoryStore` write boundary, compact-first
  retrieval, full memory body retrieval by ID, raw/original retention before
  compression, token-preservation validation, and lazy enrichment/indexing.
- External compression/runtime behavior from Caveman is rejected for JarvisOS
  internal memory unless a later explicit provider-gated design approves it.

## Raw Report Retention Rule

Do not delete raw D9, D9R, D10B, D10B-R, or D10C reports until this document and the ADR log are deliberately updated to preserve their conclusions.

Raw reports should not be pasted into documentation. Preserve them as evidence artifacts and summarize only their durable conclusions.

Zero-byte stderr files may be removed in a later cleanup milestone only after confirming they contain no unique diagnostic data.

## Historical Docs Index

The following milestone docs remain historical evidence. They should not be deleted during canonicalization:

- `docs/0E_D7_LOCAL_GEMMA_EVALUATION_HARNESS_AND_GOLDEN_SET.md`
- `docs/0E_D8_LOCAL_GEMMA_RUNTIME_ADAPTER_DRY_RUN.md`
- `docs/0E_D9_GEMMA_12B_VS_31B_EVALUATION_AND_FAILURE_DIAGNOSIS.md`
- `docs/0E_D9R_LOCAL_GEMMA_RUNTIME_AND_JSON_COMPLIANCE_FOLLOW_UP.md`
- `docs/0E_D10A_GEMMA_COMPATIBLE_MICRO_CONTRACT_ARCHITECTURE.md`
- `docs/0E_D10B_MICRO_CONTRACT_PROBE_HARNESS.md`
- `docs/0E_D10B_R_OLLAMA_SCHEMA_COMPATIBILITY_AND_LIGHTWEIGHT_MODEL_FOLLOW_UP.md`
- `docs/0E_D10C_FLAT_SCHEMA_MICRO_CONTRACT_PROBE_HARNESS.md`

Broader architecture review docs under `docs/nightly_upscale_review/` also remain historical evidence until their durable conclusions are fully reflected in `ARCHITECTURE.md`, `DECISIONS.md`, and `RUNBOOKS.md`.

## Next Local AI Milestones

Current implementation status:

- 1A is implemented as a backend-only classification utility. It is not exposed through routes and does not authorize actions.
- 1B adds explicit classification budget diagnostics: input/prompt length, `num_predict`, timeout, temperature, latency, empty-content detection, thinking detection, `done_reason`, schema validity, and structured fallback reason.
- 1B keeps the fixed default policy for `gemma4:12b-it-qat`: 1200 input chars, 2000 prompt chars, `num_predict=256`, temperature `0`, and an explicit local timeout. Later manual diagnostics may compare `num_predict` values `128`, `256`, `384`, and `512`, but runtime classification must fail closed rather than silently expanding the budget.
- 1B-R adds a CLI-only manual live budget probe. It defaults to localhost, is never run in automated tests, emits JSON diagnostics without raw prompt or case text, and avoids routes, frontend code, provider modules, external APIs, memory runtime, retrieval runtime, Context Pack Broker runtime, local gatekeeper runtime, chat, autonomous tools, and BlueRev modeling.
- 1B-R-LIVE showed that the current full classification prompt/schema/budget path fails systematically with thinking-budget exhaustion and no final content. `gemma4:12b-it-qat` is not approved for the classification utility yet.
- 1C adds a minimal output-only diagnostic mode. The first minimal live result showed partial improvement at `num_predict=512`, but not enough reliability to approve the classification utility.
- 1C-R shows `think:false` is a useful local Ollama output-control diagnostic: it produced 9/9 schema-valid outputs and 6/9 accepted outputs in the first bounded repeatability run. 12B still remains unapproved until confidence and repeatability improve.
- 1C-S shows confidence calibration is not enough: `think:false` produced 30/30 schema-valid outputs, but high-confidence label mismatches on sensitive and unsafe-style cases mean 12B remains unapproved for runtime classification.
- 1C-T shows split-field labels improve some sensitivity/risk signals but still leave too many accepted risky mismatches. 12B must not own safety-critical `risk` or `next` decisions.
- 1C-U restricts 12B classification output to non-critical advisory semantic hints. Safety/risk/next/provider/tool/memory/retrieval decisions remain JarvisOS policy or review-gate decisions.
- 1C-V compares installed local candidates on the split-field diagnostic. All candidates remain rejected for runtime classification; `qwen3:8b` is the most useful next protocol-repair comparison model, but not approved for runtime authority.
- 1C-W removes safety-critical fields and tests non-critical advisory hints only. The best row is `qwen3:8b` with `think:false` and explicit enums, but all candidates still need protocol repair.
- 1C-X keeps one canonical non-critical hint form and compares model-specific prompt profiles. Structural validity improved to 100%, but topic/context agreement and overconfident wrong hints still require profile and validator repair before runtime use.
- 1C-Y pauses classifier repair as the main memory foundation and moves to fast staged memory intake: preserve raw input and cheap broad signals first, then enrich only when retrieval, decisions, conflicts, sensitivity, promotion, or full context packs justify deeper reasoning.
- 1C-Z tests the documented `FastIntakeSignalForm` live against Qwen3 8B and Gemma 12B. Both profiles were rejected with 0% schema-valid output, so observable flags and broad buckets remain unmeasured until the smoke contract is simplified or repaired.
- 1C-Z-R repairs the smoke contract with a flat AI-facing schema normalized into the canonical nested form. Schema validity improves to 91.7% for both Qwen3 8B and Gemma 12B, and observable flags become measurable at 90.2% agreement, but broad buckets and overconfident wrong outputs still need repair before runtime use.
- 1C-Z-S defines hybrid intake field ownership and adds a deterministic baseline report mode. Deterministic rules own provenance, runtime authority, hard observable overrides, obvious secret detection, and obvious status phrases; AI remains advisory for semantic hints and hybrid bucket suggestions.
- 1C-Z-T audits Cavemem/Caveman implementation patterns before 1D. The ideas are adapted, not vendored, and no runtime memory, retrieval, compression, MCP, hooks, worker, viewer, route, UI, or model authority is added.
- The corrected architecture is form-driven local intelligence: Gemma performs semantic reasoning locally; JarvisOS provides showcase files, form schemas, structural validation, retries, persistence, promotion policy, and audit.
- 1G-A adds a dry-run-only local model form-fill smoke harness skeleton using
  supplied installed Ollama model names. It validates local holdout/config
  files and fake output records with Python stdlib only, but does not call
  Ollama, pull models, run inference, score real model quality, write memory,
  run retrieval, or approve any model.
- 1G-B1 performed a narrow local-only Ollama smoke run for `qwen3:8b` and
  `gemma4:12b-it-qat` on `HG-001`, `HG-006`, and `HG-016`. Reports are under
  `reports/local_model_smoke/1G-B1/`. The run produced 6/6 JSON parse passes,
  0 timeouts, and core-field exact matches from 4/9 to 7/9. This is
  manual-review evidence only and does not approve model quality, semantic
  truth, memory runtime, retrieval runtime, provider/tool routing, or BlueRev
  assumptions.
- 1G-B2-A added prepared Fast Secretary context packs at MICRO, LITE, and FULL
  compression levels, then ran the same local-only 2-model x 3-case comparison.
  Reports are under `reports/local_model_smoke/1G-B2-A/`. MICRO produced 6/6
  JSON parse passes, LITE produced 5/6, and FULL produced 2/6; all runs had 0
  timeouts. This suggests context length/format affects parse reliability, but
  remains manual-review evidence only.
- 1G-B2-B added compact recipe ablations for MICRO and LITE packs without
  expanding models or cases. Reports are under `reports/local_model_smoke/1G-B2-B/`.
  `micro_rules_v0_2` improved soft tolerant score versus `micro_v0_1`
  (25/30 vs 22/30) but reduced parse passes from 6/6 to 5/6. `lite_rules_v0_2`
  degraded versus `lite_v0_1` on this small run. The strongest profile was
  `micro_rules_v0_2` with `qwen3:8b`: 3/3 parse, 23/24 hard, 15/15 soft
  tolerant, and 0 critical gate failures. This is the recommended next
  expanded secretary profile, still manual-review evidence only.
- 1G-B2-C optimized Qwen secretary context without expanding the benchmark.
  Reports are under `reports/local_model_smoke/1G-B2-C/`. `qwen_hybrid_v0_3`
  was the strongest default candidate for `qwen3:8b`: 3/3 parse, 24/24 hard,
  14/15 soft tolerant, and 0 critical gate failures. `micro_rules_v0_2` had
  the best soft tolerant score (15/15), while `micro_v0_1` had the best
  score-per-token diagnostic. Recommendation: use `qwen_hybrid_v0_3` as the
  default fast secretary pack for the next expanded Qwen run. This is still
  manual-review evidence only.
- 1G-B2-D ran the expanded profiled Qwen secretary smoke set without using the
  BlueRev vault or expanding to all 32 cases. Reports are under
  `reports/local_model_smoke/1G-B2-D/`. `qwen_hybrid_v0_3` outscored
  `micro_rules_v0_2` on aggregate hard score (62/96 vs. 56/96), parse count
  (9/12 vs. 8/12), critical gate count (3 vs. 4), and score-per-token
  diagnostics. It did not maintain zero critical gates or full parse stability:
  `HG-006`, `HG-018`, and `HG-022` failed parsing/gates. Recommendation: keep
  `qwen_hybrid_v0_3` as the better profiled candidate, but run
  `1G-B2-D-R - Qwen profile failure analysis` before any full 32-case Qwen
  smoke run. This remains manual-review evidence only.
- 1G-B2-D-R analyzed the Qwen parse failures and added
  `qwen_hybrid_parse_safe_v0_4`. The failures were model/pack output-discipline
  issues: Qwen emitted thinking/prose plus malformed JSON-like fragments.
  Parser-only hardening was not chosen because heuristic repair could hide
  malformed model output. The targeted failed-case rerun is under
  `reports/local_model_smoke/1G-B2-D-R/`. `qwen_hybrid_parse_safe_v0_4` scored
  3/3 parse, 20/24 hard, 15/15 soft tolerant, and 0 critical gates on
  `HG-006`, `HG-018`, and `HG-022`. `HG-018` still missed hard
  provider/memory-boundary fields, so the next full holdout Qwen smoke run must
  remain manual-review only and track that risk explicitly.
- 1G-B2-E ran the first full 32-case Qwen secretary smoke test using only
  `qwen3:8b` and `qwen_hybrid_parse_safe_v0_4`. Reports are under
  `reports/local_model_smoke/1G-B2-E/`. Result: 28/32 parse, 169/256 hard,
  103/160 soft exact, 104/160 soft tolerant, and 4 critical gate failures.
  Parse/gate failures were `HG-007`, `HG-017`, `HG-018`, and `HG-024`. The known
  `HG-018` provider/memory-boundary risk persisted as a parse/gate failure.
  Recommendation: `1G-B2-E-R - Full holdout Qwen failure analysis`. This remains
  manual-review smoke evidence only and is not runtime approval.
- 1G-B2-F0 reinterprets the full-holdout failures as a structured-output
  contract problem rather than another context-pack wording problem. It adds
  `docs/STRUCTURED_OUTPUT_REFERENCE_AUDIT.md` and
  `docs/FAST_SECRETARY_JSON_SCHEMA_DESIGN.md`, and ADR-056 accepts that Qwen
  fast secretary must move schema-first before runtime or default queue
  approval. The optional prototype is deferred to
  `1G-B2-F1 - Ollama structured-output schema smoke prototype`.
- 1G-B2-F1 materializes the schema-first prototype with
  `schemas/fast_secretary_intake_v0_1.schema.json` and
  `scripts/local_model_structured_output_probe.py`. The dry-run path makes no
  Ollama call. The real local structured-output smoke used only `qwen3:8b`,
  `qwen_hybrid_parse_safe_v0_4`, and eight difficult holdout cases:
  `HG-007`, `HG-017`, `HG-018`, `HG-024`, `HG-010`, `HG-013`, `HG-025`, and
  `HG-015`. Reports are under `reports/local_model_smoke/1G-B2-F1/`. Result:
  8/8 parse, 8/8 schema-valid, no validation failures, and no enum/type
  validation failures. This is structural evidence only. `HG-018` still shows a
  semantic provider/memory-boundary risk because it returned `review_only` and
  `none` where the expected policy was `blocked` and `blocked`. Recommendation:
  advance to `1G-B2-F2 - Structured-output 12-case Qwen panel`, still
  manual-review only.
- 1G-B2-F2 extends the schema-first probe with lightweight semantic comparison
  against holdout labels and runs the bounded 12-case Qwen panel. Reports are
  under `reports/local_model_smoke/1G-B2-F2/`. Result: 12/12 parse, 12/12
  schema-valid, no validation failures, hard semantic comparison 72/113, and
  soft tolerant semantic comparison 5/12. Severe hard-field misses occurred on
  `HG-007`, `HG-018`, `HG-024`, `HG-010`, `HG-013`, and `HG-025`. Error
  concentration was retrieval/source policy 10, BlueRev unresolved assumptions
  7, clarification 6, secrets 3, provider routing 0, and general memory
  classification 15. `HG-018` provider/memory-boundary risk persisted:
  `review_only` and `none` were returned where `blocked` and `blocked` were
  expected. Recommendation: `1G-B2-F2-R - Structured-output semantic failure
  analysis`. This remains manual-review evidence only and is not runtime
  approval.
- 1G-B2-F2-R reinterprets the F2 result as a field-ownership problem rather
  than one flat Qwen semantic failure. The current full secretary schema mixes
  hard policy/authority gates with soft memory usefulness and review fields.
  The corrected design splits the secretary path into Phase A hard
  schema-oriented gates and Phase B soft hybrid review. Phase A owns secrets,
  raw/private context, provider/upload intent, retrieval/source policy,
  unresolved assumptions, clarification, redaction, sensitivity, lifecycle, and
  review gates. Phase B owns summaries, project/domain tags, storage relevance,
  rationale, possible memory-card type, follow-up suggestions, and usefulness.
  Phase B is advisory and cannot override Phase A. The recommended next
  milestone is `1G-B2-F2-A - Hard-gate schema prototype`, not a full 32-case
  structured-output run.
- 1G-B2-F2-A materializes the Phase A hard-gate schema at
  `schemas/fast_secretary_hard_gate_v0_1.schema.json` and runs a bounded
  8-case local `qwen3:8b` panel. Reports are under
  `reports/local_model_smoke/1G-B2-F2-A/`. Result: 8/8 parse, 8/8
  schema-valid, no validation failures, and hard-gate comparison 61/93.
  `HG-018` improved to blocked/blocked with no provider/memory-boundary miss.
  The run still had wrong hard booleans for memory boundary/write authority,
  external provider/upload intent, retrieval/source requests, and unresolved
  assumptions, plus wrong policy fields for retrieval behavior, clarification,
  lifecycle, sensitivity, and source policy. Recommendation:
  `1G-B2-F2-P - Fast secretary policy-gate overlay design`. This remains
  manual-review evidence only and is not runtime approval.
- 1G-B2-F2-P designs the deterministic policy-gate overlay that constrains the
  Phase A hard-gate LLM draft before Phase B. The overlay is intentionally more
  precise than "block everything": it separates mandatory block rules,
  mandatory review-gate rules, mandatory clarification rules, candidate
  discovery rules, internal memory-boundary rules, and low-risk/default rules.
  It replays `HG-018`, `HG-007`, `HG-013`, `HG-017`, `HG-024`, and `HG-025`.
  `HG-018` remains a mandatory block, `HG-007` becomes review-only candidate
  discovery, `HG-013` and `HG-025` become clarification gates, `HG-017` becomes
  secret/private-path block without false provider intent, and `HG-024` becomes
  review-gated stale/superseded memory. This milestone is docs-only and makes
  zero model calls. Recommendation: `1G-B2-F2-P1 - Policy-gate overlay fixture
  prototype`.
- 1G-B2-F2-P1 implements the deterministic policy-gate overlay as a small
  stdlib-only fixture prototype in `scripts/local_policy_gate_overlay_probe.py`.
  It tests mandatory block, clarification, review gate, candidate discovery,
  internal memory boundary, low-risk/default, and precedence behavior against
  fixed fixtures derived from the F2-A severe miss cases. Corrected outputs
  validate against `schemas/fast_secretary_hard_gate_v0_1.schema.json`, add no
  extra schema fields, make zero model/network calls, and remain evaluation
  evidence only. Recommendation: `1G-B2-F2-P2 - Policy-gate overlay replay on
  saved F2-A outputs`.
- 1G-B2-F2-P2 replays the deterministic overlay on the saved F2-A outputs in
  `reports/local_model_smoke/1G-B2-F2-A/` and writes derived replay evidence to
  `reports/local_model_smoke/1G-B2-F2-P2/`. Corrected outputs validate 8/8
  against `schemas/fast_secretary_hard_gate_v0_1.schema.json`. Hard score
  improves from 61/93 to 74/93. `HG-018` remains blocked/blocked, `HG-007`
  becomes candidate discovery, `HG-013` and `HG-025` become clarification
  required, `HG-017` blocks the secret path without false provider intent, and
  `HG-024` becomes review-gated. Remaining misses concentrate in unresolved
  assumptions, lifecycle proposal, and comparator/holdout mapping ambiguity.
  The replay makes zero model/network calls and remains evaluation evidence
  only. Recommendation: `1G-B2-F2-P3 - Integrate policy overlay into
  structured-output evaluation harness`.
- 1G-B2-F2-P3 integrates the deterministic policy overlay into the
  structured-output evaluation harness as the explicit `--apply-policy-overlay`
  option. The no-model saved-report replay command writes
  `reports/local_model_smoke/1G-B2-F2-P3/`, keeps the raw Phase A draft,
  overlay-corrected output, baseline comparison, and corrected comparison
  separate, and makes zero model/network calls. Corrected outputs validate 8/8.
  Baseline hard score remains 61/93 and overlay-corrected hard score remains
  74/93. `HG-018` remains blocked/blocked and the intended P2 severe-case
  outcomes are preserved. Remaining misses: hard booleans
  `contains_raw_private_or_ip_sensitive_context: 1`,
  `memory_boundary_or_write_authority_claim: 2`,
  `retrieval_or_source_use_request: 1`,
  `unresolved_assumption_or_open_decision: 5`; policy fields
  `lifecycle_status_proposal: 8`, `sensitivity_bucket_proposal: 2`. Lifecycle,
  unresolved-assumption, and memory-boundary misses are likely comparator or
  holdout-mapping cleanup; sensitivity/private-context/retrieval misses may be
  real overlay defects. Recommendation:
  `1G-B2-F2-C - Hard-gate comparator and holdout expectation cleanup`.
- Deterministic sensitivity checks are hard overrides for obvious cases such as API keys, passwords, tokens, `.env` content, forbidden paths, disallowed providers, invalid enums, and explicit confirmation requirements. They cannot reliably distinguish public literature data from proprietary prototype experimental data.

The accepted next local AI sequence is:

```text
1A         Classification-only Gemma 12B utility
1B         Thinking/token budget control
1B-R       CLI-only classification budget probe
1B-R-LIVE  Manual Gemma 12B classification probe
1C         Classification live probe analysis and roadmap rebase
1C-V       Local model bakeoff for form-driven classification
1C-W       Cross-model non-critical hint protocol repair
1C-X       Canonical non-critical hint form with model-specific prompt profiles
1C-Y       Fast staged memory intake design
1C-Z       FastIntakeSignalForm smoke test
1C-Z-R     Flat FastIntake smoke contract repair
1C-Z-S     Deterministic baseline and hybrid intake ownership
1C-Z-T     Cavemem/Caveman reference implementation audit
1D-A       Local-model-facing showcase files design
1D-B       Micro-context design
1D-C       MemoryStore facade design
1D-D       Internal compression policy tests
1D-E       SQLite/FTS schema design
1D-F       Progressive retrieval contract design
1D-G       Holdout intake generalization set
1E         Form protocol catalog design
1F         Structural validator + retry loop design
1G-A       Local model form-fill smoke harness skeleton
1G-B1      Installed local model form-fill smoke run
1G-B2-A    Fast secretary context pack compression and scoring refinement
1G-B2-B    Fast secretary recipe ablation
1G-B2-C    Qwen secretary context optimization
1G-B2-D    Expanded profiled Qwen secretary smoke run
1G-B2-D-R  Qwen profile failure analysis
1G-B2-E    Full holdout Qwen secretary smoke run
1G-B2-E-R  Full holdout Qwen failure analysis
1G-B2-F0   Structured-output reference audit and schema-first redesign
1G-B2-F1   Ollama structured-output schema smoke prototype
1G-B2-F2   Structured-output 12-case Qwen panel
1G-B2-F2-R Structured-output semantic failure analysis
1G-B2-F2-A Hard-gate schema prototype
1G-B2-F2-P Fast secretary policy-gate overlay design
1G-B2-F2-P1 Policy-gate overlay fixture prototype
1G-B2-F2-P2 Policy-gate overlay replay on saved F2-A outputs
1G-B2-F2-P3 Integrate policy overlay into structured-output evaluation harness
1G-B2-F2-C Hard-gate comparator and holdout expectation cleanup
1H         Showcase files generator design
1I         Context access from showcase files
1J         Provider/tool intent form design
```

Then:

```text
2A         Source-grounded review protocol
2B         Optional 31B/API sampling review
2C         Memory promotion policy
2D         Memory index generation
2E         Context package assembly
```

Then external provider hardening:

```text
3A         External prompt package format
3B         Redaction/sensitivity policy
3C         Provider abstraction hardening
3D         DeepSeek
3E         Grok
3F         Gemini
3G         GPT-5.5
3H         Provider selection policy
```

Do not start Context Pack Broker runtime, local gatekeeper runtime, provider routing, chat, memory runtime, retrieval runtime, tool execution, or BlueRev modeling before the form/protocol/memory foundation and reliability gates prove stable.

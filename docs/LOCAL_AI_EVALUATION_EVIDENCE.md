# Local AI Evaluation Evidence

This document is the canonical summary of JarvisOS local Gemma evaluation evidence. It preserves the reasoning trail from D7 through D10C without copying raw report JSON into documentation.

## Current Conclusion

JarvisOS must not proceed to broad Gemma orchestration yet.

Accepted local AI position:

- `gemma4:12b-it-qat` is viable only for narrow classification-style local utility work.
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
- The corrected architecture is form-driven local intelligence: Gemma performs semantic reasoning locally; JarvisOS provides showcase files, form schemas, structural validation, retries, persistence, promotion policy, and audit.
- Deterministic sensitivity checks are hard overrides for obvious cases such as API keys, passwords, tokens, `.env` content, forbidden paths, disallowed providers, invalid enums, and explicit confirmation requirements. They cannot reliably distinguish public literature data from proprietary prototype experimental data.

The accepted next local AI sequence is:

```text
1A         Classification-only Gemma 12B utility
1B         Thinking/token budget control
1B-R       CLI-only classification budget probe
1B-R-LIVE  Manual Gemma 12B classification probe
1C         Classification live probe analysis and roadmap rebase
1D         Gemma-facing showcase files design
1E         Form protocol catalog design
1F         Structural validator + retry loop design
1G         Gemma form-fill smoke test harness
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

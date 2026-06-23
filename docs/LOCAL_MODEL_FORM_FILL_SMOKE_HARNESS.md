# Local Model Form-Fill Smoke Harness

Milestones:

- 1G-A - Local model form-fill smoke harness skeleton
- 1G-B1 - Installed local model form-fill smoke run
- 1G-B2-A - Fast secretary context pack compression and scoring refinement
- 1G-B2-B - Fast secretary recipe ablation
- 1G-B2-C - Qwen secretary context optimization
- 1G-B2-D - Expanded profiled Qwen secretary smoke run
- 1G-B2-D-R - Qwen profile failure analysis
- 1G-B2-E - Full holdout Qwen secretary smoke run
- 1G-B2-F0 - Structured-output reference audit and schema-first redesign
- 1G-B2-F1 - Ollama structured-output schema smoke prototype
- 1G-B2-F2 - Structured-output 12-case Qwen panel
- 1G-B2-F2-R - Two-phase structured secretary semantic analysis
- 1G-B2-F2-A - Hard-gate schema prototype
- 1G-B2-F2-P - Fast secretary policy-gate overlay design
- 1G-B2-F2-P1 - Policy-gate overlay fixture prototype
- 1G-B2-F2-P2 - Policy-gate overlay replay on saved F2-A outputs
- 1G-B2-F2-P3 - Integrate policy overlay into structured-output evaluation harness
- 1G-B2-F2-C - Hard-gate comparator and holdout expectation cleanup
- 1G-B2-F2-B - Phase B soft hybrid review design

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

## 1G-B2-D Expanded Profiled Qwen Secretary Smoke Run

1G-B2-D tests whether the best 1G-B2-C Qwen profile generalizes beyond the
three optimized cases.

The exact matrix:

```text
model: qwen3:8b
packs: qwen_hybrid_v0_3, micro_rules_v0_2
cases: HG-001, HG-006, HG-016, HG-002, HG-005, HG-008, HG-009, HG-011, HG-017, HG-018, HG-022, HG-028
total: 24 local Ollama runs
```

Reports are written under:

```text
reports/local_model_smoke/1G-B2-D/
```

Summary files:

- `reports/local_model_smoke/1G-B2-D/expanded_profiled_qwen_summary.json`
- `reports/local_model_smoke/1G-B2-D/expanded_profiled_qwen_summary.md`

High-level result:

```text
micro_rules_v0_2: 8/12 parse, 56/96 hard, 37/60 soft exact, 38/60 soft tolerant, 4 gates, 1339 tokens
qwen_hybrid_v0_3: 9/12 parse, 62/96 hard, 37/60 soft exact, 38/60 soft tolerant, 3 gates, 1257 tokens
```

`qwen_hybrid_v0_3` remains the better profiled candidate on aggregate hard
score, parse count, critical gate count, and score-per-token diagnostics. It
did not maintain full parse stability or zero critical gates. The concerning
failure cases are `HG-006`, `HG-018`, and `HG-022`; all three failures were
`json_not_parsed` gates.

Recommended next milestone:

```text
1G-B2-D-R - Qwen profile failure analysis
```

Do not expand to the full 32-case set until failure analysis explains or
repairs the remaining parse/gate failures.

## 1G-B2-D-R Qwen Profile Failure Analysis

1G-B2-D-R inspects the `qwen_hybrid_v0_3` failures on `HG-006`, `HG-018`, and
`HG-022`.

Analysis report:

```text
docs/QWEN_PROFILE_FAILURE_ANALYSIS_1G_B2_D_R.md
```

The failures were not timeouts or model refusals. The raw outputs contained
Qwen thinking/prose plus malformed JSON-like objects with split strings,
duplicated fragments, or split enum/tag values. Parser-only hardening was not
chosen because heuristic repair could make malformed model text look accepted.

Created parse-safe pack:

```text
docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_HYBRID_PARSE_SAFE_v0_4.md
```

The v0.4 pack keeps the same semantic routing rules as v0.3 but removes the
table/example shape and moves strict JSON-only constraints to the top.

Narrow rerun:

```text
model: qwen3:8b
packs: qwen_hybrid_v0_3, qwen_hybrid_parse_safe_v0_4
cases: HG-006, HG-018, HG-022
total: 6 local Ollama runs
```

Reports are written under:

```text
reports/local_model_smoke/1G-B2-D-R/
```

High-level result:

```text
qwen_hybrid_v0_3:             0/3 parse,  0/24 hard,  0/15 soft tolerant, 3 gates, 1257 tokens
qwen_hybrid_parse_safe_v0_4:  3/3 parse, 20/24 hard, 15/15 soft tolerant, 0 gates, 1235 tokens
```

`qwen_hybrid_parse_safe_v0_4` fixed the targeted parse/gate failures in the
narrow rerun. `HG-018` still missed hard provider/memory-boundary fields, so the
next full holdout smoke run must remain manual-review only and track this
semantic risk.

Recommended next milestone:

```text
1G-B2-E - Full holdout Qwen secretary smoke run
```

## 1G-B2-E Full Holdout Qwen Secretary Smoke Run

1G-B2-E runs the first full 32-case local smoke test for the current parse-safe
Qwen secretary pack.

The exact matrix:

```text
model: qwen3:8b
pack: qwen_hybrid_parse_safe_v0_4
cases: HG-001 through HG-032 from docs/holdout/intake_generalization_v0.jsonl
total: 32 local Ollama runs
```

Reports are written under:

```text
reports/local_model_smoke/1G-B2-E/
```

Summary files:

- `reports/local_model_smoke/1G-B2-E/full_holdout_qwen_summary.json`
- `reports/local_model_smoke/1G-B2-E/full_holdout_qwen_summary.md`

High-level result:

```text
qwen_hybrid_parse_safe_v0_4: 28/32 parse, 169/256 hard, 103/160 soft exact, 104/160 soft tolerant, 4 gates, 1235 tokens
```

Parse and critical gate failures:

```text
HG-007, HG-017, HG-018, HG-024
```

The known `HG-018` provider/memory-boundary risk persisted as a parse/gate
failure. Other low-hard-score cases indicate remaining clarification, retrieval,
cross-project, personal/coursework memory, and provider/memory boundary risks.

Recommended next milestone:

```text
1G-B2-E-R - Full holdout Qwen failure analysis
```

Do not treat v0.4 as runtime-approved or default-queue-approved. The full
holdout parse score is below 30/32, and hard-field misses remain significant.

## 1G-B2-F0 Structured-Output Reference Audit And Schema-First Redesign

1G-B2-F0 changes the next direction from more prompt-only context-pack tuning
to schema-first structured-output experiments.

Design docs:

- `docs/STRUCTURED_OUTPUT_REFERENCE_AUDIT.md`
- `docs/FAST_SECRETARY_JSON_SCHEMA_DESIGN.md`

Decision:

```text
ADR-056 - Fast secretary structured output should become schema-first before runtime use
```

Core conclusion:

```text
Prompt-only JSON generation through the CLI is not robust enough for future
fast secretary approval. JSON Schema / structured-output experiments must come
before any runtime/default queue decision.
```

Prototype status:

```text
deferred to 1G-B2-F1
```

The optional prototype is deferred because 1G-B2-F0 is a design/audit milestone
and `1G-B2-F1` is already scoped as the local Ollama structured-output schema
smoke prototype.

Recommended next milestone:

```text
1G-B2-F1 - Ollama structured-output schema smoke prototype
```

## 1G-B2-F1 Ollama Structured-Output Schema Smoke Prototype

1G-B2-F1 materializes the schema-first structured-output prototype proposed by
F0.

Prototype files:

- `schemas/fast_secretary_intake_v0_1.schema.json`
- `scripts/local_model_structured_output_probe.py`

The probe uses Python standard library only. Dry-run mode loads the schema,
holdout cases, and context pack, validates planned inputs, writes no report,
and makes no Ollama call.

Real smoke matrix:

```text
model: qwen3:8b
schema: schemas/fast_secretary_intake_v0_1.schema.json
context pack: docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_HYBRID_PARSE_SAFE_v0_4.md
cases: HG-007, HG-017, HG-018, HG-024, HG-010, HG-013, HG-025, HG-015
total: 8 local Ollama API calls
```

Reports are written under:

```text
reports/local_model_smoke/1G-B2-F1/
```

Summary files:

- `reports/local_model_smoke/1G-B2-F1/structured_output_schema_smoke_summary.json`
- `reports/local_model_smoke/1G-B2-F1/structured_output_schema_smoke_summary.md`

High-level result:

```text
parse: 8/8
schema-valid: 8/8
validation failures: none
enum/type validation failures: none
```

This is structural evidence only. It does not prove semantic truth, memory
readiness, retrieval readiness, provider/tool readiness, queue readiness, or
BlueRev validity.

Known semantic risk:

```text
HG-018 returned review_only/none for provider and memory-boundary fields where
the expected policy was blocked/blocked. external_provider_allowed remained
false.
```

Recommended next milestone:

```text
1G-B2-F2 - Structured-output 12-case Qwen panel
```

Do not treat the F1 result as runtime approval. The next panel should measure
whether schema-first output remains stable across more difficult cases and
whether semantic gate behavior improves under manual review.

## 1G-B2-F2 Structured-Output 12-Case Qwen Panel

1G-B2-F2 keeps the F1 schema-first path and expands only to the scoped 12-case
panel.

The exact matrix:

```text
model: qwen3:8b
schema: schemas/fast_secretary_intake_v0_1.schema.json
context pack: docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_HYBRID_PARSE_SAFE_v0_4.md
cases: HG-007, HG-017, HG-018, HG-024, HG-010, HG-013, HG-025, HG-015, HG-001, HG-006, HG-016, HG-022
total: 12 local Ollama API calls
```

Reports are written under:

```text
reports/local_model_smoke/1G-B2-F2/
```

Summary files:

- `reports/local_model_smoke/1G-B2-F2/structured_output_12_case_panel_summary.json`
- `reports/local_model_smoke/1G-B2-F2/structured_output_12_case_panel_summary.md`

High-level result:

```text
parse: 12/12
schema-valid: 12/12
validation failures: none
enum/type validation failures: none
hard semantic comparison: 72/113
soft tolerant semantic comparison: 5/12
```

Severe hard-field miss cases:

```text
HG-007, HG-018, HG-024, HG-010, HG-013, HG-025
```

Error concentration:

```text
retrieval_source_policy: 10
bluerev_unresolved_assumptions: 7
clarification: 6
secrets: 3
provider_routing: 0
general_memory_classification: 15
```

`HG-018` provider/memory-boundary risk persisted. The model returned
`review_only` and `none` where `blocked` and `blocked` were expected.
`external_provider_allowed` remained `false`.

Interpretation:

- Structured output maintained the parse/schema channel on the 12-case panel.
- Semantic policy quality is not strong enough for full holdout expansion.
- The semantic comparison is against holdout labels only; it does not prove
  semantic truth.
- `semantic_truth_scored` remains `false`.
- `manual_review_required` remains `true`.

Recommended next milestone:

```text
1G-B2-F2-R - Structured-output semantic failure analysis
```

## 1G-B2-F2-R Two-Phase Structured Secretary Semantic Analysis

1G-B2-F2-R reinterprets the F2 result as a schema/field-ownership problem.

Design doc:

```text
docs/TWO_PHASE_SECRETARY_ANALYSIS_DESIGN_1G_B2_F2_R.md
```

Core conclusion:

```text
Structured output fixed the parse/schema channel, but the current single pass
mixes hard policy gates with soft review fields.
```

Corrected split:

- Phase A - hard schema-oriented gate pass.
- Phase B - soft hybrid review pass.

Phase A owns:

- secret/credential detection;
- raw private or IP-sensitive context detection;
- external provider or upload intent;
- memory boundary or write-authority claims;
- retrieval/source-use requests;
- unresolved assumptions or open decisions;
- clarification, redaction, provider permission, retrieval/source policy,
  lifecycle, sensitivity, and review gates.

Phase B owns:

- summary;
- project/domain labels;
- domain tags;
- storage relevance;
- soft rationale;
- possible memory-card type;
- follow-up question;
- usefulness for future review.

Phase B constraints:

```text
Phase B is advisory.
Phase B cannot override Phase A.
Phase B cannot unblock blocked/review-gated content.
Phase B cannot approve memory writes.
```

F2 miss interpretation:

- `HG-018`, `HG-010`, `HG-013`, and `HG-025` expose Phase A hard-gate
  failures around provider/raw-memory, ambiguous previous context, cross-project
  leakage, and ambiguous source/entity references.
- `HG-007` and `HG-024` include Phase A retrieval/conflict issues but also show
  comparator/schema-mapping ambiguity.
- project/domain/reason-code misses are mostly Phase B advisory failures.
- obvious secrets, provider upload intent, raw memory folders, forbidden paths,
  cross-project leakage, and ambiguous source IDs should receive deterministic
  policy overlays.

Recommended next milestone:

```text
1G-B2-F2-A - Hard-gate schema prototype
```

Do not run a full 32-case structured-output Qwen smoke until Phase A hard gates
are isolated and tested.

## 1G-B2-F2-A Hard-Gate Schema Prototype

1G-B2-F2-A materializes and tests the Phase A hard-gate schema.

Schema:

```text
schemas/fast_secretary_hard_gate_v0_1.schema.json
```

The schema intentionally omits summary, project, domain, tags, storage
usefulness, and rationale fields. It includes only hard gate fields for secrets,
raw private/IP-sensitive context, provider/upload intent, memory boundary,
retrieval/source use, unresolved assumptions, clarification, redaction,
provider permission, source/retrieval policy, lifecycle, sensitivity, review,
hard reason, and hard uncertainty.

The exact matrix:

```text
model: qwen3:8b
schema: schemas/fast_secretary_hard_gate_v0_1.schema.json
cases: HG-018, HG-010, HG-013, HG-025, HG-007, HG-024, HG-016, HG-017
total: 8 local Ollama API calls
context pack: none
```

Reports are written under:

```text
reports/local_model_smoke/1G-B2-F2-A/
```

Summary files:

- `reports/local_model_smoke/1G-B2-F2-A/hard_gate_schema_smoke_summary.json`
- `reports/local_model_smoke/1G-B2-F2-A/hard_gate_schema_smoke_summary.md`

High-level result:

```text
parse: 8/8
schema-valid: 8/8
validation failures: none
enum/type validation failures: none
hard-gate comparison: 61/93
HG-018 blocked/blocked: true
```

Wrong hard boolean counts:

```text
memory_boundary_or_write_authority_claim: 1
mentions_external_provider_or_upload_intent: 1
retrieval_or_source_use_request: 4
unresolved_assumption_or_open_decision: 5
```

Wrong policy field counts:

```text
allowed_future_retrieval_behavior: 4
clarification_required: 4
lifecycle_status_proposal: 8
sensitivity_bucket_proposal: 3
source_policy_for_future_retrieval: 2
```

Interpretation:

- Phase A kept the structured-output channel stable.
- `HG-018` improved to blocked/blocked.
- Hard-gate comparison only improved slightly over the F2 hard-rate baseline.
- Deterministic policy overlays are still needed for hard booleans and policy
  fields before Phase B soft review or full holdout expansion.

Recommended next milestone:

```text
1G-B2-F2-P - Fast secretary policy-gate overlay design
```

## 1G-B2-F2-P Fast Secretary Policy-Gate Overlay Design

1G-B2-F2-P designs the deterministic overlay that constrains the Phase A
hard-gate LLM draft before Phase B soft review.

Design doc:

```text
docs/FAST_SECRETARY_POLICY_GATE_OVERLAY_DESIGN.md
```

Pipeline:

```text
input/event
-> Phase A hard-gate LLM draft
-> deterministic policy-gate overlay
-> corrected hard-gate decision
-> Phase B soft hybrid review
-> manual review / memory proposal / no-write
```

Rule classes:

- mandatory block;
- mandatory review gate;
- mandatory clarification;
- candidate discovery;
- internal memory boundary;
- low-risk/default.

Precedence:

```text
mandatory block
-> clarification
-> review gate
-> candidate discovery
-> internal memory boundary
-> low-risk/default
```

Case replay conclusions:

- `HG-018`: preserve mandatory block for provider intent plus whole memory
  folder.
- `HG-007`: do not over-block public literature candidate discovery; use
  `review_only` plus `candidate_discovery_only`.
- `HG-013`: require clarification for cross-project JarvisOS memory style use
  in coursework.
- `HG-017`: block `.ssh/id_rsa` as secret/private path without inventing
  provider intent.
- `HG-024`: review-gate stale/superseded Gemma routing memory, not mandatory
  block.
- `HG-025`: require clarification for ambiguous "latest decision from memory
  document" references.

This milestone is docs-only. It adds no overlay code and makes zero model
calls.

Recommended next milestone:

```text
1G-B2-F2-P1 - Policy-gate overlay fixture prototype
```

## 1G-B2-F2-P1 Policy-Gate Overlay Fixture Prototype

1G-B2-F2-P1 implements the deterministic overlay as a small stdlib-only fixture
prototype.

Prototype:

```text
scripts/local_policy_gate_overlay_probe.py
```

Tests:

```text
tests/test_local_policy_gate_overlay_probe.py
```

Implemented rule classes:

- mandatory block;
- clarification;
- review gate;
- candidate discovery;
- internal memory boundary;
- low-risk/default.

Fixture coverage:

- `HG-018`-like provider memory upload forces blocked/blocked.
- `HG-007`-like public literature discovery remains candidate discovery only.
- `HG-013`-like cross-project memory-style use requires clarification.
- `HG-017`-like `.ssh/id_rsa` blocks without false provider intent.
- `HG-024`-like stale/superseded memory becomes review-gated.
- `HG-025`-like ambiguous memory document reference requires clarification.
- A mixed public-literature plus secret input proves block precedence.
- A low-risk internal note stays manual-review with no retrieval.

The fixture tests validate corrected outputs against
`schemas/fast_secretary_hard_gate_v0_1.schema.json` and verify that the overlay
adds no extra schema fields. This milestone makes zero model calls and adds no
runtime memory, retrieval, provider routing, or Phase B behavior.

Recommended next milestone:

```text
1G-B2-F2-P2 - Policy-gate overlay replay on saved F2-A outputs
```

## 1G-B2-F2-P2 Policy-Gate Overlay Replay

1G-B2-F2-P2 replays the deterministic overlay on saved F2-A hard-gate outputs.

Command:

```powershell
python scripts/local_policy_gate_overlay_probe.py --replay-report-dir reports/local_model_smoke/1G-B2-F2-A --holdout docs/holdout/intake_generalization_v0.jsonl --schema-path schemas/fast_secretary_hard_gate_v0_1.schema.json --out-dir reports/local_model_smoke/1G-B2-F2-P2
```

Reports:

```text
reports/local_model_smoke/1G-B2-F2-P2/
```

Replay results:

- cases replayed: 8
- corrected outputs schema-valid: 8/8
- baseline hard score: 61/93
- overlay-corrected hard score: 74/93
- model calls: 0
- network calls: 0

Intended case outcomes:

- `HG-018`: remains blocked/blocked with external provider blocked.
- `HG-007`: becomes `review_only` plus `candidate_discovery_only`.
- `HG-013`: becomes clarification-required.
- `HG-017`: blocks secret path and clears false provider/upload intent.
- `HG-024`: becomes `review_only` plus `review_gate_required`.
- `HG-025`: becomes clarification-required.

Remaining hard boolean misses:

```text
contains_raw_private_or_ip_sensitive_context: 1
memory_boundary_or_write_authority_claim: 2
retrieval_or_source_use_request: 1
unresolved_assumption_or_open_decision: 5
```

Remaining policy field misses:

```text
lifecycle_status_proposal: 8
sensitivity_bucket_proposal: 2
```

Probable comparator/holdout-mapping ambiguities:

- `HG-018` memory-boundary flag: broad memory-folder provider upload is already
  blocked as provider/raw-private context, while the comparator also expects a
  memory-boundary claim.
- `HG-024` lifecycle: `superseded` can describe the old referenced memory,
  while the new instruction can still be `proposed_memory`.

Recommended next milestone:

```text
1G-B2-F2-P3 - Integrate policy overlay into structured-output evaluation harness
```

## 1G-B2-F2-P3 Policy Overlay Harness Integration

1G-B2-F2-P3 integrates the deterministic overlay into the structured-output
evaluation harness as an explicit opt-in.

Flag:

```text
--apply-policy-overlay
```

The flag is valid only with:

```text
schemas/fast_secretary_hard_gate_v0_1.schema.json
```

No-model replay command:

```powershell
python scripts/local_model_structured_output_probe.py --replay-existing-report-dir reports/local_model_smoke/1G-B2-F2-A --apply-policy-overlay --schema-path schemas/fast_secretary_hard_gate_v0_1.schema.json --report-dir reports/local_model_smoke/1G-B2-F2-P3
```

Reports:

```text
reports/local_model_smoke/1G-B2-F2-P3/
```

Integration behavior:

- raw Phase A draft stays in `parsed_output`;
- corrected object is written to `policy_overlay_corrected_output`;
- baseline comparison is written to `baseline_semantic_comparison`;
- corrected comparison is written to `semantic_comparison`;
- comparison basis is `policy_overlay_corrected_output`;
- overlay application remains evaluation-only and opt-in.

P3 no-model replay results:

- cases evaluated: 8 saved F2-A outputs;
- corrected outputs schema-valid: 8/8;
- baseline hard score: 61/93;
- overlay-corrected hard score: 74/93;
- `HG-018` blocked/blocked preserved;
- model calls: 0;
- network calls: 0;
- overlay ready for future real local runs under `--apply-policy-overlay`: true.

Remaining hard boolean misses:

```text
contains_raw_private_or_ip_sensitive_context: 1
memory_boundary_or_write_authority_claim: 2
retrieval_or_source_use_request: 1
unresolved_assumption_or_open_decision: 5
```

Remaining policy field misses:

```text
lifecycle_status_proposal: 8
sensitivity_bucket_proposal: 2
```

Likely comparator/holdout ambiguity:

- lifecycle status expectations;
- unresolved-assumption semantics;
- memory-boundary expectation for whole-folder provider upload.

Likely real overlay defects:

- sensitivity proposals for some unknown/internal cases;
- one raw-private-context miss;
- one retrieval/source-use miss.

Recommended next milestone:

```text
1G-B2-F2-C - Hard-gate comparator and holdout expectation cleanup
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
- structured-output schema loading;
- structured-output dry-run without Ollama calls;
- structured-output result validation and summary generation.
- schema-facing semantic comparison mapping;
- semantic comparison misses and not-compared behavior;
- F2 summary generation with semantic score rollups.

## Future 1G-B

After 1G-B2-F2-P3, the next milestone is:

```text
1G-B2-F2-C - Hard-gate comparator and holdout expectation cleanup
```

1G-B2-F2-C should clean up comparator and holdout expectations before any Phase
B soft hybrid review or full holdout structured-output Qwen smoke run. The
schema-first path must remain local, explicit, bounded, auditable, and separate
from runtime memory, retrieval, provider routing, tool execution, and BlueRev
modeling.

## Milestone Boundary Confirmation

1G-B2-F2-P3 adds opt-in policy-overlay support to the structured-output
evaluation harness and derived reports. It does not integrate structured output
into runtime behavior.

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
- vendored code.

This milestone does not start `1G-B2-F2-C - Hard-gate comparator and holdout expectation cleanup`.

## 1G-B2-F2-B Phase B Soft Hybrid Review Design

`1G-B2-F2-B` adds the Phase B soft-review schema and design:

```text
schemas/fast_secretary_soft_review_v0_1.schema.json
docs/FAST_SECRETARY_PHASE_B_SOFT_REVIEW_DESIGN.md
tests/test_fast_secretary_phase_b_soft_review_schema.py
```

Phase B is advisory and monotonic. It receives Phase A constraints and may add
summary, labels, usefulness, rationale, and follow-up context for human review.
It cannot override Phase A, unblock blocked or clarification-required content,
approve provider use, approve retrieval, approve memory writes, execute tools,
or clear manual review.

Recommended next milestone:

```text
1G-B2-F2-B1 - Phase B soft-review fixture prototype
```

## 1G-B2-F2-B1 Phase B Soft-Review Fixture Prototype

`1G-B2-F2-B1` adds a deterministic fixture probe for Phase B:

```powershell
python scripts\local_phase_b_soft_review_probe.py `
  --phase-a-report-dir reports\local_model_smoke\1G-B2-F2-C `
  --schema-path schemas\fast_secretary_soft_review_v0_1.schema.json `
  --out-dir reports\local_model_smoke\1G-B2-F2-B1
```

The fixture is no-model and no-network. It creates one Phase B soft-review JSON
per saved Phase A result and a summary report. The summary must keep
`phase_b_can_override_phase_a = false`, `runtime_approved = false`, and
`semantic_truth_scored = false`.

Recommended next milestone:

```text
1G-B2-F2-B2 - Phase B soft-review harness integration
```

## 1G-B2-F2-B2 Phase B Soft-Review Harness Integration

`1G-B2-F2-B2` integrates Phase B soft review into the structured-output
evaluation harness as an explicit opt-in replay transform:

```powershell
python scripts\local_model_structured_output_probe.py `
  --replay-existing-report-dir reports\local_model_smoke\1G-B2-F2-C `
  --apply-phase-b-soft-review `
  --schema-path schemas\fast_secretary_hard_gate_v0_1.schema.json `
  --phase-b-schema-path schemas\fast_secretary_soft_review_v0_1.schema.json `
  --report-dir reports\local_model_smoke\1G-B2-F2-B2
```

Phase B remains advisory only. The harness records schema validation,
monotonicity violations, model/network call status, and runtime approval status.
It cannot override Phase A, approve memory writes, approve retrieval, approve
provider use, execute tools, or clear manual review.

Recommended next milestone:

```text
1G-B2-F2-B3 - Phase B local structured-output soft-review smoke
```

## 1G-B2-F2-B3 Phase B Local Structured-Output Soft-Review Smoke

`1G-B2-F2-B3` adds `scripts/local_phase_b_soft_review_model_probe.py`.

The smoke is intentionally small:

```text
model: qwen3:8b
schema: schemas/fast_secretary_soft_review_v0_1.schema.json
cases: HG-007, HG-018, HG-024, HG-025
source: reports/local_model_smoke/1G-B2-F2-B2
```

The report is written under:

```text
reports/local_model_smoke/1G-B2-F2-B3/
```

This remains manual-review-only. Passing the smoke does not approve runtime use.

## 1G-B2-F2-B3-S Phase B Soft-Only Schema Split

B3-S replaces the previous model-facing Phase B schema with a soft-only proposal
schema for local model calls:

```text
schemas/fast_secretary_soft_proposal_v0_1.schema.json
```

Run command:

```powershell
python scripts\local_phase_b_soft_review_model_probe.py `
  --run-local `
  --source-b2-report-dir reports\local_model_smoke\1G-B2-F2-B2 `
  --schema-path schemas\fast_secretary_soft_proposal_v0_1.schema.json `
  --out-dir reports\local_model_smoke\1G-B2-F2-B3-S `
  --model qwen3:8b `
  --case-ids HG-007,HG-018,HG-024,HG-025 `
  --timeout-seconds 180
```

The summary must show no authority-field leakage and `runtime_approved=false`.

## 1G-B2-F2-B4 Phase B Expanded Local Soft-Review Panel

B4 expands the corrected soft-only Phase B smoke to eight cases:

```text
HG-007, HG-010, HG-013, HG-016, HG-017, HG-018, HG-024, HG-025
```

The report is written under:

```text
reports/local_model_smoke/1G-B2-F2-B4/
```

The structural acceptance criteria are parse, schema validity, and zero
authority-field leakage. B4 also records separate soft-quality diagnostics, but
those diagnostics do not approve semantic truth or runtime use.

## 1G-B2-F2-B5-A General Phase B Instruction Repair

B5-A keeps the B4 eight-case panel but repairs the model-facing instruction
profile with general reusable category guidance.

Run command:

```powershell
python scripts\local_phase_b_soft_review_model_probe.py `
  --run-local `
  --source-b2-report-dir reports\local_model_smoke\1G-B2-F2-B2 `
  --schema-path schemas\fast_secretary_soft_proposal_v0_1.schema.json `
  --out-dir reports\local_model_smoke\1G-B2-F2-B5-A `
  --model qwen3:8b `
  --case-ids HG-007,HG-010,HG-013,HG-016,HG-017,HG-018,HG-024,HG-025 `
  --timeout-seconds 180
```

Acceptance compares against the B4 soft-quality baseline of `14/29` while
preserving parse, schema validity, and zero authority-field leakage.

## 1G-B2-F2-B5-B Deterministic Secret/Private Soft Clamp

B5-B keeps the B4/B5-A eight-case panel and adds deterministic post-model
effective-proposal clamping.

Run command:

```powershell
python scripts\local_phase_b_soft_review_model_probe.py `
  --run-local `
  --source-b2-report-dir reports\local_model_smoke\1G-B2-F2-B2 `
  --schema-path schemas\fast_secretary_soft_proposal_v0_1.schema.json `
  --out-dir reports\local_model_smoke\1G-B2-F2-B5-B `
  --model qwen3:8b `
  --case-ids HG-007,HG-010,HG-013,HG-016,HG-017,HG-018,HG-024,HG-025 `
  --timeout-seconds 180
```

Acceptance uses the effective proposal, not the raw model proposal:

- parse `8/8`;
- raw schema validity `8/8`;
- effective schema validity `8/8`;
- raw authority leakage reported separately;
- effective authority leakage must be `0`;
- effective soft quality must improve over the B5-A baseline of `22/29`.

Clamp count is evidence only. It is not a pass requirement.

## 1G-B2-F2-B5-C Sensitivity-Aware Phase B Semantic Repair

B5-C keeps the same eight-case continuity panel and updates deterministic Phase
B handling for sensitivity semantics.

Run command:

```powershell
python scripts\local_phase_b_soft_review_model_probe.py `
  --run-local `
  --source-b2-report-dir reports\local_model_smoke\1G-B2-F2-B2 `
  --schema-path schemas\fast_secretary_soft_proposal_v0_1.schema.json `
  --out-dir reports\local_model_smoke\1G-B2-F2-B5-C `
  --model qwen3:8b `
  --case-ids HG-007,HG-010,HG-013,HG-016,HG-017,HG-018,HG-024,HG-025 `
  --timeout-seconds 180
```

Acceptance:

- parse `8/8`;
- raw schema validity `8/8`;
- effective schema validity `8/8`;
- raw authority leakage `0`;
- effective authority leakage `0`;
- raw soft quality at least `22/29`;
- effective soft quality at least `26/29`;
- runtime approval remains `false`.

B5-C also adds deterministic tests for English and Italian provider-negation
phrases so local-only private/IP-sensitive memory is not misclassified as
external-provider upload intent.

# Structured Output Reference Audit

Milestone: `1G-B2-F0 - Structured-output reference audit and schema-first redesign`

This document is design/reference analysis only. It adds no runtime memory,
retrieval, provider routing, backend route, frontend UI, queue behavior,
external provider call, model call, vendored dependency, or BlueRev modeling.

## Executive Summary

The full-holdout Qwen secretary run showed that prompt-only JSON generation is
not reliable enough for future default-queue or runtime approval.

Current evidence:

```text
model: qwen3:8b
pack: qwen_hybrid_parse_safe_v0_4
cases: 32
parse: 28/32
hard: 169/256
soft exact: 103/160
soft tolerant: 104/160
critical gates: 4
parse/gate failures: HG-007, HG-017, HG-018, HG-024
```

The next robust step is schema-first structured generation. Context packs can
carry domain hints, but the output contract should be owned by JSON Schema,
constrained output where available, structural validation, semantic scoring, and
manual review.

## Reference Patterns

### Ollama Structured Outputs

Ollama supports structured outputs by passing a JSON Schema through the
`format` parameter of its local API. The design pattern for JarvisOS is:

```text
input + compact context pack + JSON Schema
-> local Ollama structured-output request
-> JSON object shaped by schema
-> structural validator
-> semantic scorer
-> manual-review evidence
```

JarvisOS implication:

- stop relying only on CLI text output plus parser recovery;
- test the local Ollama API with schema-constrained output;
- keep output schema small and explicit;
- treat schema validity as structure only, not semantic truth.

### JSON Mode Is Not Enough

JSON mode aims at parseable JSON. JSON Schema aims at required fields, enum
values, booleans, arrays, and object shape.

JarvisOS needs schema-level control because fast secretary output includes:

- exact enum values;
- required policy fields;
- blocked/review-only retrieval fields;
- boolean gates such as `not_decided`, `clarification_required`, and
  `redaction_required`;
- bounded arrays such as `domain_tags` and `uncertain_fields`.

Valid JSON alone would not prevent semantically risky values, missing policy
fields, or vague free-text substitutions.

### Constrained Decoding

Structured-output systems commonly enforce JSON Schema, grammar, regex, or EBNF
constraints during decoding rather than relying only on post-hoc parsing.

JarvisOS should treat constrained decoding as a structure reliability tool:

- it can reduce syntax failures and missing fields;
- it does not prove factual correctness;
- it does not authorize memory writes, provider calls, retrieval, tool calls, or
  BlueRev assumptions;
- it must be followed by deterministic validation and manual review.

### Outlines

Outlines is a useful reference pattern for generating text under JSON Schema,
regular-expression, or grammar constraints.

JarvisOS takeaway:

- schema/grammar should be an explicit artifact;
- decoding constraints should not be buried in prompt wording;
- model output should be considered a proposal even when it is structurally
  valid.

Outlines is reference-only for this milestone. JarvisOS does not vendor or
integrate it here.

### Guidance

Guidance demonstrates the value of structured generation programs and typed
slots. It treats generation as constrained filling rather than free prose.

JarvisOS takeaway:

- separate short categorical fields from optional review prose;
- keep policy-relevant outputs in enums and booleans;
- defer long natural-language explanations until the core form is stable.

Guidance is reference-only for this milestone.

### XGrammar, vLLM, And SGLang

XGrammar, vLLM, and SGLang are relevant because they show the broader direction:
fast grammar or schema-constrained generation can become an inference-layer
capability rather than an application parser trick.

JarvisOS takeaway:

- future local serving choices should consider schema/grammar support;
- immediate work should stay with the already local Ollama path;
- no runtime server, model-serving replacement, or dependency integration is
  added in this milestone.

### DSPy And BAML

DSPy and BAML are useful as design references because they move prompt work
toward typed signatures, metrics, evaluation, and repeatable optimization.

JarvisOS takeaway:

- define a typed output contract first;
- define scoring before broader reruns;
- run small difficult-case panels before full holdout reruns;
- treat prompt/context changes as testable protocol variants, not ad hoc prose
  tuning.

DSPy and BAML are reference-only. JarvisOS does not vendor or integrate them in
this milestone.

## JarvisOS Diagnosis

The current fast secretary profile has two separate problems:

1. **Structure reliability**: prompt-only CLI output still produced parse/gate
   failures on the full holdout set.
2. **Semantic reliability**: even parsed outputs still missed hard fields in
   clarification, retrieval, provider/memory-boundary, personal/coursework, and
   BlueRev cases.

Structured output can address the first problem. It cannot solve the second by
itself.

## Recommended Architecture Shift

Current path:

```text
context pack text
-> Qwen CLI free-text generation
-> parser recovery
-> scoring
```

Recommended experiment path:

```text
compact context pack
+ JSON Schema
+ local Ollama structured-output API
-> strict JSON object
-> structural validator
-> semantic scorer
-> manual-review evidence
```

## Layer Responsibilities

| Layer | Responsibility |
|---|---|
| Context pack | Domain hints, routing principles, compact reminders |
| JSON Schema | Shape, required fields, enums, arrays, booleans, short descriptions |
| Structured-output API | Syntactic and schema-constrained generation |
| Structural validator | Reject malformed or incomplete output |
| Semantic scorer | Compare against holdout expectations |
| JarvisOS policy gate | Own hard safety/provenance decisions |
| Manual review | Decide whether evidence is acceptable |

## Milestone Recommendation

Next milestone:

```text
1G-B2-F1 - Ollama structured-output schema smoke prototype
```

The prototype should stay small: local-only, no new dependency, no external
provider, no runtime integration, and no full 32-case rerun.

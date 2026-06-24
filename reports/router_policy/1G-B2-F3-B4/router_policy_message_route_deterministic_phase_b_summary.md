# 1G-B2-F3-B4 - Deterministic Phase B soft-review source

Start HEAD: `9b9ec90537c4f387d276485d1a4bddeb5477a5b3`

## Source

Detected source function:

```text
local_phase_b_soft_review_probe.build_soft_review(*, case_id, input_text, phase_a)
```

Shape compatibility with B1: true.

Adapter required: false.

The deterministic builder already emits the 11 B1-required fields:

- `summary_short`
- `project_bucket`
- `primary_domain`
- `domain_tags`
- `storage_relevance`
- `usefulness_for_future_review`
- `possible_memory_card_type`
- `soft_reason_code`
- `brief_rationale`
- `suggested_followup_question`
- `soft_uncertain_fields`

## Path

B4 replaces the fixed benign Phase B stub only in an explicit offline path. The
default B3 stub path remains available and unchanged.

```text
message
-> deterministic Phase A overlay / A5-R1 operational gates
-> deterministic Fast Secretary Phase B soft review
-> B1 Phase B RouterHint bridge
-> RouterPolicy decision
-> semantic validator
-> A3 safe-local guard
```

## Panel

| case_id | sanitized message | Phase B reason | outcome |
|---|---|---|---|
| `B4-BENIGN` | Synthetic benign local-answer request about a centrifugal pump. | `contextual_summary` | `local_answer` with injected responder |
| `B4-SOURCE` | Synthetic public DOI/source review request about algae modeling. | `source_candidate` | `not_safe_local_route` |
| `B4-AMBIGUITY` | Synthetic unresolved-reference request. | `blocked_by_phase_a` | `not_safe_local_route` |
| `B4-HARD-GATE` | Synthetic secret-placeholder request; raw token omitted. | `blocked_by_phase_a` | `not_safe_local_route` |

Coherent triple check: pass.

Cross-case mix detected: false.

Malformed Phase B result: invalid deterministic Phase B failed closed before
RouterPolicy/A3.

## Privacy

Reports use synthetic or sanitized messages only.

No raw model output, raw private prompts, raw secret tokens, or BlueRev private
content are committed.

## Boundary

- Qwen Phase A/gate producer added: false
- live Qwen/Gemma/Ollama call added: false
- provider/tool/MCP/browser/terminal runtime added: false
- memory/retrieval runtime added: false
- backend/frontend/DB added: false
- BlueRev behavior added: false

## Residual Risks

- B4 is offline/deterministic only.
- B4 does not approve live Phase B.
- B4 does not approve chat or removal of `--assume-public-simple`.
- Phase B remains advisory only.
- Phase A/gates remain deterministic authority.
- B1 is a bridge over structurally valid Phase B proposals, not a raw
  model-output normalizer.
- Prompt-real/private runs must remain outside committed reports unless
  sanitized.

Recommended next milestone:

```text
1G-B2-F3-B4-R - Deterministic Phase B source audit
```

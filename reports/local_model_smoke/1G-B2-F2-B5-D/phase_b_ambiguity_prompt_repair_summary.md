# 1G-B2-F2-B5-D Phase B Ambiguity Prompt Repair Summary

Manual review is required. This smoke does not prove semantic truth or approve runtime use.

- model: `qwen3:8b`
- cases: `HG-007,HG-010,HG-013,HG-016,HG-017,HG-018,HG-024,HG-025`
- parse: 8/8
- raw schema valid: 8/8
- effective schema valid: 8/8
- raw authority leakage: 0
- effective authority leakage: 0
- raw quality before B5-D: 24/29
- raw quality after B5-D: 28/29
- effective quality before B5-D: 29/29
- effective quality after B5-D: 29/29
- HG-013 improved: True
- HG-025 improved: True
- HG-024 regressed: False
- HG-007 regressed: False
- local Ollama calls made: True
- external provider calls made: False
- runtime approved: False
- semantic truth scored: False

## Raw Misses After B5-D

- `HG-017`: [{'actual': 'high', 'field': 'storage_relevance', 'forbidden': ['high'], 'reason': 'advisory soft-quality forbidden value'}]

## Case Notes

- `HG-013`: raw `clarification_context`, card `none`, storage `low`.
- `HG-025`: raw `clarification_context`, card `none`, storage `low`.
- `HG-024`: raw `decision_candidate`, card `decision_card`, storage `high`.
- `HG-007`: raw `source_candidate`, card `source_card`, storage `high`.

B5-D is a prompt-only semantic repair for unresolved prior references. It does not change Phase A overlay, deterministic clamps, provider/export detection, schemas, runtime memory, retrieval, provider routing, or tools.

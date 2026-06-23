# 1G-B2-F2-B5-B Deterministic Phase B Soft Clamp Summary

Manual review is required. This smoke does not prove semantic truth or approve runtime use.

- total runs: 8
- parse: 8/8
- raw schema valid: 8/8
- effective schema valid: 8/8
- raw authority field leakage count: 0
- effective authority field leakage count: 0
- deterministic soft clamp count: 28
- deterministic soft clamp cases: ['HG-010', 'HG-013', 'HG-016', 'HG-017', 'HG-018', 'HG-025']
- model-facing schema has authority fields: False
- instruction profile case-specific: False
- local Ollama calls made: True
- external provider calls made: False
- runtime approved: False
- raw soft quality: 22/29
- effective soft quality: 26/29
- B5-A baseline: 22/29
- effective improved over B5-A baseline: True
- raw soft quality miss count: 7
- effective soft quality miss count: 3
- strong enough for semantic quality review: True
- recommended next milestone: 1G-B2-F2-B5 - Phase B semantic quality review

Qwen receives only the soft-only proposal schema and the input text. Phase A hard fields are merged later by deterministic Python into an internal review envelope.

The raw Qwen soft proposal is preserved for audit. The review envelope uses the deterministic effective soft proposal.

Raw quality describes Qwen behavior. Effective quality describes Qwen plus deterministic clamp behavior. Neither approves runtime behavior, memory writes, retrieval, provider use, tool execution, or semantic truth.

No memory, retrieval, provider routing, tool execution, backend route, frontend UI, queue, worker, hook, MCP, or BlueRev modeling behavior is added.

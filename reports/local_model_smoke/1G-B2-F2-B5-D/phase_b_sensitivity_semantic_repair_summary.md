# 1G-B2-F2-B5-C Sensitivity-Aware Phase B Semantic Repair Summary

Manual review is required. This smoke does not prove semantic truth or approve runtime use.

- total runs: 8
- parse: 8/8
- raw schema valid: 8/8
- effective schema valid: 8/8
- raw authority field leakage count: 0
- effective authority field leakage count: 0
- deterministic soft clamp count: 22
- deterministic soft clamp cases: ['HG-010', 'HG-016', 'HG-017', 'HG-018']
- model-facing schema has authority fields: False
- instruction profile case-specific: False
- local Ollama calls made: True
- external provider calls made: False
- runtime approved: False
- raw soft quality: 28/29
- effective soft quality: 29/29
- B5-A baseline: 22/29
- B5-C raw minimum: 22/29
- B5-C effective minimum: 26/29
- effective improved over B5-A baseline: True
- raw soft quality miss count: 1
- effective soft quality miss count: 0
- strong enough for semantic quality review: True
- recommended next milestone: 1G-B2-F2-B5 - Phase B semantic quality review

Qwen receives only the soft-only proposal schema and the input text. Phase A hard fields are merged later by deterministic Python into an internal review envelope.

The raw Qwen soft proposal is preserved for audit. The review envelope uses the deterministic effective soft proposal.

B5-C distinguishes secret/credential material, provider/private export risk, local IP-sensitive memory, and ambiguous unresolved references.

Raw quality describes Qwen behavior. Effective quality describes Qwen plus deterministic clamp behavior. Neither approves runtime behavior, memory writes, retrieval, provider use, tool execution, or semantic truth.

No memory, retrieval, provider routing, tool execution, backend route, frontend UI, queue, worker, hook, MCP, or BlueRev modeling behavior is added.

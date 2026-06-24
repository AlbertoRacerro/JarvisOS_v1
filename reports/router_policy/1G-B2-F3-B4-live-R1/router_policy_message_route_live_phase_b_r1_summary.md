# 1G-B2-F3-B4-live-R1 Phase B Provenance Leakage Repair Summary

Manual review is required. This repair does not approve production routing or semantic truth.

- start head: `4de1de0b6933bd2d28f1327f935ec5e0b2e0161f`
- bug fixed: live Phase B build seam no longer self-injects `phase_a_case_id`
  before authority leakage checks
- removed premature `phase_a_case_id` from build seam: true
- provenance added only in apply wrapper: true
- mismatch guard preserved: true
- regression test exercises real build seam: true
- lower-level live call/parse/validate path patched in test: true
- direct build assertion passed: true
- integration assertion passed: true
- default stub path unchanged: true
- deterministic B4 path unchanged: true
- live selector policy unchanged: true
- localhost validation unchanged: true

The R1 regression test calls `_build_live_local_phase_b_soft_review(...)`
directly. It patches `call_ollama_chat`, `parse_soft_proposal`,
`validate_instance`, and schema loading only, so the real output assembly and
provenance boundary are exercised.

Runtime boundary:

- Qwen remains Phase B advisory only.
- Phase A/gates remain deterministic authority.
- B1 is not a raw model-output normalizer.
- RouterPolicy/A3 remain authority before local execution.
- No backend routes, frontend UI, DB schema, memory runtime, retrieval runtime,
  provider/tool routing, MCP, browser, terminal execution, worker, hook, or
  BlueRev behavior is added.

Known residual risks:

- B4-live remains smoke-only.
- Live Qwen Phase B remains advisory only.
- Phase A/gates remain deterministic authority.
- B1 is not a raw model-output normalizer.
- No removal of `--assume-public-simple` is approved.
- No production UI/chat/memory/retrieval/provider/tool routing is approved.
- Real/private prompt runs must remain outside committed reports unless sanitized.

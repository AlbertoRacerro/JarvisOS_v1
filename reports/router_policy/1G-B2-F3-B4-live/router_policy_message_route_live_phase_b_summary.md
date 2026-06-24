# 1G-B2-F3-B4-live Local Qwen Phase B Soft-Review Smoke Summary

Manual review is required. This milestone does not approve production routing or semantic truth.

- start head: `609b5493891d7d9eb2d1de4ee5b652bf6e34f024`
- reused live Phase B module: `local_phase_b_soft_review_model_probe`
- new Qwen caller added: false
- default stub path unchanged: true
- deterministic B4 path unchanged: true
- source selector: `stub | deterministic | live_local_qwen`
- live Phase B explicit flag required: true
- localhost-only endpoint enforced: true
- tests use fake live seam: true
- B1 called after valid live Phase B insertion: pass
- raw authority leakage result: rejected fail-closed
- effective authority leakage result: rejected fail-closed
- malformed live output result: rejected fail-closed
- missing-field effective proposal result: rejected fail-closed
- live exception result: rejected fail-closed
- hard-gate dominance result: pass
- source/current-info result: pass

The live path reuses:

- `AUTHORITY_FIELD_NAMES`
- `authority_field_leakage(...)`
- `parse_soft_proposal(...)`
- `apply_deterministic_soft_clamp(...)`
- `local_model_structured_output_probe.call_ollama_chat(...)`

The smoke wrapper validates `--phase-b-endpoint` with `urllib.parse.urlparse`
before any live call. It accepts HTTP localhost origins only and rejects
credentials, non-localhost hosts, query strings, fragments, and paths before
building the `/api/chat` endpoint.

Privacy check:

- synthetic/sanitized report data only: true
- model output committed: false
- raw private prompt committed: false
- raw secret token committed: false
- BlueRev private content committed: false

Runtime boundary:

- Qwen is Phase B advisory only.
- Phase A/gates remain deterministic authority.
- B1 is not a raw model-output normalizer.
- RouterPolicy/A3 remain authority before local execution.
- No backend routes, frontend UI, DB schema, memory runtime, retrieval runtime,
  provider/tool routing, MCP, browser, terminal execution, worker, hook, or
  BlueRev modeling behavior is added.

Known residual risks:

- B4-live is smoke-only.
- Live Qwen Phase B remains advisory only.
- Phase A/gates remain deterministic authority.
- B1 is not a raw model-output normalizer.
- No removal of `--assume-public-simple` is approved.
- No production UI/chat/memory/retrieval/provider/tool routing is approved.
- Real/private prompt runs must remain outside committed reports unless sanitized.

Recommended next milestone:

```text
1G-B2-F3-B4-live-R - Local Qwen Phase B soft-review audit
```

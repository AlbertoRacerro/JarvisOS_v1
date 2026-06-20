# 0E-D6D Organic Architecture Alignment Audit

## 1. Executive Judgement

JarvisOS is aligned enough to proceed to the local Gemma evaluation foundation, provided the next step stays docs/test-harness focused and does not add runtime routing.

The runtime remains narrow and mostly diagnostic: FAST_DEV policy, the AI Gateway, Scaleway smoke paths, DeepSeek provider smoke, and the Supervisor public-test endpoint are useful evidence, but they are not the final AI architecture. The main architectural correction is sequence discipline:

1. Prove local Gemma can work with JarvisOS context, memory strategy, deterministic tools, and structured output expectations.
2. Then define local gate contracts and dry-run behavior.
3. Only after those gates are stable should external provider tiers become routing behavior.

No runtime code changes are required for D6D. The corrections in this pass are documentation clarifications only.

## 2. Current Canonical Architecture

The canonical order after D6, D6B, and D6C is:

0. Existing AI foundation:
   - FAST_DEV policy mode.
   - Scaleway smoke adapter and optional live smoke call.
   - DeepSeek smoke adapter.
   - Narrow Supervisor public-test endpoint.
   - Event redaction, settings gates, budget gates, and smoke token accounting.
1. Local AI Foundation:
   - Gemma 12B/31B as a future local worker.
   - Context pack design.
   - Memory strategy.
   - Deterministic tool contracts.
   - Structured output expectations.
   - Local evaluation harness and golden set.
2. Local Gatekeeper:
   - Hard deterministic rules first.
   - Gemma local classifier only after evaluation proves useful behavior.
   - Gate dry-run before enforcement or routing.
   - No external call at this stage.
3. Logical gates:
   - `LOCAL_ONLY`
   - `LOCAL_GEMMA`
   - `USER_CONFIRM_REQUIRED`
   - `CHEAP_GATE`
   - `CHEAP_PLUS_GATE`
   - `SCIENTIFIC_MEDIUM_GATE`
   - `FRONTIER_GATE`
   - `BLOCKED`
4. External provider tiers:
   - `cheap`: DeepSeek.
   - `cheap_plus`: Grok.
   - `scientific_medium`: Gemini 3.1 Pro / Deep Think.
   - `frontier`: GPT-5.5.
5. External provider implementation:
   - One provider at a time.
   - Smoke-only first.
   - Review and hardening after each provider.
   - No broad Supervisor routing until local evaluation, local gates, and audit policy are stable.

Scaleway remains an existing smoke provider, optional simulation plumbing, possible EU fallback, and adapter example. It must not be described as the privacy classifier, local gatekeeper, core router, or required optimal future provider.

## 3. What Remains Valid From D3, D4, and D5

D3 remains valid as the current fast development safety policy. FAST_DEV can allow public/internal technical prompts while blocking structural secret patterns. It is not a full production privacy model and should not be treated as the local gatekeeper.

D4 remains valid as a narrow DeepSeek smoke path. DeepSeek can be the future `cheap` tier candidate, but the existing adapter is smoke-only and should not become broad routing by accident.

D5 remains valid as a narrow Supervisor public-test endpoint. It proves a single backend Supervisor surface can exist without exposing provider choice to the user, but it is not chat, not memory, not file-aware, not a BlueRev assistant, and not the final routing policy.

## 4. What Remains Valid From D6

D6 is still correct on these points:

- JarvisOS should move toward one stable user-facing Supervisor AI rather than provider-branded bots.
- Users should not normally choose DeepSeek, Grok, GPT, Gemini, Claude, or Scaleway as product personas.
- Provider/model details should remain internal, admin-only, or diagnostic.
- Provider tiers are useful as a later abstraction.
- Provider-specific implementation should stay behind adapters.

D6 is no longer the next implementation sequence. Its provider-tier contract skeleton is postponed until the local Gemma foundation and local gate design are better proven.

## 5. What D6B Supersedes

D6B supersedes any provider-first interpretation of D6.

The local gatekeeper must exist before cloud provider routing. The local gatekeeper owns the decision about whether content can leave the machine. Cloud providers must not be the first classifier for raw user input. Scaleway, DeepSeek, Grok, Gemini, GPT, Claude, or any other external provider cannot be used as the initial privacy/sensitivity judge.

The corrected high-level flow is:

```text
User input
-> local deterministic hard rules
-> optional local Gemma classifier after evaluation
-> logical gate decision
-> optional external provider adapter
```

## 6. What D6C Supersedes Or Postpones

D6C postpones direct implementation of local gate contracts.

Before local Gemma can assist gatekeeping, JarvisOS needs a local evaluation foundation proving that Gemma can handle:

- JarvisOS context packs.
- Memory strategy inputs.
- Deterministic tool results.
- Structured output schemas.
- Refusal and uncertainty behavior.
- Reproducible golden-set scoring.

D6C also postpones:

- Gemma runtime.
- Ollama, LiteLLM, or model-server integration.
- Memory runtime.
- Provider routing.
- External provider expansion.
- Supervisor routing changes.

## 7. Current Runtime Status

The runtime inspected during D6D is acceptable for its current scope:

- `AIGateway` remains the route entry point for AI endpoints.
- `POST /ai/smoke-console/run` remains a controlled Scaleway smoke console, not chat.
- `POST /ai/provider-smoke/run` is DeepSeek smoke-only.
- `POST /ai/supervisor/public-test` is a narrow public/internal technical test endpoint.
- Provider HTTP logic remains isolated in provider modules and adapters.
- Privacy decisions are local.
- Event payload redaction masks sensitive keys and prompt-like fields.
- The legacy `provider_mode` setting remains a smoke-path compatibility control.

Runtime concerns are architectural, not blocking:

- `provider_mode` is still provider-specific and should remain legacy/diagnostic.
- Scaleway token counters are provider-specific and should not become the generic AI accounting model without review.
- Supervisor provider selection is temporary and should not be expanded before local Gemma evaluation and gate dry-run milestones.

## 8. Current Documentation Inconsistencies

The audit found five small documentation inconsistencies:

1. ADR-029 still named the local gate/external tier contract skeleton as the next milestone even though ADR-030 superseded that sequence.
2. `docs/ARCHITECTURE.md` described Scaleway as "the first real-provider candidate", which could be read as future centrality rather than historical smoke-path status.
3. The original D6 document still said to start incrementally with `AIProviderTier`, despite the correction notices above and below it.
4. The D6B document still carried exact old D7 milestone labels in its historical next-milestone section.
5. One nightly upscale review document preserved a Scaleway router proposal without a current supersession note.

Older milestone and nightly docs still contain historical provider abstraction language. They were not broadly rewritten because they document earlier states and backlog thinking. Future canonical docs should point to D6D when there is ambiguity.

## 9. Corrections Made

This audit made documentation-only corrections:

- ADR-029 now explicitly defers to ADR-030 and names `0E-D7 - Local Gemma Evaluation Harness and Golden Set`.
- The architecture overview now says Scaleway was the first real-provider smoke candidate and is not the local privacy classifier, local gatekeeper, or core Supervisor router.
- The D6 architecture document now marks the original `AIProviderTier` next step as superseded by D6C.
- The D6B architecture document now avoids exact superseded D7 milestone labels in its historical section.
- The nightly AI router review now has a D6D supersession note stating that Scaleway router guidance is historical only.

## 10. Future Naming Conventions

Use these terms consistently:

- `Local AI Foundation`: Gemma evaluation, context pack, memory strategy, deterministic tools, and structured output expectations.
- `LocalGatekeeper`: local deterministic and optional local-model sensitivity gate; no cloud dependency.
- `LogicalGate`: an auditable gate decision such as `LOCAL_ONLY`, `CHEAP_GATE`, or `BLOCKED`.
- `ExternalTier`: a product-level class of external capability such as `cheap`, `cheap_plus`, `scientific_medium`, or `frontier`.
- `ActualProvider`: a concrete provider adapter such as DeepSeek, Grok, Gemini, GPT, or Scaleway.
- `SmokeProvider`: diagnostic provider path used to prove credentials, gates, and accounting.
- `provider_mode`: legacy compatibility setting for current smoke paths; do not use it as the future routing abstraction.
- `Supervisor`: one user-facing AI interface, not a family of provider-branded assistants.

## 11. Canonical Milestone Order

0E-D7 implementation note: the local Gemma evaluation harness and 65-case golden set now exist. The remaining sequence starts after that foundation.

The recommended sequence is:

1. `0E-D8 - Local Gemma Runtime Adapter Dry Run`.
2. Context pack, memory strategy, deterministic tool, and structured-output contract docs/tests.
3. Local gate contract skeleton.
4. Local gate dry-run with deterministic rules only.
5. Optional local Gemma classifier experiments after golden-set quality bars exist.
6. External tier contracts.
7. One external provider smoke implementation at a time.
8. Review and hardening after each provider.
9. Supervisor route-plan audit envelope.
10. Limited Supervisor routing only after all earlier gates are stable.

## 12. What To Avoid Next

Do not move next into:

- Gemma runtime.
- Ollama, LiteLLM, or model-server integration.
- Local gate runtime contracts.
- `AIProviderTier` implementation by itself.
- External provider implementation.
- Provider routing.
- Chat UI.
- Memory runtime.
- File ingestion.
- BlueRev modeling assistant behavior.
- Agent or MCP integration.

## 13. Recommended Next Codex Task

After D7, the next Codex task should be:

```text
0E-D8 - Local Gemma Runtime Adapter Dry Run
```

It should feed local Gemma outputs into the D7 evaluation contract. It should not add chat, external APIs, UI, provider routing, memory runtime, local gate enforcement, or BlueRev modeling.

## 14. Readiness Assessment

Gemma runtime adapter dry run: ready as the next bounded step, provided it uses the D7 scorer and remains evaluation-only.

Local Gemma evaluation harness: implemented as the D7 foundation.

Local gate contracts: not ready. They should follow the evaluation harness and context/tool contract work.

External provider implementation: not ready. Existing provider smoke paths are enough for now.

Supervisor routing: not ready. The current Supervisor public-test endpoint should remain narrow.

BlueRev modeling: not ready for AI expansion. Keep BlueRev-sensitive content out of smoke prompts and provider paths.

## 15. Final Recommendation

JarvisOS should proceed to `0E-D8 - Local Gemma Runtime Adapter Dry Run`.

D6D should be treated as the alignment checkpoint that froze the direction: local evaluation first, local runtime dry run second, local gates later, external tiers later, and provider routing last.

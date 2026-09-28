# PRE-155 architecture check — intelligence per euro under a hard IP boundary

Date 2026-09-28. Coordinator: Claude (Opus). Inputs:

- four read-only research lanes (web + code), kept on the operator machine under `jarvis-control/work/evidence/pre155/research/`: `route.md` (cascades, routing, lab practice), `priv.md` (privacy-preserving offload, sanitization), `ctrl.md` (decision controllers / System-1) and `map.md` (JarvisOS code gap table at e5307dd6);
- the PRE-155 local qualification (`evidence/pre155/e4/FINAL-S1-MATRIX.md`);
- the direct-control experiment (`evidence/pre155/e5/RESULT.md`);
- live 154b/154c acceptance.

Outcome: [154b](../specs/154b-local-responder-default.md) and [154c](../specs/154c-privacy-fail-closed-default.md) merged; governed cloud escalation recorded as planned 156, behind 155.

## Verdict on the working hypothesis

| Element | Verdict | Evidence / change |
|---|---|---|
| Jarvis = sovereign state, memory, policy, tool authority, execution, routing | **SUPPORTED** | Matches CaMeL/FIDES/IFC and every lab pattern found; already true in code (broker grants, relay rejects non-local routes, cloud output never executes). |
| Gemma 4 12B QAT default local executor, thinking off, relay repair; Qwen3.5-4B fallback | **SUPPORTED → DONE (154b)** | +7 tasks over 4B responders (2x noise), 0 malformed with repair. Live: Sidecar 17 s, Hermes promoted a broker tool and answered from it. |
| Cloud as elastic reasoning via cascade local → cheapest adequate → stronger → frontier | **SUPPORTED** (H1) | FrugalGPT/AutoMix/RouteLLM/Switchcraft; production: GPT-5 router, Copilot Auto, Cursor Router, Foundry. Gains are workload-specific; static routers collapse out of distribution on agentic coding (ACRouter: 8.9–21 % OOD). |
| Objective max E[U] − λ·cost − μ·latency s.t. constraints | **MODIFY** (H2) | Don't use a single scalar. Hard gates first (privacy, authority, budget), then a per-task quality floor and latency SLO, then the cheapest expected € per *verified* success. Privacy is never a weight. |
| Router = deterministic policy + cheap learned/historical difficulty + verifier escalation | **SUPPORTED** (H3), learned part **DEFER** | Start with deterministic eligibility/budgets plus objective-verifier escalation (tests, schema, unit/balance checks). Add a local task-family success predictor only after Jarvis has verified traces and it beats always-local on held-out tasks. |
| Cloud planner + local executor for hard tasks (Minions-style) | **DEFER** (H4) | Minions: 5.7x cheaper at 97.9 % quality on long-document QA, but the planner sees task structure and can pull detail. Needs a vetted derivative contract and Jarvis-specific evaluation first. |
| Privacy class is a hard pre-dispatch boundary | **SUPPORTED** (P1); **MODIFY NOW** in code → 154c | Model judgement is not a control (ConfAIde: 39–57 % contextual disclosure). The existing 059 spine is real, but new/missing/unrecognised settings default to `FAST_DEV`, where unmarked proprietary prose becomes S1. 154c makes `STRICT_IP` the default. |
| Deterministic projection; an LLM may *propose* derivatives but a deterministic validator gates egress | **SUPPORTED** (P2) | Secret scanners: gitleaks recall 86–88 %, trufflehog 31–52 %; LLM redactors are task-specific. The existing 059 sanitizer and derivative design already follows this. |
| Taint/provenance on data items; record the exact egressed derivative and its recipient | **SUPPORTED** (P3), mostly **EXISTS** | 059b/077 packets record the digest, provider/model and derivative lineage. Item-level propagation for new 155 flowsheet data: defer until 155 needs it. |
| Sanitized derivatives preserve enough engineering reasoning | **CONDITIONAL** (P4) | Yes when identifiers and values are incidental (explanation, dimensional analysis, debugging with a minimal reproducer). No when the value *is* the answer (exact geometry, recipe, threshold, fault signature). No published industrial-IP utility-vs-reidentification benchmark was found. |
| Cloud/tool outputs are data, never authority | **SUPPORTED** (P5), **EXISTS** | Broker-mediated execution; untrusted-tool-result wrapping in Hermes. |
| System-1 as advisory prose | **REJECT** (C1) | Failed to beat placebo; a perturbation cost 2–3 engineering tasks. |
| System-1 as a controller applying bounded decisions | **REJECTED for now, DEFER** (C2–C4) | Literature shows the shape (Toolken+ reject option, RAG-MCP top-K, LLMCompiler) but no frozen-model win. Measured here (e5, Gemma, 23 Hermes tasks, paired): baseline 15/14/14; controller-applied same-model logits 14/14 (net −1, 0), wrong-tool 29–42 % vs 0–5 %, 2–3x dispatches, p95 53–235 s vs 17–36 s. Pre-registered rejection rule met. A future controller needs Jarvis-specific training data. |

## Answers A–I

**A.** Yes. "Local sovereign executor + policy-gated cloud reasoning" is the dominant shape in current practice: Apple on-device + PCC, Copilot/Cursor/Foundry routers with eligibility policies, Minions/PAPILLON local-cloud research. The part the evidence does *not* support is automatic, frequent escalation of *unclassified* context. Frequency should follow classification coverage, not the other way round.

**B.** Minimize €/task with these levers, in order of evidence strength:
1. Solve locally what Gemma solves; Qwen4 for latency-bound simple work.
2. Retrieve and summarize locally; send one stable, minimal derivative.
3. Reuse stable prompt prefixes (cached input is 50–90 % cheaper), but only where caching is policy-cleared.
4. Use objective-verifier escalation instead of confidence guesses.
5. Keep outputs concise.
6. Use Batch for asynchronous cleared work.
7. Measure € per *verified success*, including retries and failed first attempts.

Do not add a learned router, semantic-entropy sampling or cloud prompt compression before Jarvis traces justify them.

**C.** Apply hard filters, then floors, then cost:
1. Hard filters: privacy class and derivative approval, provider allowlist, authority, remaining budget.
2. Floors: drop models below the task-family quality floor or latency SLO. Quality scores come from Jarvis's own evaluations; unknown stays unknown.
3. Choose the minimum expected € per verified success, or a user-selected quality/latency mode.
4. Show the chosen model, cost, cache use and escalation reason.

**D.** Stays local even when cloud would be smarter:
- raw strategic designs, recipes and exact topology/geometry/parameters/tolerances that carry the differentiator;
- private repositories and broad code context;
- credentials, and local infrastructure/security detail;
- unreleased simulation datasets and traceable run histories;
- memory, policy, grants and canonical state;
- anything whose mere use reveals a confidential project;
- embeddings of any of the above.

**E.** Normally exposed: one task statement; only the relevant derived facts; units, boundary conditions, constraints and uncertainty; a short isolated or synthetic fragment where code is needed; the requested output schema. Everything else is excluded unless independently authorized: history, unrelated files, memory, raw tool results, paths/names, telemetry, cached content.

**F.** Sometimes, and it is task-specific (see P4). If the projection destroys the needed signal, stay local or ask the user. Never silently widen the derivative.

**G.** Routing ownership splits three ways:
- **Deterministic Jarvis policy owns eligibility** (privacy, credentials, providers, budget, authority).
- A cheap local difficulty/history signal may *recommend* among allowed models, once measured.
- Objective verifiers trigger escalation.

Gemma must never decide whether data may leave or whether money may be spent.

**H.** Missing today, per the code map:
1. Fail-closed default for unclassified prompts (**fixed by 154c**).
2. A configurable model catalog with task-family quality/price/latency tiers. Current costs are hard-coded for two route classes, and escalation always targets `external:reasoning`.
3. Verified-outcome logging per task family (the routing evaluation corpus).
4. A cached sanitized context bundle reused across calls.
5. A governed cloud-escalation affordance in the Sidecar/Hermes path (chat is local-only today).
6. Cache-aware session boundaries.

**I.** Split for spec 155:
- **Done in pre-155:**
  - 154b (Gemma default, thinking control, relay repair, crash recovery with the #726 fix);
  - 154c (fail-closed default; the operator machine is on `STRICT_IP`);
  - the one bounded direct-control experiment (rejected; neural System-1 deferred).
- **After 155, as one "governed cloud escalation / intelligence-per-euro" slice (planned 156):**
  - a configurable tier catalog with budgets and quality floors;
  - one-step verifier- or user-triggered escalation from Sidecar/Hermes through the existing 059 spine, under `STRICT_IP` with ask-user classification;
  - outcome/cost logging.
- **Later, trace-gated:** a local task-family success predictor, Minions-style decomposition, item-level taint for 155 data, and engineering-projection evaluations with re-identification tests.

## Why cloud chat escalation is not in pre-155

The research favours small routing changes before 155 and warns that routing decisions need Jarvis's own traces (`route.md` NOW/DEFER). The code map shows chat is local-only by contract (152), so adding cloud to it is a new product surface on the egress boundary. It deserves its own accepted slice. The safety precondition, fail-closed classification, lands now in 154c, so that slice starts from a safe default.

## Live acceptance (operator machine, one-click launcher, master 1ab5f76f)

- Gemma 4 12B QAT Q4_0 from the ext4 copy: ready in 41 s, thinking off, 7.9 GB VRAM of 12 GB.
  - Sidecar direct answer: 17 s.
  - Hermes turn: proposed `jarvis_retrieval_query`, which was promoted, run through the Jarvis broker, and answered from its result.
- `kill -9` of llama-server: `LLAMACPP_RECOVERING` after 2 s, model serving again after 12 s, and the next Sidecar turn answered. The first attempt found the gap fixed in #726: recovery waited for a request that the UI never sends to an unavailable route.
- Qwen3.5-4B fallback via a configuration switch: ready in 7 s, 3.4 GB; direct turn 4.4 s; Hermes tool turn 65 s.
- Model files on `/mnt/d` (DrvFs) can stall a load for over 15 minutes. The operator configuration uses sha-verified ext4 copies.

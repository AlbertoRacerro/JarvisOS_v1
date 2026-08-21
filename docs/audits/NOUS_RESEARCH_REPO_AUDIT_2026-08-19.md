# Nous Research repository audit — 2026-08-19

Status: supporting audit evidence; **not implementation authority**  
Canonical intake register: `docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`

This document records a code-first audit of public repositories visible under the `NousResearch` GitHub organization. Its main purpose is to distinguish **Nous-authored projects** from third-party projects merely forked into the organization, and to preserve the concrete mechanisms that may be useful to JarvisOS / BLUECAD / BlueRev.

No finding in this file authorizes implementation. `docs/specs/STATUS.md` remains the sole live authority for specification state and queue order.

## Provenance rule: org membership != authorship

Before attributing a mechanism to Nous Research, inspect GitHub repository metadata for `fork`, `parent`, and `source`. During this audit, several apparently relevant repositories were confirmed to be direct forks and therefore should be credited/studied at their upstream source instead:

- `NousResearch/agent-governance-toolkit` -> `microsoft/agent-governance-toolkit`;
- `NousResearch/OpenShell` -> `NVIDIA/OpenShell`;
- `NousResearch/NemoClaw` -> `NVIDIA/NemoClaw`;
- `NousResearch/Gym` -> `NVIDIA-NeMo/Gym`;
- `NousResearch/Automodel` -> `NVIDIA-NeMo/Automodel`;
- `NousResearch/RL` -> `NVIDIA-NeMo/RL`;
- `NousResearch/pico` -> `HLC-Lab/pico`;
- `NousResearch/speculators` -> `vllm-project/speculators`.

The same check should be repeated for any future Nous-org repository before treating it as a Nous innovation.

---

## NR-01 — `NousResearch/hermes-agent`

**Evidence:** CODE-FIRST  
**Reference value:** S  
**Disposition:** candidate reference; already represented in the canonical register as REF-022.

The upstream Nous repository itself was inspected, not only downstream forks.

### Progressive authorized tool disclosure

Hermes replaces large MCP/plugin schema catalogs with `tool_search`, `tool_describe`, and `tool_call`, while keeping core/session-surface tools direct. Disclosure degrades from short descriptions -> names-only -> per-server summaries as context cost grows. The deferred catalog is rebuilt from the current live registry rather than being trusted from stale session state.

The bridge does **not** create new authority: underlying calls still pass through the normal guardrails, approval flow, hooks, result handling and current session toolset scope.

### Conflict-aware execution

Hermes partitions batches into ordered sequential/parallel segments instead of assuming that simultaneous model-emitted calls commute. Filesystem operations reserve canonical paths with reader/writer roles; reader-reader overlap may proceed, while any conflicting writer becomes a barrier.

Candidate generalization for BLUECAD:

`resource scope + read/write role + dependency semantics -> safe execution plan`.

### Fail-closed arguments, checkpoints and persistence

Malformed/non-object tool arguments are not repaired and then executed. File mutations receive checkpoints on the resolved workspace path. Tool progress is flushed to durable session state after side effects so a restart/termination cannot erase what already happened.

### Large-result spillover

Large tool outputs are persisted outside active model context, leaving a preview + readable reference. An aggregate per-turn budget also spills remaining large results. This is directly relevant to compiler output, repository search, CFD/FEM logs, solver traces and large engineering reports.

Current upstream license checked during this audit: MIT.

---

## NR-02 — `NousResearch/hermes-toolperf-evals`

**Evidence:** CODE-FIRST  
**Reference value:** S  
**Disposition:** candidate.

This is one of the strongest Nous-specific references found. It treats **tool ergonomics as an empirical systems problem**.

The project mined a very large corpus of Hermes session messages, linked tool results back to calls, normalized failure classes and measured concrete forms of waste such as retries, exact duplicate calls, fallback shell commands, truncation/re-read loops, context bytes and common tool-specific errors. Pain points were then converted into isolated runtime changes and tested baseline-vs-fix on deliberately hard cases.

Examples documented by the project include terminal `cd` boilerplate, read-file truncation/re-read churn, Python environment mismatch, patch ambiguity, zero-match searches, process polling, huge skill output, timeout behavior, duplicate calls and write->read verification waste.

### JarvisOS requirement candidate

Every significant capability should eventually emit structured execution telemetry sufficient for offline analysis, for example:

`tool_call_id, run_id, task_id, capability, model/provider, normalized_error_class, retry_of, duplicate_of, fallback_tool, result_bytes, context_bytes, latency_ms, authorization_outcome, verifier_outcome, recovery_hint_used, terminal_state`.

Use measured traces to improve schemas, defaults, error messages, batching and tool boundaries. A strong model should not be allowed to hide a bad tool interface by repeatedly recovering from it.

---

## NR-03 — `NousResearch/hermes-compression-eval`

**Evidence:** CODE-FIRST  
**Reference value:** S / A+  
**Disposition:** candidate.

The repository contains real fixtures, compressor driver, probes, grader, reports, scrubber and tests. Its core insight is that context compression should be judged by **downstream task survival**, not by summary similarity or token reduction alone.

The canonical grading rubric measures six dimensions:

- accuracy of concrete identifiers/facts;
- awareness of the **current** state rather than a mid-session snapshot;
- artifact trail (files, commands, tool calls, PRs, jobs, etc.);
- completeness;
- continuity: whether a new assistant can continue without re-fetching/re-exploring;
- instruction following.

### JarvisOS / BLUECAD adaptation

A future `ContextSurvivalEval` should construct realistic engineering/coding sessions, compress them, give only the compressed handoff to a fresh agent, and probe whether it can recover:

- exact component/equipment IDs;
- units, assumptions, equations and constraints;
- file/repo/artifact provenance;
- last known-good state and unresolved blockers;
- exact next action;
- decisions that were later reverted or superseded.

Compression may optimize representation; it must not silently destroy execution continuity.

---

## NR-04 — `NousResearch/hermes-agent-self-evolution`

**Evidence:** CODE-FIRST  
**Reference value:** A concept / B+ implementation maturity  
**Disposition:** parked candidate; do not treat as production self-modification.

The project separates candidate artifacts, structural hard constraints and multi-dimensional fitness. It can generate/evolve skills from synthetic, golden or session-derived data and evaluate baseline vs evolved variants on holdout data.

Important caveat discovered by following the real execution path: although `constraints.py` defines a full Hermes test-suite runner and `--run-tests` is represented in configuration, the audited `evolve_skill.py` flow does **not** invoke that full suite. The produced skill is validated structurally and against a proxy/holdout evaluation, then written to output for review. The inspected flow does not automatically patch Hermes or create a real PR. The `evolution/code/` area was effectively unimplemented at audit time.

### Safe adaptation

If JarvisOS ever experiments with self-improvement, require:

`offline candidate generation -> immutable baseline -> hard structural/policy constraints -> mandatory deterministic test/verifier suite -> holdout benchmark -> diff/evidence package -> explicit human review -> normal spec/PR promotion`.

Never allow live authority-bearing code/policy to rewrite itself directly.

---

## NR-05 — `NousResearch/autoreason`

**Evidence:** CODE-FIRST  
**Reference value:** A  
**Disposition:** candidate for subjective refinement only.

The real v2 runner implements an incumbent-preserving refinement loop:

1. A = current incumbent;
2. critic identifies weaknesses;
3. B = revision;
4. AB = synthesis of A+B;
5. each judge receives an independently randomized presentation order;
6. rankings are aggregated with Borda-style scoring;
7. ties favor incumbent A;
8. unchanged A is therefore a first-class candidate;
9. convergence occurs after repeated incumbent wins.

### JarvisOS use

This is useful for prompts, specifications, design narratives, reports and other partially subjective artifacts where blindly rewriting each iteration causes drift.

Candidate rule:

`promote challenger only if it beats incumbent under a stable rubric`.

Do **not** replace deterministic engineering verification, tests or solver truth with LLM voting.

---

## NR-06 — `NousResearch/nomos`

**Evidence:** CODE-FIRST  
**Reference value:** A- / B+  
**Disposition:** parked candidate.

Nomos is a reasoning harness that launches many candidate solution workers, prioritizes problems with the weakest current score/evidence, and later consolidates submissions before a pairwise tournament.

The reusable idea is **adaptive compute allocation**, not generic multi-agent voting:

`confidence/evidence deficit -> additional reasoning or verification budget`.

For JarvisOS/BLUECAD, high-confidence deterministically verified work should not consume the same reasoning budget as contradictory or under-verified work. Combine this concept with claim/evidence confidence rather than self-grader scores alone.

---

## NR-07 — `NousResearch/hermes-paperclip-adapter`

**Evidence:** CODE/DOCS inspected  
**Reference value:** B+ / A-  
**Disposition:** supporting reference.

The adapter treats Hermes as a worker managed by an external orchestrator. Useful contract fields include `agentId`, `runId`, `taskId`, `wakeReason`, allowed toolsets, timeout, workspace/worktree mode, checkpoint flag, model/provider and persistent session state.

It captures stdout/stderr, token/cost/session identity, parses structured transcript entries and validates/migrates session state between heartbeat runs.

Candidate future JarvisOS worker-adapter contract:

`run identity + task identity + wake reason + exact scope/toolsets + workspace isolation + session codec + usage/cost + structured transcript + terminal outcome`.

This overlaps with stronger NexusAI / bug-hunter / Hermes-core patterns and therefore does not require a separate orchestration architecture.

---

## NR-08 — `NousResearch/Hermes-Function-Calling`

**Evidence:** CODE-FIRST  
**Reference value:** B historical  
**Disposition:** superseded by modern Hermes Agent for authority/runtime design.

This older repository contains function schemas, validators and JSON/function-call examples. Its validator checks function name, required arguments, types and enums, but its JSON-mode parser tries several recovery paths (`json.loads`, `ast.literal_eval`, Markdown JSON extraction).

For authority-bearing calls, prefer the modern Hermes pattern: malformed tool arguments fail closed instead of being repaired into something executable.

---

## NR-09 — `NousResearch/atropos` + `tinker-atropos`

**Evidence:** CODE/DOCS inspected  
**Reference value:** A concept  
**Disposition:** parked research reference.

Atropos defined RL environments as services separate from the trainer/inference engine. Environments collect/evaluate trajectories and can represent dataset tasks, interactive environments, tool calling, code execution, multimodal work and multi-turn behavior.

The repository is now **archived and explicitly no longer maintained**, so it should not become a JarvisOS dependency.

`tinker-atropos` is an original integration layer that demonstrates the architectural benefit of the separation: the same environment/reward definitions can be used while changing the training backend to Thinking Machines' Tinker service.

### Engineering-specialist implication

If a future Jarvis/BLUECAD specialist is trained or reinforced, define the engineering truth independently of the trainer:

`EngineeringEnvironment = task generator + allowed observations/actions + deterministic/primary-source verifier + reward + trajectory record`.

Possible environments: tool selection, flowsheet reasoning, unit consistency, CAD operations, equation solving, solver setup, convergence diagnosis, report evidence attribution. Training infrastructure should remain replaceable.

---

## NR-10 — `NousResearch/neural-steering`

**Evidence:** CODE/DOCS inspected  
**Reference value:** B research  
**Disposition:** parked.

Implements Contrastive Neuron Attribution for discovering sparse MLP neuron circuits and scaling them during inference. It is relevant to interpretability and experimental behavioral steering of local models.

Do not confuse model steering with policy/authorization: changing a model's behavioral circuit can never substitute for typed capability authority, sandboxing, approvals or deterministic verification.

---

## NR-11 — `NousResearch/smc-inference-server`

**Evidence:** CODE/DOCS inspected  
**Reference value:** B research  
**Disposition:** parked.

Runs Sequential Monte Carlo steering behind an API, with vLLM/llamppl and optional multi-GPU worker/load-balancer setup. The useful high-level lesson is that quality/control can improve through **inference-time search/steering** rather than only larger base models.

The current implementation is primarily multi-GPU/vLLM oriented and is not a ready consumer-laptop solution.

---

## NR-12 — `NousResearch/DisTrO`

**Evidence:** repository metadata / project scope  
**Reference value:** B future research  
**Disposition:** parked.

Original Nous project for distributed training over the Internet. Potential relevance is long-term decentralized/local-AI sovereignty and use of geographically distributed compute, not current JarvisOS execution architecture.

---

## Lower-priority / historical observations

- `NousResearch/nousflash-agents`: real but older social-agent pipeline combining retrieval, short/long memory, reply/follow/post and wallet behavior. It lacks the modern authority separation of Hermes and is useful mainly as historical evidence of architectural evolution.
- `NousResearch/Obsidian`: older vision-model research; low relevance to the current agent-runtime audit.
- `NousResearch/Open-Reasoning-Tasks`: useful reasoning-task corpus/taxonomy, not an execution architecture.
- `NousResearch/hermes-example-plugins`: reference implementations for Hermes plugin lifecycle; revisit when a concrete plugin ABI/spec is active.
- `NousResearch/tinker-atropos`: useful chiefly as evidence that environment/reward definitions can remain portable across training backends.

---

# Cross-repository synthesis

The strongest Nous-specific lesson is not one isolated feature. Their more interesting original projects form a feedback loop around the agent/runtime:

```text
Hermes Agent runtime
      |
      +--> structured execution traces
      |        |
      |        v
      |   Tool-performance mining
      |        |
      |        v
      |   measured runtime/tool improvements
      |
      +--> long-session compression
      |        |
      |        v
      |   downstream context-survival probes
      |
      +--> candidate prompt/skill refinement
      |        |
      |        v
      |   incumbent comparison + holdout/evidence
      |
      +--> difficult/uncertain task
               |
               v
          allocate more inference/reasoning budget
```

A JarvisOS analogue should therefore prioritize **instrumented improvement**:

1. runtime operations produce typed telemetry and verifier outcomes;
2. offline analytics identify systematic waste/failures;
3. changes are tested baseline-vs-candidate;
4. context compression is tested by continuation ability;
5. subjective refinements must beat an explicit incumbent;
6. uncertain tasks receive extra compute/verification, not every task;
7. any learned/evolved artifact enters normal review/promotion rather than self-installing.

For future model specialization, keep a second, separate loop:

`engineering environment/reward -> replaceable training backend -> specialist model -> deterministic engineering eval -> only then eligible for JarvisOS routing`.

# JarvisOS Executive Brief for Fable

## Purpose

This pack is for a high-cost frontier-model review of JarvisOS strategy. It is
not a code dump. It is meant to help Fable 5 evaluate architecture, sequencing,
model economy, memory, agent design, tooling, and computational engineering
direction with minimal token waste.

## One-Sentence Thesis

JarvisOS is an AI-native technical operating system for engineering, research,
and technology creation: local-first, policy-gated, traceable, cost-aware, and
designed to turn project knowledge, simulations, tools, and models into durable
engineering model capital.

## Strategic Position

JarvisOS is not trying to become a generic chatbot. The intended product is a
technical workbench that owns:

| Layer | JarvisOS role |
| --- | --- |
| State | Durable workspaces, entities, assumptions, parameters, decisions, artifacts, runs |
| Policy | Sensitivity, routing, budget, provider, tool, and state-change gates |
| Execution | Local runner, local model routes, guarded external provider routes |
| Audit | Ledgers, digests, metadata, source manifests, reproducible run records |
| Intelligence | Local semantic classification, bounded context assembly, future external escalation |
| Workflow | Engineering, research, simulation, model management, and future agent orchestration |

The core design principle is:

> AI models propose. JarvisOS validates, gates, records, executes, and audits.

## Current State Snapshot

As of HEAD `a6a7bc4 Add backend architecture handout with prioritized-direction notes`, JarvisOS has a working backend-led architecture with:

- FastAPI backend and React/Vite frontend.
- SQLite-backed local runtime state under `C:\JarvisOS`.
- Domain Foundation for project knowledge.
- Local Python Runner V0 for bounded simulation runs.
- AI execution spine through `run_ai_task` and `ai_jobs`.
- Frontend AI console for `/ai/tasks/run`.
- Local Ollama adapter and route bindings for multiple installed local models.
- Auto route bridge that is local-only and policy-gated.
- RouterPolicy canonicalized into backend runtime with root script shim.
- Context levels and route-aware context budgets.
- Docs-only external reference audit for semantic routing patterns.

## Current Strategic Advantage

JarvisOS has already made several high-leverage decisions that should be kept:

- It separates semantic classification from execution authority.
- It treats local models as useful but non-authoritative.
- It keeps cloud execution explicit and gated.
- It records AI calls in `ai_jobs`.
- It preserves manual context blocks even when project-context retrieval is off.
- It has a computational workspace direction rather than a chat-only direction.
- It frames memory as staged evidence and retrieval, not instant model belief.

This is the right foundation for a "real-world Jarvis" because it avoids the
fragile pattern where a model directly owns memory, tools, external calls, and
project state.

## Highest-Risk Design Areas

| Area | Current risk | Why it matters |
| --- | --- | --- |
| Retrieval | Project context is budgeted, but source selection is not intelligent yet | Large workspaces will need precise source choice |
| Local model ceiling | Local models may be too weak for deep reasoning | Needs graceful escalation without exfiltration |
| External escalation | Cloud routes exist but Auto must not execute external yet | Requires redaction, confirmation, and provider registry |
| Memory | Staged memory design exists, runtime is incomplete | Poor memory can poison future decisions |
| Agents | Registry skeletons exist, orchestration is not built | Agents need permissions, scope, and ledgers before autonomy |
| Tooling | Runner is bounded, broader tool layer is future | Tool execution is where safety failures become real-world effects |
| Evaluation | Tests cover safety behavior, not enough outcome quality | Routing needs success signals before adaptive optimization |

## What Is Intentionally Not Built Yet

JarvisOS intentionally does not yet provide:

- Autonomous background agents.
- External Auto execution.
- Redact-then-external workflows.
- Semantic/vector retrieval.
- Memory promotion runtime.
- Tool-calling agent loop.
- Browser/MCP tool execution from the AI spine.
- Streaming AI responses.
- Model grading or adaptive bandit routing.
- Full BlueRev engineering co-pilot behavior.
- Multi-node local inference scheduling.

These are deferred because the current priority is a safe, inspectable local
spine before adding autonomy.

## Review Goals for Fable

Fable should evaluate:

1. Whether the architecture can scale into a technical operating system without
   becoming a brittle chatbot wrapper.
2. Whether the routing/model-economy design is efficient and safe enough.
3. Whether memory/context should remain staged and deterministic before semantic
   retrieval is added.
4. Whether the agent swarm target is correctly sequenced after tool policy and
   ledgers.
5. Whether computational engineering workflows are the right center of gravity.
6. Which next milestones maximize compounding value without weakening safety.

## Recommended Next Strategic Sequence

| Priority | Milestone direction | Rationale |
| --- | --- | --- |
| 1 | Local runtime smoke and reliability hardening | Auto now depends on real local routes |
| 2 | Sensitivity and redaction design | Required before any external escalation |
| 3 | Context source selection | Current context_level is budget/posture only |
| 4 | Evaluation and success signals | Required before adaptive/economic routing |
| 5 | Tool policy and execution ledger | Required before useful agents |
| 6 | Agent swarm orchestration | Only after tools, memory, and policy are strong |

## Decision Rubric for Fable

Fable should judge every proposed next step against these questions:

| Question | Good answer | Bad answer |
| --- | --- | --- |
| Does it strengthen durable state? | Adds explicit records, provenance, or ledgers | Hides more state in prompts |
| Does it preserve policy authority? | Model output remains advisory or gated | Model decides permissions directly |
| Does it reduce cost or risk? | Uses local/fake/default routes until escalation is justified | Makes cloud/default behavior easier by accident |
| Does it improve engineering workflows? | Helps models, simulations, decisions, artifacts, or evidence | Adds generic chat features only |
| Is it testable offline? | Has deterministic or stubbed tests | Requires live provider calls for correctness |
| Is it reversible? | Adds narrow surfaces and ledgers | Adds broad autonomy without rollback |

The best next milestones are those that increase real engineering utility while
making the system easier to inspect. Avoid milestones that merely make the UI
feel more agentic while skipping state, memory, tool, or safety foundations.

## Current Product Identity

JarvisOS should present itself as:

- A local-first technical workbench.
- A policy-gated AI execution system.
- A future computational engineering operating system.
- A model-capital and evidence-management platform.

It should not present itself as:

- A general companion chatbot.
- A generic API router.
- An autonomous agent framework.
- A cloud-first AI dashboard.
- A memory product whose main asset is model-written summaries.

This positioning matters because it determines roadmap pressure. Chat products
optimize smooth conversation. JarvisOS should optimize durable technical work:
what was assumed, what was tested, what changed, what was decided, which model
or tool acted, which context was used, and why a provider or action was allowed.

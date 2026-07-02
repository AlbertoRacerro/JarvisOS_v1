# JarvisOS Agent Swarm Target

## Current State

JarvisOS does not yet have an operational agent swarm. Current backend agent and
tool modules are minimal registries/protocols. This is good: the execution and
policy spine is being built before autonomy.

Current skeletons:

| Area | Status |
| --- | --- |
| Agent registry | Minimal dataclass registry with names/capabilities |
| Tool registry | Minimal tool protocol and registry |
| Runner | Bounded local Python execution for a narrow modeling use case |
| AI task spine | Implemented with ledgers and route classes |
| Auto route | Local-only, policy-gated |
| Memory runtime | Not yet implemented |
| Autonomous loops | Not built |

## Target Swarm Model

The long-term design should be a supervised technical swarm, not a free-running
agent cloud.

Recommended role split:

| Agent role | Responsibility | Execution authority |
| --- | --- | --- |
| Router/triage agent | Classify request, choose capability/context posture | Advisory only |
| Research agent | Gather and summarize approved local/external evidence | Read-only unless explicitly authorized |
| Memory curator | Propose memory intake/promotions/conflict notes | No direct canonical writes |
| Simulation planner | Propose model specs, parameters, run plans | No execution without runner gate |
| Code analyst | Inspect code, suggest patches/tests | No writes unless Codex/operator approves |
| Tool executor | Execute approved tools under policy | Narrow, logged, reversible where possible |
| Reviewer/critic | Check assumptions, safety, tests, and scope creep | Advisory, can block by policy |
| Orchestrator | Sequence subtasks and handoffs | No provider/tool bypass |

The swarm should be a graph of bounded workers connected by ledgers and policy
gates, not a single prompt with hidden authority.

## Non-Negotiable Agent Invariants

| Invariant | Reason |
| --- | --- |
| No hidden external calls | Protects IP, cost, and privacy |
| No direct DB writes from agents | Preserves memory/state integrity |
| No tool execution without policy gate | Prevents real-world side effects |
| No model-owned permission decisions | Keeps deterministic safety boundary |
| Every run has a ledger record | Enables audit and rollback |
| Context provenance is visible | Prevents unverifiable summaries |
| Agent outputs are proposals unless promoted | Avoids model hallucinations becoming state |

## Execution Architecture Target

Future agent execution should likely use this flow:

1. User asks for a task.
2. RouterPolicy and task classifier produce a bounded plan proposal.
3. Orchestrator creates one or more agent jobs.
4. Each job receives a scoped context bundle.
5. Each job returns structured output with evidence.
6. Tool requests become separate policy-gated operations.
7. Memory writes become separate proposed-memory records.
8. Human or deterministic policy approves promotion/execution where needed.
9. Final answer summarizes work and references ledgers/artifacts.

This design keeps agents useful while avoiding opaque autonomy.

## Agent Swarm Dependencies

Agent swarm work should wait for:

| Dependency | Why |
| --- | --- |
| Tool policy contract | Agents need executable boundaries |
| MemoryStore facade | Agents need safe memory proposals |
| Source selection | Agents need useful, bounded context |
| Evaluation signals | Agent routing needs outcome feedback |
| Control-state ledgering | Non-executing states need audit |
| External redaction/confirmation | Research agents may need cloud/search later |
| Role schemas | Agent outputs must be typed and testable |

Without these, an agent swarm would become a brittle prompt orchestration layer.

## Recommended First Agent Slice

The first practical agent slice should be read-only and local:

| Slice | Details |
| --- | --- |
| Name | `AGENT-READONLY-0` |
| Scope | Plan-and-review agent over local project context |
| Model route | Auto/local only |
| Tools | None, or read-only repository/context inspection through existing backend-owned APIs |
| Memory writes | Proposed only, no promotion |
| Output | Structured plan, risks, required approvals |
| Ledger | Agent job record plus source manifest |

This would test orchestration and context without introducing dangerous tool
execution.

## What Not To Build Yet

Do not build these before the prerequisites:

- Autonomous background task loop.
- Self-scheduling agents.
- Agent-to-agent hidden message bus.
- Direct MCP/browser/shell execution.
- External search/provider calls from agents.
- Memory writes without review.
- Long-running workers with unclear cancellation.
- "Manager agent" with implicit authority.

## Fable Review Questions

1. Is the proposed role split sufficient for a technical OS?
2. Should agent jobs be stored in `ai_jobs`, a new ledger, or both?
3. What is the minimal safe tool contract before agents execute anything?
4. How should JarvisOS score agent success without a grading model becoming
   authority?
5. Which agent should be first: reviewer, memory curator, simulation planner, or
   code analyst?

## Maturity Levels

| Level | Description | JarvisOS readiness |
| --- | --- | --- |
| L0 | Single AI response through route spine | Implemented |
| L1 | Read-only planner/reviewer agent | Near-term candidate |
| L2 | Agent proposes memory/tool actions for approval | Requires MemoryStore/tool contract |
| L3 | Agent executes low-risk read-only tools | Requires tool ledger and policy |
| L4 | Agent executes reversible state changes | Requires approval, rollback, audit |
| L5 | Multi-agent durable workflow | Requires job orchestration and observability |
| L6 | Background autonomy | Not ready |

This maturity ladder is useful because it prevents the project from jumping
from "AI console" directly to "agent swarm" without the intermediate governance
layers.

## Agent Data Model Sketch

A future agent job record should probably include:

- Agent role.
- Triggering user request or parent job.
- Workspace id.
- Route/model used.
- Context pack digest and source manifest.
- Tool permissions granted.
- Proposed tool calls.
- Proposed memory writes.
- Output schema version.
- Review status.
- Error/control state.
- Cost and latency metadata.

This should be designed before broad agents are implemented. Otherwise agent
outputs will become hard to audit and impossible to compare.

## Safe First Agent Recommendation

The strongest first candidate is a reviewer/critic agent because it can create
value without acting:

- It can inspect a task plan.
- It can identify missing tests.
- It can flag policy or scope risk.
- It can ask for narrower context.
- It can produce a structured review ledger.

Avoid starting with executor agents. Execution is where incomplete policy
contracts become real system risk.

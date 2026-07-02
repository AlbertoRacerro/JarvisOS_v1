# Fable Review Index

## Review Pack Purpose

This directory is a compact review pack for an expensive Fable 5 strategic
review. It intentionally avoids code dumps and full test logs.

## Files

| File | Purpose |
| --- | --- |
| `JARVISOS_EXECUTIVE_BRIEF_FOR_FABLE.md` | One-pass strategic summary |
| `JARVISOS_CURRENT_ARCHITECTURE.md` | Current subsystem architecture |
| `JARVISOS_AI_ROUTING_AND_MODEL_ECONOMY.md` | Route bindings, Auto, model economy, context budgets |
| `JARVISOS_MEMORY_CONTEXT_DESIGN.md` | Current context behavior and staged memory direction |
| `JARVISOS_AGENT_SWARM_TARGET.md` | Future agent swarm shape and boundaries |
| `JARVISOS_COMPUTATIONAL_ENGINEERING_WORKSPACE.md` | Modeling, runner, BlueRev, engineering model capital |
| `JARVISOS_TOOLING_ROADMAP.md` | Tool policy and execution roadmap |
| `JARVISOS_RECENT_MILESTONES.md` | Recent commit timeline and milestone interpretation |
| `JARVISOS_OPEN_QUESTIONS_FOR_FABLE.md` | Targeted questions for Fable |

## Suggested Read Order

1. `JARVISOS_EXECUTIVE_BRIEF_FOR_FABLE.md`
2. `JARVISOS_CURRENT_ARCHITECTURE.md`
3. `JARVISOS_AI_ROUTING_AND_MODEL_ECONOMY.md`
4. `JARVISOS_MEMORY_CONTEXT_DESIGN.md`
5. `JARVISOS_OPEN_QUESTIONS_FOR_FABLE.md`
6. Remaining domain-specific files as needed.

## Source Material Used

Primary repository sources:

| Source | Used for |
| --- | --- |
| `README.md` | Product thesis, current stack, local-first direction |
| `docs/ARCHITECTURE.md` | Backend/frontend/state/policy architecture |
| `docs/HANDOUT_BACKEND_ARCHITECTURE.md` | Current backend handout and priority notes |
| `docs/routing/ROUTER_MATRIX_0_DESIGN.md` | Routing matrix, context levels, reference decisions |
| `docs/reference_audits/semantic-routing-giants.md` | Reference audit conclusions |
| `docs/STAGED_MEMORY_INTAKE.md` | Staged memory lifecycle |
| `docs/MEMORYSTORE_FACADE_DESIGN.md` | Future MemoryStore boundary |
| `docs/SQLITE_FTS_MEMORY_SCHEMA_DESIGN.md` | Future memory schema direction |
| `docs/MICRO_CONTEXT_DESIGN.md` | Micro-context boundary |
| `docs/LOCAL_AI_EVALUATION_EVIDENCE.md` | Local model boundary and evaluation history |
| `backend/app/modules/ai/execution.py` | Route bindings and AI spine defaults |
| `backend/app/modules/ai/routing/bridge.py` | Auto bridge behavior |
| `backend/app/modules/ai/routing/decision.py` | Canonical RouterPolicy producer and local/secret boundary |
| `backend/app/modules/ai/routing/capability_route_matrix.py` | Capability matrix and context budgets |
| `backend/app/modules/local_ai/classification/contracts.py` | Classifier contract and non-authority boundaries |
| `backend/app/modules/runner/safety.py` | Runner safety constraints |
| `backend/app/modules/tools/*` | Current tool skeleton |
| `backend/app/modules/agents/*` | Current agent skeleton |
| `git log --oneline -40` | Recent milestone hashes/messages |

## Review Objectives

Ask Fable to evaluate:

- Whether the architecture can become a real technical OS rather than a chatbot
  wrapper.
- Whether Auto routing is safe, efficient, and correctly sequenced.
- Whether memory/context should remain staged before semantic retrieval.
- Whether the model economy makes good use of local models and guarded cloud.
- Whether agent swarm design is properly delayed until tools/memory/ledgers are
  stronger.
- Whether the computational engineering workspace is the right strategic center.

## Boundaries of This Pack

This pack does not claim:

- External Auto execution is ready.
- Retrieval or memory runtime is implemented.
- Agents or tools are operational.
- Local models are reliable for critical decisions.
- BlueRev modeling is AI-approved.
- Provider routing is fully optimized.
- Fable review has approved any architecture.

This pack is a review input, not a product release note.

## Expected Fable Output

Recommended output from Fable:

1. Architecture risks ranked by severity.
2. Next milestone sequence.
3. Design changes before agents/tools.
4. Memory/retrieval strategy recommendation.
5. Local/external model economy recommendation.
6. Computational engineering workspace critique.
7. Specific questions that require repo/code follow-up.

## Token Economy Notes

This pack intentionally compresses repository history into strategic summaries.
If Fable needs more detail, request only the relevant source file or module,
rather than the full repository.

Suggested escalation:

| If Fable needs | Provide next |
| --- | --- |
| Routing details | `backend/app/modules/ai/routing/*` plus tests |
| AI spine details | `backend/app/modules/ai/execution.py`, gateway/models/routes tests |
| Memory details | Memory design docs and context builder |
| Runner details | Runner service/safety/models/routes and tests |
| UI details | AI console page and API client |
| Milestone evidence | Specific commit diff and test outputs |

The goal is to spend frontier-model tokens on architecture judgment, not on
rediscovering file structure.

## Current-State Caveat

This pack represents the repository state inspected for this slice, not a
guarantee that every historical report remains current. Where recent commits
supersede older docs, prefer current backend code, current route matrix docs,
and current milestone commits. Where a capability is described as future or not
built, Fable should treat that as a boundary, not as an invitation to assume the
runtime already exists. The most important review discipline is to distinguish
four categories: implemented and tested, implemented but needing runtime smoke,
documented design only, and unknown / needs verification.

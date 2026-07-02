# JarvisOS Computational Engineering Workspace

## Strategic Center

JarvisOS should be judged as a computational engineering workspace, not only as
an AI chat shell. The long-term goal is to help users create, test, refine, and
audit technical systems.

The "Tony Stark Jarvis" analogy is useful only if grounded in deterministic
engineering workflow:

- Project knowledge.
- Models and assumptions.
- Simulations.
- Experimental evidence.
- Decisions.
- Code.
- Tools.
- AI reasoning.
- Audit trails.

## Current Workspace Objects

JarvisOS already has foundations for technical work:

| Object | Purpose |
| --- | --- |
| Workspace | Project boundary |
| Entity / EntityLink | Domain graph |
| Event | Timeline or state change evidence |
| Artifact | Files, references, generated outputs |
| ModelSpec | Conceptual model definition |
| Assumption | Explicit uncertain premise |
| Parameter | Named quantity with provenance |
| ModelVersion | Versioned implementation |
| SimulationRun | Execution attempt/result |
| RunnerJob | Local execution lifecycle |
| Decision | Durable reasoning or selection record |
| AISettings | Provider and budget policy |

This is the correct substrate for engineering model capital: state is explicit,
not buried in chat history.

## Modeling Workbench Direction

The Modeling Workbench should become the interface where users:

- Define model specs.
- Link assumptions and parameters.
- Select or generate implementation artifacts.
- Run bounded simulations.
- Compare results.
- Attach evidence.
- Promote conclusions into decisions.

AI can help propose model structures, identify missing assumptions, generate
candidate code, and critique outputs. But JarvisOS should keep model execution,
parameter provenance, and decision promotion explicit.

## Current Runner Capability

The local runner is currently narrow and useful:

| Feature | Current behavior |
| --- | --- |
| Input validation | Canonical finite JSON with size caps |
| Supported model | Batch-growth style parameters are explicitly checked |
| Script boundary | Must live inside workspace model implementation directory |
| Script policy | Blocks network, subprocess, destructive filesystem markers, secrets/env access |
| Run paths | Working/input/output paths constrained under run root |
| Artifacts | Output paths constrained and size-limited |
| Timeout | Bounded |

This is not a general Python automation system. It is the seed of a controlled
computational execution environment.

## BlueRev Relevance

BlueRev is the current flagship domain for computational engineering:

- Microalgae/process modeling.
- Assumptions and parameters.
- Simulation runs.
- Literature values and candidate ranges.
- Design decisions.
- Future model-capital workflows.

However, BlueRev modeling should not outrun the AI/runtime foundation. Prior
docs repeatedly treat local models as advisory and require stronger workbench,
context, and external escalation infrastructure before critical modeling
decisions rely on AI.

## Target Computational Loop

Recommended future loop:

1. Define objective and workspace.
2. Capture assumptions, parameters, constraints, and evidence.
3. Propose a model spec.
4. Generate or attach implementation.
5. Validate implementation policy.
6. Run simulation.
7. Analyze output.
8. Compare against evidence or acceptance criteria.
9. Promote or reject decisions.
10. Record every step as durable model capital.

AI should assist every step, but each state transition should be explicit and
auditable.

## Missing Capabilities

| Missing capability | Importance |
| --- | --- |
| Multi-model comparison UI | Needed for real engineering trade studies |
| Parameter provenance and uncertainty handling | Needed for credible models |
| Calibration/validation workflows | Needed before model outputs become decisions |
| Sensitivity analysis | Needed for engineering insight |
| Artifact lineage | Needed for audit and reproducibility |
| AI-assisted model generation | Useful but must be reviewed |
| External literature/research intake | Requires source, copyright, and sensitivity policy |
| Domain-specific evaluators | Needed to detect wrong-but-plausible outputs |

## Recommended Engineering Roadmap

| Stage | Goal |
| --- | --- |
| `WORKBENCH-0` | Make model specs, assumptions, parameters, decisions ergonomic |
| `RUNNER-1` | Add controlled additional model templates and richer artifact output |
| `MODEL-LINEAGE-0` | Link specs, versions, runs, artifacts, and decisions |
| `SIM-EVAL-0` | Add deterministic validation and acceptance criteria |
| `AI-MODEL-ASSIST-0` | Let AI propose model specs/code as reviewable drafts |
| `BLUE-REV-FOUNDRY-0` | Convert BlueRev into a reproducible model-capital workspace |

## Key Strategic Choice

JarvisOS should avoid becoming a shallow UI around LLM calls. The moat is the
computational state machine: explicit knowledge objects, executable models,
audited runs, and policy-gated AI assistance.

## Decision Quality Loop

Engineering value compounds only if decisions can be revisited. JarvisOS should
make every important decision traceable to:

| Decision input | Example |
| --- | --- |
| Objective | What the model/workflow was trying to optimize |
| Assumptions | Physical, economic, biological, software, or hardware premises |
| Parameters | Values, ranges, units, source, and confidence |
| Evidence | Papers, observations, logs, artifacts, simulations |
| Model version | Implementation used for the result |
| Run outputs | Tables, plots, errors, generated artifacts |
| AI contribution | Draft, critique, route/model, context digest |
| Human/policy action | Accepted, rejected, deferred, superseded |

This is where JarvisOS can become more than an assistant: it can become an
engineering memory system with executable provenance.

## Computational Workspace Anti-Patterns

| Anti-pattern | Consequence |
| --- | --- |
| Model outputs written directly into assumptions | Pollutes project truth |
| Simulation runs detached from model versions | Makes results irreproducible |
| Parameter values without units/provenance | Breaks engineering review |
| AI-generated code immediately runnable | Weakens safety and correctness |
| Literature values promoted to measured values | Corrupts design basis |
| Chat-only decision history | Makes audit and rollback impossible |

The workspace should enforce distinctions between candidate, measured,
validated, accepted, and current-design values.

## Frontier-Model Role in Engineering

Fable/frontier models are most useful when:

- Reviewing architecture and assumptions.
- Finding missing variables.
- Critiquing model structure.
- Suggesting experiment/simulation plans.
- Explaining unexpected outputs.
- Comparing alternative designs.

They should not silently become authority for validated engineering facts or
state transitions.

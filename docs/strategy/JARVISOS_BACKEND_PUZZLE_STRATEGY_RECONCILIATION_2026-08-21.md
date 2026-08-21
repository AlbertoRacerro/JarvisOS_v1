# Backend Puzzle Strategy — Relationship to Existing JarvisOS Strategy

Status: **strategy reconciliation only; not implementation authority**  
Prepared: 2026-08-21  
Companion to: `JARVISOS_BACKEND_PUZZLE_STRATEGY_2026-08-21.md`

The backend-puzzle strategy is an evidence-driven continuation of the existing JarvisOS strategy set, not a silent replacement of it.

## Documents that remain valid

### `JARVISOS_CURRENT_ARCHITECTURE.md`

Its core architectural contract remains valid:

- backend-led durable state and policy;
- frontend as operator interface rather than a second source of truth;
- AI models do not own canonical state changes, provider permissions, retrieval authority or tool execution;
- future agents/tools attach through explicit contracts;
- avoid one super-agent and provider-owned policy.

The backend-puzzle strategy preserves these invariants and adds concrete upstream/runtime choices for implementing them.

### `JARVISOS_AI_ROUTING_AND_MODEL_ECONOMY.md`

Its routing doctrine remains valid:

- local/cloud choice is policy-controlled rather than a model-owned fallback;
- classifier output is advisory;
- external escalation is explicit and privacy/cost-aware;
- model/provider identity and usage remain observable.

The new strategy changes the layer **below** that policy: inference engines and local runtime lifecycle become replaceable adapters/control-plane backends instead of accumulating engine-specific Jarvis code.

### BLUECAD strategy documents

`BLUECAD_CORE_DESIGN.md`, `BLUECAD_SEAM_MAP.md`, `BLUECAD_TOOLING_AND_LICENSING.md`, `BLUECAD_CONVERSATIONAL_DESIGN_LAYER.md` and related domain strategy remain the domain reference set. The backend-puzzle strategy does not transfer BLUECAD canonical engineering identity, provenance or verification to generic agent frameworks or external solvers.

## Document whose invariants remain but maturity assumptions are superseded

### `JARVISOS_AGENT_SWARM_TARGET.md`

Keep its safety invariants:

- agents are supervised bounded workers;
- no direct canonical DB writes;
- outputs are proposals unless promoted;
- tool actions require policy;
- no model-owned permission decisions;
- runs require durable identity/evidence;
- context provenance must remain visible.

Update/supersede these earlier maturity assumptions when the future backend puzzle is re-derived:

- "Memory runtime not yet implemented" is obsolete: current JarvisOS has canonical proposal/promotion/replacement/freshness semantics for Assumptions, Parameters and Decisions.
- the minimal `modules/agents` and `modules/tools` registries should not automatically become the production swarm/tool framework merely because they were reserved as skeletons;
- mature upstream AgentRuntime, MCP/tool, sandbox and code-intelligence layers must compete against extending those skeletons;
- the future swarm should be described through runtime/capability/grant/commit contracts, not through a hard-coded list of internally authored agent classes.

## Precedence rule

This reconciliation does **not** give the new strategy implementation authority.

For current behavior and queue state:

1. `docs/specs/STATUS.md` and merged governing specs win;
2. exact runtime/code and tests define what exists;
3. existing strategy documents remain useful where not contradicted by newer exact evidence;
4. `JARVISOS_BACKEND_PUZZLE_STRATEGY_2026-08-21.md` is the consolidated planning map for the later backend-puzzle re-derivation;
5. before implementation, exact-master and upstream state must be revalidated and promoted through normal ADR/spec/readiness gates.

Required product order remains:

`finish current functional queue -> frontend visual identity -> backend puzzle implementation`.

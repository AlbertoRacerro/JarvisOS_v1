# JarvisOS / BLUECAD / BlueRev idea intake and candidate-integration register

Status: canonical intake register; **not implementation authority**  
Created: 2026-08-19  
Last audit update: 2026-08-19  
Owner: repository maintainer

This document is the durable cross-chat register for external projects, papers, products, repositories, architectural patterns, engineering ideas, hardware concepts, and other material that may be useful to JarvisOS, BLUECAD, or BlueRev.

Its purpose is to prevent potentially useful ideas from being lost when discussion moves between ChatGPT conversations.

This document is deliberately **not** a second roadmap. `docs/specs/STATUS.md` remains the sole live authority for specification state, dependencies, queue order, and implementation authorization. Nothing in this register may be implemented merely because it appears here. Promotion into product work still requires the normal backlog/spec/readiness/implementation process.

## Mandatory intake rule

When a maintainer conversation proposes, links, uploads, or discusses something that might materially improve JarvisOS, BLUECAD, or BlueRev, the coordinating agent must:

1. read this register before claiming that an idea is new, already covered, or absent;
2. inspect the new source deeply enough to separate actual implementation from README/marketing claims when source access permits;
3. add a new entry or update the closest existing entry instead of leaving the useful result only in chat context;
4. preserve source/provenance, the concrete reusable mechanism, major caveats, and current disposition;
5. avoid converting the entry into implementation authority; if later promoted, link the governing spec/ADR rather than duplicating its live state here;
6. keep rejected and superseded entries when they carry useful negative evidence, so weak patterns are not repeatedly rediscovered;
7. re-check current source version and licensing before copying code or substantial implementation detail;
8. when auditing a GitHub organization, check repository `fork`, `parent`, and `source` metadata before attributing an idea to that organization.

This rule applies to, for example, a newly discovered GitHub project, Rizzo-PI/Rizzo-pii-like system, research paper, engineering software, CAD/CFD/FEM workflow, local-AI runtime, agent framework, hardware module, sensor, photobioreactor component, or BlueRev process idea.

## Entry states

- `CAPTURED`: relevant source/idea recorded but not deeply audited.
- `AUDITED`: code/docs inspected and reusable patterns identified.
- `CANDIDATE`: materially worth adapting when an authorized product need reaches it.
- `PARKED`: useful but premature or lacking a current trigger.
- `REJECTED`: not worth importing/adapting in its current form; retain why.
- `PROMOTED`: one or more ideas entered a governing spec/ADR; that record now owns implementation state.
- `SUPERSEDED`: a stronger reference replaced this entry's role.

## Evidence labels

- `CODE-FIRST`: concrete code/tests/contracts inspected.
- `DOCS-FIRST`: documentation inspected, implementation not fully proven.
- `CONCEPT`: design hypothesis retained without treating the source as implementation evidence.

## Value grade

Grades are reference value, not implementation priority:

- `S`: unusually strong direct reference.
- `A`: strong reusable patterns.
- `B`: selected useful ideas, substantial adaptation required.
- `C`: limited or mostly overlapping value.
- `D`: weak/misleading reference or clearly better upstream exists.

---

# Current candidate register

| ID | Source / idea family | Area | Evidence | Grade | State | Main reusable value |
| --- | --- | --- | --- | --- | --- | --- |
| REF-001 | PHENOMVALENCE/JARVIS-OS | agent authority / desktop actions | CODE-FIRST | A | CANDIDATE | typed actions, permission/risk metadata, deterministic bypass, effect verification, recoverable deletion and audit patterns |
| REF-002 | Ouru77/ev-assistant | local desktop assistant | DOCS-FIRST | B | PARKED | offline-first voice/browser/screen routing, destructive confirmations, memory and desktop-assistant UX |
| REF-003 | moeru-ai/AIRI | computer use / task state | CODE-FIRST | S | CANDIDATE | perception-snapshot-bound computer use, session operation budgets, task memory separated from long-term memory |
| REF-004 | IRISX-AI/IRIS-Mini | realtime multimodal desktop UI | DOCS-FIRST | B | PARKED | realtime multimodal interaction, polished desktop UI, Socket.io/Windows setup patterns |
| REF-005 | SreejanPersonal/JARVIS-AGI | legacy Jarvis clone | DOCS-FIRST | C | PARKED | historical comparison only; stale relative to stronger references and licensing requires care |
| REF-006 | Wayfinder | routing / evaluation architecture | CODE-FIRST | A | CANDIDATE | deterministic preprocess -> features -> scoring -> recommendation -> explanation, validated config, dry-run JSON, benchmarks, ADRs |
| REF-007 | Cavemem/Caveman family | memory / retrieval | CONCEPT | A | PARKED | local-first write boundary, progressive retrieval, technical-token preservation, gated promotion |
| REF-008 | BlueRev Obsidian vault bridge | knowledge architecture | CONCEPT | A | CANDIDATE | Obsidian source-of-truth, read-only retrieval/index, bounded context packs, evidence/status classes, gated canonical promotion |
| REF-009 | Solnest coding agent | autonomous coding gates | CODE-FIRST | B | CANDIDATE | post-edit deterministic gates; implementation guardrails are weaker than the concept |
| REF-010 | reverse-skill | capability routing / experience | CODE-FIRST | B+ | CANDIDATE | machine-readable routing authority, local tool inventory, experience journal with controlled promotion |
| REF-011 | HyperClaw | authority / sandboxing | CODE-FIRST | A | CANDIDATE | monotonically restrictive authority, per-agent creds, workspace/network/resource isolation |
| REF-012 | nexu-io/open-design | BLUECAD artifacts / agent runtimes | CODE-FIRST | S | CANDIDATE | refreshable Live Artifacts with provenance/snapshots and declarative agent-runtime adapters |
| REF-013 | isdvsv/bug-hunter | autonomous coding runtime | CODE-FIRST | A | CANDIDATE | canonical run state, single-writer lock, baseline, dry-run, resume, chunk/hash cache, payload validation, canary-first changes |
| REF-014 | avivl/claude-007-agents | multi-agent orchestration | CODE-FIRST | D | REJECTED | negative reference: advertised-real components included simulated MCP/tasks/mock/random analysis |
| REF-015 | mrveiss/AutoBot-AI | approvals / workflow orchestration | CODE-FIRST | A+ | CANDIDATE | persistent approval lifecycle, revision/resubmit, workflow dependency semantics, bounded remembered approvals |
| REF-016 | Jacobdrosol/NexusAI | distributed workers / authority | CODE-FIRST | A+ | CANDIDATE | worker readiness/attestation, typed least-privilege agent blueprints, credential refs, payload-bound one-shot approvals, scheduler |
| REF-017 | Solnest-AI/echo-agent | untrusted-content boundary | CODE-FIRST | A | CANDIDATE | deterministic lanes, sealed no-tool reasoning, strict structured output, ID whitelist, fail-soft fallback |
| REF-018 | grabbly/lanehub | multi-agent identity | CODE-FIRST | B+ | CANDIDATE | stable authenticated actor identities, per-agent credentials/endpoints, provenance-preserving merged feed |
| REF-019 | Lessan / linux-autonomos-agent | learning / tool effectiveness | CODE-FIRST | B- | PARKED | empirical tool effectiveness and prior-task retrieval; needs contextual metrics and no authority promotion |
| REF-020 | ZYRAXON browser family | browser/computer use | CODE-FIRST | C | SUPERSEDED | isolated observations only; AIRI/Hermes/Nexus references are stronger |
| REF-021 | zyraxon-code | coding editor | CODE-FIRST | D | REJECTED | insufficient unique value over studying actual upstream editor/agent projects |
| REF-022 | NousResearch/Hermes Agent | large tool catalogs / execution | CODE-FIRST | S | CANDIDATE | tiered progressive tool disclosure, scope-safe bridge, conflict-aware parallelism, strict JSON, checkpoints/persistence, large-result spillover |
| REF-023 | Rizzo-PI / Rizzo-pii family | engineering AI efficiency | CAPTURED | — | CAPTURED | software-side inference/specialization may matter as much as hardware; exact version must be re-audited before requirements |
| REF-024 | Seeker.Bot | evidence / capability dependencies | CODE-FIRST | A | CANDIDATE | claim-level evidence arbitration, verification depth, domain-sensitive confidence decay, capability dependency graph |
| REF-025 | ZYRAXON-AI | dynamic capability installation / memory | CODE-FIRST | B- | PARKED | typed capability-install concept and simple memory ranking; broad self-evolve authority is unsuitable |
| REF-026 | solnest-jarvis | latency lane / background jobs | CODE-FIRST | A- | CANDIDATE | fast native-tool lane, read-only background specialists, job epochs, concurrency cap, orphan reaping, stale-result suppression |
| REF-027 | MAYA-AIt | prompt-routed multi-agent graph | CODE-FIRST | C | REJECTED | mostly single-turn prompt specialists/placeholders; small useful record-ID ranking pattern already covered better elsewhere |
| REF-028 | IRIS-GO | advertised multi-agent system | CODE-FIRST | D | REJECTED | negative reference: advertised Browser/File/OS/Coder/Research agent files are empty and roadmap marks them unfinished |
| REF-029 | arpitrajjj/OnyxBridge + OnyxDashboard | edge-device / fleet telemetry | CODE-FIRST | A- | CANDIDATE | persistent device identity, idempotent registration, periodic heartbeat, bounded offline queue/backoff, SSE live dashboard + polling fallback |
| REF-030 | arpitrajjj/Mishri | utility behavior selection | CODE-FIRST | C+ | PARKED | utility-scored action selection with drives/state, anti-repeat penalty and pacing; relevant only to low-stakes ambient behavior |
| REF-031 | arpitrajjj/rich-editor-bot + rippercasted | messaging UX / C++ scaffold | CODE-FIRST | C | PARKED | Telegram rich-editor/mini-app UX and clean CMake packaging are valid but add little unique JarvisOS/BlueRev architecture value |
| REF-032 | NousResearch/hermes-toolperf-evals + hermes-compression-eval | runtime improvement / context survival | CODE-FIRST | S | CANDIDATE | mine real tool failures/waste; baseline-vs-fix evaluation; grade compression by ability to resume exact work, not summary similarity |
| REF-033 | NousResearch/autoreason + hermes-agent-self-evolution | refinement / controlled self-improvement | CODE-FIRST | A | CANDIDATE | explicit incumbent, blinded challenger comparison, offline candidate evolution; promotion requires deterministic gates and review |
| REF-034 | NousResearch/Nomos + Atropos/tinker-atropos | adaptive reasoning / specialist training environments | CODE-FIRST | A- | PARKED | allocate compute to under-verified tasks; separate environment/reward truth from replaceable trainer/inference backend |
| REF-035 | NousResearch/neural-steering + smc-inference-server + DisTrO | model steering / inference-time search / distributed training | CODE-FIRST | B | PARKED | research options for local-model steering, inference-time quality and distributed training; never substitutes for authority policy |

Supporting detailed Nous audit: `docs/audits/NOUS_RESEARCH_REPO_AUDIT_2026-08-19.md`.

---

# Detailed reusable patterns

## REF-001 — PHENOMVALENCE/JARVIS-OS

- Models propose **typed actions**, not unrestricted shell commands.
- Action contracts carry explicit risk, permissions, reversibility, local/network posture and parameter schema.
- Deterministic requests bypass the LLM when intent is already known.
- Prefer recoverable destructive operations where possible.
- A process returning success is not proof the requested real-world effect happened; support post-action verifiers.
- Audit history should resist silent alteration, e.g. tamper-evident chaining.

Do not create a second authority system beside JarvisOS's current execution spine.

## REF-002 — ev-assistant

Useful end-user patterns: offline-first voice -> router -> local model -> TTS, browser/screen integration, destructive confirmations, long-term memory and optional screen vision. Its safety/routing model is not authoritative until a deeper code audit proves it.

## REF-003 — AIRI

AIRI is a strong reference for safe desktop computer-use despite a different product philosophy.

### Perception-bound action

A GUI mutation should be bound to the exact perception state used to choose it. Candidate JarvisOS fields:

`grounding_snapshot_id, host_id, display_id, window/session_id, coordinate_space_version, captured_at, expires_at`.

Before a click/type/drag, executor verifies that the grounding snapshot is still valid. A stale screenshot should force re-perception rather than a blind action.

### Task memory != long-term memory

Keep transient execution state separate from durable user/domain memory. Candidate task state:

`goal, current_step, confirmed_facts, artifacts, blockers, next_step, plan, assumptions, completion_criteria`.

Also retain session operation budgets and explicit pending-action lifecycle.

## REF-004 — IRIS-Mini

Useful mainly for UI/runtime comparison: realtime multimodal interaction, polished presentation, realtime transport and Windows setup flows. Do not adopt frameworks merely because this reference uses them.

## REF-005 — JARVIS-AGI

Historical comparison only. Prefer current references for architecture and independently audit licensing before any reuse.

## REF-006 — Wayfinder

Strong pattern:

`preprocess -> feature extraction -> scoring -> recommendation -> explanation`.

Supporting practices: validated configuration round trips, deterministic dry-run, machine-readable JSON, benchmark/evaluation harnesses, offline tests and ADRs. Do not copy simplistic local-vs-cloud or complexity-only routing where JarvisOS has richer provider/authority policy.

## REF-007 — Cavemem/Caveman memory patterns

- local-first write authority;
- progressive retrieval rather than indiscriminate context loading;
- preserve engineering identifiers, units, chemical names, equations, filenames and IDs through compression;
- summaries are derived representations, not replacements for canonical evidence;
- durable promotion is gated.

## REF-008 — BlueRev Obsidian vault bridge

Preferred hybrid model: Obsidian may remain human-readable source of truth; start with read-only indexing/retrieval; construct bounded Context Packs; promote only stable summaries/decisions to canonical memory; retain papers/protocols/source cards as evidence; use explicit `canonical/candidate/measured/to_measure/future/archive` states.

## REF-009 — Solnest coding agent

Keep automatic deterministic feedback immediately after an agent edit. Tests, lint, type, secret and policy checks belong in the execution loop rather than only in prompts.

Do not copy observed weaknesses such as shell `eval`, regex-only secret detection, staged-diff-only coverage or obvious scanner exclusions. Use declarative runners and purpose-built scanners.

## REF-010 — reverse-skill

Machine-readable routing is canonical; Markdown is a human view. Maintain an inventory of tools/capabilities that actually exist. Store successful/failing task patterns in a field journal. Never let one observed case automatically become a canonical routing rule.

## REF-011 — HyperClaw

Adopt monotonic restriction:

`global policy -> provider/runtime -> agent -> sandbox -> subagent`.

A lower layer may remove authority but must never restore a capability denied above it. Useful resource scopes include workspace `none/read-only/read-write`, network posture, per-agent credentials and CPU/RAM limits.

## REF-012 — open-design

### Live Artifacts for BLUECAD

Represent an artifact as:

`template + data binding + provenance + connector policy + snapshots + refresh history`.

Candidate applications include reactor profiles, mass/energy balances, Sankey diagrams, equipment datasheets, convergence dashboards, sensitivity plots, economics, validation reports and PFD/scene overlays. Refresh from engineering state without asking an LLM to redraw the presentation; preserve the last known-good snapshot after a failed refresh.

### Declarative agent runtimes

Codex, Claude Code, Qwen/Hermes/local CLIs and future runners should be described by runtime definitions (executable/version probe, auth, stream format, prompt transport, model selection, capabilities) rather than one bespoke orchestration class per provider.

## REF-013 — bug-hunter

Strong patterns: canonical machine-readable run state; single-writer lock; baseline before modifications; first-class dry-run/resume; chunking/hash cache; payload validation; canary-first modifications; retry/backoff + journal; exact branch/PR/file scope.

Candidate run record:

`run_id, exact_base_sha, scope, objective, constraints, files_owned, baseline, produced_changes, evidence, findings, retries, state`.

## REF-014 — claude-007-agents

Negative evidence: components described as real/runnable contained simulated MCP connections, synthetic tasks, `simulateAgentExecution()`, mock filesystem lists and random architecture-pattern detection. README architecture is never sufficient evidence of an execution path.

## REF-015 — AutoBot-AI

Approval is a durable lifecycle:

`pending -> approved / rejected / revision_requested -> resubmitted`.

Remembered approvals must be structurally scoped. Dependency semantics should distinguish `DATA`, `RESOURCE`, `ORDER`, `TRANSACTIONAL`, and `NONE`; directly relevant to BLUECAD geometry -> mesh -> solver -> analysis/report graphs.

## REF-016 — NexusAI

A configured worker is not automatically dispatchable. Check enabled/online state, model/provider availability, required tools, runtime probe/attestation, authentication readiness, model catalog and credential-reference existence.

Candidate typed agent fields:

`role, accepted inputs, produced outputs, capabilities, resource scope, risk ceiling, network posture, model policy, credential refs, completion contract`.

For high-impact permits bind approval to `actor + action key + canonical payload digest + expiry + unused state`. Prefer scheduling as `validated target -> dedupe -> readiness/authority guard -> run record -> bounded retry/backoff -> terminal outcome`.

## REF-017 — echo-agent

Trust rule: untrusted content may inform judgment but must not automatically enter a tool-enabled authority context.

Candidate flow:

`email/web/PDF/document -> sealed no-tool reasoner -> strict structured output -> deterministic whitelist/validation -> separately authorized action`.

## REF-018 — LaneHub

Each agent should have stable authenticated `actor_id`, isolated credentials and provenance-preserving messages/events. “Claude said X” should be backed by run identity, not a forgeable prose prefix.

## REF-019 — Lessan

Tool success/failure history and similar-task retrieval may influence routing. Segment effectiveness by capability, environment/version, input class, latency, cost, failure mode and deterministic verifier. Historical success never expands authority.

## REF-020 — ZYRAXON browser family

Keep only observations not already covered by AIRI/Hermes/Nexus. No dedicated adoption path is justified today.

## REF-021 — zyraxon-code

Rejected as primary reference because useful concepts are better studied in actual upstream editor/agent projects.

## REF-022 — NousResearch/Hermes Agent

The focused audit inspected **upstream `NousResearch/hermes-agent` itself**, not only downstream forks. Current upstream license checked on 2026-08-19: MIT.

### Tiered progressive tool disclosure

For large plugin/MCP catalogs, Hermes keeps core/session-surface tools direct and defers non-core schemas behind:

`tool_search -> tool_describe -> tool_call`.

Disclosure degrades from names + short descriptions to names-only and, for extreme catalogs, per-server summaries. The catalog is rebuilt from the current live registry. Unknown tools remain visible rather than disappearing. Deferred discovery stays within current session scope, and bridge calls traverse the same guardrail/approval/hook/result path as direct calls.

### Conflict-aware parallel execution

Hermes does not equate multiple emitted calls with safe parallelism. It partitions ordered batches into sequential/parallel segments. Filesystem operations reserve canonical paths with reader/writer roles: reader-reader overlap may commute; any writer conflict is ordered. Malformed/non-object JSON becomes a barrier and later fails rather than being guessed/repaired.

This maps directly to BLUECAD resource reservations and coding-agent file ownership.

### Execution integrity and spillover

Other strong patterns: exact-path checkpoints, bounded approval serialization, incremental durable session flush after side effects, bounded worker/timeouts, current-scope recheck on tool-search unwrap, and persistent spillover for large individual/aggregate tool output.

Direct uses include compiler output, test logs, CFD/FEM solver traces, repository searches and engineering reports.

## REF-023 — Rizzo-PI / Rizzo-pii family

Intake trigger, not assumed implementation. The useful hypothesis is that European/local AI independence and engineering performance can improve through inference software, specialization, compression, routing and task-specific execution rather than only larger hardware. Re-open exact current repository/version before extracting requirements.

## REF-024 — Seeker.Bot

### Capability dependency graph

Code implements capability -> provider mapping with recursive dependency resolution, missing-capability errors, cycle detection and topological ordering. Fold the useful concept into the richer JarvisOS capability/workflow registry rather than creating another graph store.

### Evidence arbitrage and decay

Represent atomic claims with sources, support/contradiction, agreement state, verification depth and effective confidence. For BLUECAD, actual engineering provenance must outrank “model confidence”. Show conflict zones explicitly.

Information age should matter: API/news facts decay faster than durable engineering/history facts. Use explicit domain/provenance metadata and deterministic policy rather than keyword-only classification. Stale facts become candidates for re-verification.

## REF-025 — ZYRAXON-AI

The inspected “self evolution” mainly writes local MCP configuration with command/args/env after broad permission. Redesign safely as `CapabilityInstallProposal` containing source/package, pinned version/hash, permissions, network/resources, validation/attestation and explicit activation approval. Capability installation is a supply-chain/authority event, not an ordinary tool call.

## REF-026 — solnest-jarvis

Useful fast native-tool lane for common low-latency operations, plus background specialist lifecycle: read-only background jobs only, concurrency cap, timeout, epoch tagging, persisted PIDs/orphan reaping, kill switch and undelivered-result retention. Old results from superseded task epochs must not silently land into a new state.

## REF-027 — MAYA-AIt

Mostly single-turn LangGraph prompt specialists with placeholders. Minor valid pattern: retrieve real DB records deterministically, let the LLM rank/explain, then map back to existing IDs with fallback. Already covered better elsewhere, so rejected as a primary architecture reference.

## REF-028 — IRIS-GO

Negative evidence: README describes Browser/File/OS/Coder/Research agents while inspected corresponding source files are empty and roadmap marks them unfinished. Diagrams are not implementation evidence.

## REF-029 — arpitrajjj/OnyxBridge + OnyxDashboard

A follow by the public GitHub account is not evidence of malicious intent; this entry records only public technical patterns. No public JarvisOS fork/name match was visible during the audit.

Useful subsystem: persistent device UUID/config, idempotent registration, periodic network-constrained heartbeat, exponential backoff, bounded file-backed offline queue, queue drain on reconnect, missing-device re-registration, SQLite WAL backend, SSE live updates and polling fallback.

Candidate pattern:

`EdgeNode -> authenticated register/attest -> heartbeat/telemetry queue -> backend state -> SSE -> operator UI`.

Security caveat: inspected Onyx dashboard did not provide the authenticated node/attestation boundary JarvisOS requires. Copy resilience/UX, not security.

## REF-030 — arpitrajjj/Mishri

Low-stakes utility behavior loop: behaviors receive state/drive scores, random noise and anti-repeat penalty before max-score selection. Potential use only for ambient/persona behavior or non-critical proactive suggestions; never engineering actions or permissions.

## REF-031 — arpitrajjj miscellaneous

`rich-editor-bot` is a substantial Telegram bot + mini-app editor and may inform remote rich-message UX. `rippercasted` is a clean generic C++17/CMake scaffold. Neither adds unique core architecture.

## REF-032 — Nous Research runtime-evaluation laboratory

Detailed evidence: `docs/audits/NOUS_RESEARCH_REPO_AUDIT_2026-08-19.md`.

### `hermes-toolperf-evals`

One of the strongest Nous-specific references. It mines real Hermes session traces, normalizes tool failure classes, measures retries/duplicates/fallbacks/result sizes/context waste and turns observed pain points into isolated baseline-vs-fix experiments.

Candidate Jarvis telemetry:

`tool_call_id, run_id, task_id, capability, model/provider, normalized_error_class, retry_of, duplicate_of, fallback_tool, result_bytes, context_bytes, latency_ms, authorization_outcome, verifier_outcome, terminal_state`.

Tool ergonomics should improve from measured traces, not intuition; a strong model must not hide a weak tool interface by repeatedly recovering.

### `hermes-compression-eval`

Contains fixtures, compressor driver, probe suites, grader, reports and tests. Compression quality is assessed via downstream ability to recover exact current state, artifact trail, completeness and continuation ability.

A future `ContextSurvivalEval` should compress realistic coding/engineering sessions, give only the compressed handoff to a fresh agent, then probe exact component IDs, units, paths, decisions, last known-good state, blockers and next action. Token reduction is not success if continuity is lost.

## REF-033 — Nous Research refinement / controlled self-improvement

### `autoreason`

The real runner keeps A = incumbent, generates B = revision and AB = synthesis, randomizes presentation order independently per judge, aggregates rankings, gives ties to incumbent A and converges after repeated incumbent wins.

Candidate rule for prompts/specs/design reports:

`promote challenger only if it beats an explicit incumbent under a stable rubric`.

Never use LLM voting instead of deterministic engineering truth.

### `hermes-agent-self-evolution`

Useful experimental separation of candidate generation, structural constraints and holdout fitness, but implementation maturity is lower than the name implies. The audited skill-evolution path does not invoke the full Hermes test-suite runner even though such a helper exists/configuration mentions tests; output is written for review rather than automatically applied, and inspected code-self-evolution area was not implemented.

Safe Jarvis pattern:

`offline candidate -> immutable baseline -> hard constraints -> mandatory deterministic tests/verifiers -> holdout benchmark -> evidence/diff -> explicit review -> normal spec/PR promotion`.

Never permit live authority-bearing code/policy to rewrite itself directly.

## REF-034 — Nous reasoning / training environments

### `Nomos`

Many candidate reasoning workers are allocated preferentially to problems with weaker current evidence/scores, followed by consolidation and pairwise selection. The useful principle is **adaptive compute allocation**: difficult/contradictory/under-verified work gets extra reasoning or verification budget; easy verified work does not.

### `Atropos` + `tinker-atropos`

Atropos separates RL environments/trajectory evaluation from trainer and inference engine. The repository is now archived and explicitly unmaintained, so treat it as architecture reference only. `tinker-atropos` demonstrates that environment/reward definitions can remain portable while the training backend changes.

Future engineering-specialist pattern:

`EngineeringEnvironment = task generator + allowed observations/actions + deterministic/primary-source verifier + reward + trajectory record`.

Possible environments include tool selection, units, flowsheet reasoning, CAD operations, equation solving, solver setup, convergence diagnosis and evidence attribution. Training infrastructure remains replaceable.

## REF-035 — Nous model / inference research

### `neural-steering`

Contrastive Neuron Attribution for finding sparse behavioral/factual MLP circuits and steering them at inference. Relevant to local-model interpretability/research, but model steering never replaces typed authority, sandboxing, approvals or deterministic verification.

### `smc-inference-server`

Sequential Monte Carlo steering behind an API, oriented to vLLM and optional multi-GPU workers. Useful lesson: quality can improve through inference-time search/steering, not only larger base models. Current implementation is not a ready consumer-laptop solution.

### `DisTrO`

Original Nous distributed-training-over-Internet project. Potential long-term relevance to decentralized/local-AI sovereignty, not current JarvisOS execution architecture.

### Provenance caveat for the Nous organization

Several attractive-looking repositories in `NousResearch` are direct forks, including Microsoft/NVIDIA/vLLM/HLC projects. Their innovations must be attributed and audited at upstream rather than treated as Nous-authored. This audit explicitly confirmed direct forks for `agent-governance-toolkit`, `OpenShell`, `NemoClaw`, `Gym`, `Automodel`, `RL`, `pico`, and `speculators`.

---

# Cross-cutting architecture synthesis

The strongest audited ideas currently converge toward the following possible long-term structure. This is a reference synthesis, **not an approved architecture or spec**:

```text
USER / AUTOMATION
       |
       v
Intent + Trust Classification
       |
       +---- untrusted content ----> Sealed Reasoner (NO TOOLS)
       |
       v
Agent / Model Router
       |
       v
Capability Registry
       |
       +---- progressive authorized Tool Catalog
       |
       v
Monotonic Authority Chain
       |
       v
Workflow Graph / Resource Reservations
(DATA / RESOURCE / ORDER / TRANSACTIONAL)
       |
       +---- Standing Grant
       +---- Payload-bound One-shot Permit
       |
       v
Worker Readiness / Capability Attestation
       |
       v
Checkpoint / Baseline / Exact Scope / Epoch
       |
       v
EXECUTION
       |
       +---- conflict-aware parallel segments
       |
       v
Deterministic Verifier
       |
       v
Domain State / Live Artifact
       |
       +---- claim/evidence/conflict provenance
       |
       v
Audit + AgentRun + Experience Journal
       |
       +---- tool-performance telemetry
       +---- context-survival evaluation
```

Additional cross-cutting principles now supported by multiple audits:

- **visibility is not authority**: a model may know a capability exists without receiving permission to invoke it;
- **untrusted information is not instruction authority**;
- **stale execution state is dangerous**: bind GUI actions to perception snapshots and background results to task epochs;
- **parallelism is a resource-safety decision**, not merely a model-output optimization;
- **large tool output should spill, not destroy context**;
- **confidence is provenance-dependent and time-sensitive**, not a permanent scalar emitted by a model;
- **edge workers need identity/readiness/heartbeat/attestation**, not just an IP address;
- **Markdown is usually a view**, while canonical state should be machine-readable where automation depends on it;
- **runtime improvement should be empirical**: measure failure/retry/waste, change one boundary, compare baseline vs candidate;
- **compression is successful only if work survives it**;
- **unchanged incumbent is a valid candidate** during subjective refinement; rewrites are not automatically improvements;
- **reasoning budget should follow uncertainty/evidence deficit**, not be spent uniformly;
- **self-improvement must remain offline, gated and reviewable**;
- **training environment/reward truth should be portable across trainer/provider backends**.

---

# BlueRev / engineering-specific intake rule

This register is not limited to software projects. Future BlueRev material belongs here when it may alter product or engineering capability, including:

- photobioreactor geometry, materials, membranes, ETFE, pumping, gas exchange, mixing, sensors, harvesting, fouling control, microorganism viability, illumination, thermal control, mooring, offshore power and field instrumentation;
- CFD/FEM/process simulation methods;
- digital twins, state estimation, optimization, control, uncertainty, data reconciliation and experiment design;
- CAD/manufacturing methods;
- scientific papers, patents, standards, datasets, hardware boards, cameras, edge computers, pumps, valves, probes or lab equipment;
- funding-relevant technical capabilities that may be difficult to acquire later.

Record the engineering claim separately from marketing language, and mark uncertain technical claims until supported by primary evidence.

---

# Promotion rule

When a candidate becomes relevant to current product work:

1. revalidate the source against its current version when recency matters;
2. check licensing before copying code or substantial implementation detail;
3. state the concrete JarvisOS/BLUECAD/BlueRev problem it solves;
4. run the minimum-necessary test;
5. create/update the appropriate backlog/spec/ADR through the normal repository process;
6. change this entry to `PROMOTED` and link the authoritative record;
7. keep implementation status exclusively in `docs/specs/STATUS.md`.

# Maintenance rule

Prefer updating an existing entry over creating synonyms. Preserve negative findings. When a later audit changes an earlier conclusion, append the new evidence and mark the old conclusion superseded rather than silently erasing provenance.

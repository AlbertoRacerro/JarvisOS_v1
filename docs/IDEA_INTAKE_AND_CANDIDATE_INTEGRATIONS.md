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
7. re-check current source version and licensing before copying code or substantial implementation detail.

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

---

# Detailed reusable patterns

## REF-001 — PHENOMVALENCE/JARVIS-OS

Keep/adapt:

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

Also retain the idea of session operation budgets and explicit pending-action lifecycle.

## REF-004 — IRIS-Mini

Useful mainly for UI/runtime comparison: realtime multimodal interaction, React/Tailwind/Framer/Three-style presentation, websocket-style transport and Windows setup flows. Do not adopt frameworks merely because this reference uses them.

## REF-005 — JARVIS-AGI

Historical comparison only. Prefer current references for architecture and independently audit licensing before any reuse.

## REF-006 — Wayfinder

Strong pattern:

`preprocess -> feature extraction -> scoring -> recommendation -> explanation`.

Supporting practices: validated configuration round trips, deterministic `--dry-run`, machine-readable JSON, benchmark/evaluation harnesses, offline tests and ADRs. Do not copy simplistic local-vs-cloud or complexity-only routing where JarvisOS has richer provider/authority policy.

## REF-007 — Cavemem/Caveman memory patterns

Candidate principles:

- local-first write authority;
- progressive retrieval rather than indiscriminate context loading;
- preserve engineering identifiers, units, chemical names, equations, filenames and IDs through compression;
- summaries are derived representations, not replacements for canonical evidence;
- durable promotion is gated.

## REF-008 — BlueRev Obsidian vault bridge

Preferred hybrid model:

- Obsidian can remain a human-readable source-of-truth vault;
- start with read-only indexing/retrieval;
- a Context Pack Builder selects bounded source material per task;
- only stable summaries/decisions are candidates for canonical JarvisOS memory;
- papers/protocols/source cards remain retrievable evidence instead of being copied wholesale;
- explicit statuses such as `canonical`, `candidate`, `measured`, `to_measure`, `future`, `archive` prevent uncertain engineering knowledge becoming fact accidentally.

## REF-009 — Solnest coding agent

Keep automatic deterministic feedback immediately after an agent edit. Tests, lint, type, secret and policy checks belong in the execution loop rather than only in prompts.

Do not copy observed weaknesses such as shell `eval`, regex-only secret detection, staged-diff-only coverage or obvious scanner exclusions. Use declarative runners and purpose-built scanners.

## REF-010 — reverse-skill

- Machine-readable routing is canonical; Markdown is a human view.
- Maintain an inventory of tools/capabilities that actually exist locally.
- Store successful/failing task patterns in a field journal.
- Never let one observed case automatically become a canonical routing rule; promotion needs deterministic evidence or explicit review.

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

Strong autonomous-repository patterns:

- canonical machine-readable run state; Markdown is a render;
- single-writer lock;
- baseline before modifications;
- first-class dry-run and resume;
- chunking and content-hash cache;
- payload/schema validation before subagent launch;
- canary-first autonomous modifications;
- retry/backoff + execution journal;
- exact branch/PR/file scope.

Candidate run record:

`run_id, exact_base_sha, scope, objective, constraints, files_owned, baseline, produced_changes, evidence, findings, retries, state`.

## REF-014 — claude-007-agents

Negative evidence: components described as real/runnable contained simulated MCP connections, synthetic tasks, `simulateAgentExecution()`, mock filesystem lists and random architecture-pattern detection. README architecture is never sufficient evidence of an execution path.

## REF-015 — AutoBot-AI

### Persistent approval lifecycle

Approval is a durable object, not a transient yes/no modal:

`pending -> approved / rejected / revision_requested -> resubmitted`.

Record requester, workflow/step, resource, before/after intent, evidence/reason, decision maker, comments, linked task, timestamps and risk.

### Approval memory

Remembered approvals must be structurally scoped by project/user/capability/resource/risk/expiry. Do not copy broad shell wildcarding.

### Dependency semantics

Distinguish:

- `DATA`: B consumes A output;
- `RESOURCE`: calls contend on mutable state;
- `ORDER`: ordering only;
- `TRANSACTIONAL`: one commit/rollback unit;
- `NONE`: independent and safe to parallelize.

Directly relevant to BLUECAD geometry -> mesh -> solver -> analysis/report graphs.

## REF-016 — NexusAI

### Worker readiness / capability attestation

A configured worker is not automatically dispatchable. Check enabled/online state, model/provider availability, required tools, runtime probe/attestation, authentication readiness, model catalog and credential-reference existence.

This is a strong basis for a future JarvisOS worker registry spanning workstation, secondary PC, Raspberry Pi/edge nodes, GPU workers, sensors and BlueRev gateways.

### Typed least-privilege agent blueprint

Candidate fields:

`role, accepted inputs, produced outputs, capabilities, resource scope, risk ceiling, network posture, model policy, credential refs, completion contract`.

Never embed raw credentials in exportable agent definitions.

### One-shot payload-bound approval

Bind a high-impact permit to:

`actor + action key + canonical payload digest + expiry + unused state`.

Changing a parameter invalidates the permit; consumption is atomic and one-shot. Keep it distinct from a standing grant such as “may create plots in this workspace”.

### Scheduler

Prefer:

`schedule -> validated target -> dedupe -> readiness/authority guard -> run record -> bounded retry/backoff -> terminal outcome`

rather than `cron -> prompt`.

## REF-017 — echo-agent

Trust rule:

> Untrusted content may inform model judgment, but must not automatically enter a tool-enabled authority context.

Candidate flow:

`email/web/PDF/document -> sealed no-tool reasoner -> strict structured output -> deterministic whitelist/validation -> separately authorized action`.

Also retain deterministic lanes before model calls, bounded context, no inherited tools/settings, whitelist generated IDs against actual source IDs, deterministic fallback, idempotent dry-runs and visible read-back for state changes.

## REF-018 — LaneHub

The useful abstraction is agent identity, not Telegram. Each agent should have stable authenticated `actor_id`, isolated credential, provenance-preserving messages/events and a shared feed that never loses who produced an item. “Claude said X” should be backed by authenticated run identity, not a forgeable text prefix.

## REF-019 — Lessan

Tool success/failure history and similar-task retrieval can influence routing. A JarvisOS implementation should segment effectiveness by capability, environment/version, input class, latency, cost, failure mode and deterministic verifier. Historical success may guide selection but never expand authority.

## REF-020 — ZYRAXON browser family

Keep only observations not already covered by AIRI/Hermes/Nexus. No dedicated adoption path is justified today.

## REF-021 — zyraxon-code

Rejected as primary reference because useful concepts are better studied in actual upstream editor/agent projects.

## REF-022 — NousResearch/Hermes Agent

The focused audit upgrades Hermes from captured to a top-tier code-first reference. Current upstream license inspected on 2026-08-19: MIT; nevertheless integration should adapt concepts rather than create a parallel authority system.

### Tiered progressive tool disclosure

For large plugin/MCP catalogs, Hermes keeps core/session-surface tools direct and defers non-core plugin/MCP schemas behind:

`tool_search -> tool_describe -> tool_call`.

Disclosure is tiered:

- no deferred tools: normal passthrough;
- catalog fits context budget: names + short descriptions;
- larger catalog: names-only;
- extreme catalog: only per-server summary/tool counts, with individual discovery by search.

Important JarvisOS requirements derived from the pattern:

- core control tools stay directly visible;
- deferred catalog is rebuilt from the **current live authorized registry**, not a stale session cache;
- an unknown/unclassifiable tool stays visible rather than being silently dropped;
- tool search discovers only capabilities in the current session scope;
- the bridge invokes the underlying tool through the exact same guardrail/approval/hook/result-truncation path as a direct call;
- UI/audit should expose the real underlying tool, not hide it behind `tool_call`.

### Conflict-aware parallel execution

Hermes does not equate “multiple tool calls emitted together” with “safe to parallelize”. It partitions an ordered batch into sequential/parallel segments and treats interactive or unsafe operations as barriers.

For filesystem operations it reserves canonical paths with reader/writer roles:

- reader/read overlap may run concurrently;
- any overlap involving a writer is ordered;
- a search root overlapping a write is also ordered;
- malformed/non-object JSON arguments become a sequential barrier and later fail execution rather than being guessed/repaired.

This maps well to BLUECAD resource locking and coding-agent file ownership.

### Execution integrity

Other concrete patterns:

- malformed tool arguments do not get “helpfully” repaired before execution;
- file mutations receive a checkpoint tied to the exact resolved workspace path;
- concurrent approval prompts are serialized/bounded;
- tool progress is flushed to durable session state before actions that could restart/terminate the process;
- concurrent batches have bounded worker counts/timeouts;
- session-scoped tool-search unwrap rechecks the actual authorized registry scope.

### Large tool-result spillover

Oversized tool output is preserved outside the active model context instead of being destructively truncated:

1. tools may cap their own output;
2. larger individual results spill to a persistent cache with preview + readable reference;
3. an aggregate per-turn budget spills the largest remaining results until context is safe.

Direct JarvisOS/BLUECAD uses include build logs, test output, CFD/FEM solver logs, repository searches and large data/report tools.

## REF-023 — Rizzo-PI / Rizzo-pii family

This is an intake trigger, not an assumed implementation. The useful hypothesis is that European/local AI independence and engineering performance can improve through inference software, specialization, compression, routing and task-specific execution rather than only larger hardware.

When a new exact version is proposed, reopen the repository/version and extract only verified engineering mechanisms; do not infer features from social posts.

## REF-024 — Seeker.Bot

### Capability dependency graph

Code implements capability -> provider mapping with recursive dependency resolution, missing-capability errors, cycle detection and topological ordering. The abstraction is useful, but JarvisOS should fold it into the richer capability/workflow registry rather than create another graph store.

### Evidence arbitrage

The stronger idea is claim-level evidence handling rather than model voting. Seeker represents:

- atomic claim;
- source model/provider;
- base confidence;
- supporting/contradicting models;
- agreement level such as consensus/majority/split/contradiction;
- verification depth from unverified through corroborated/primary-source/empirically tested;
- effective confidence discounted by verification depth.

For BLUECAD, replace “model confidence” as the trust source with actual engineering provenance. Candidate evidence object:

`claim -> sources -> conflicts -> verification depth -> validator/primary source/experiment -> current confidence`.

Useful UI consequence: show **conflict zones** explicitly instead of averaging contradictory answers into one confident sentence.

### Domain-sensitive confidence decay

Seeker also applies temporal half-life by information domain. The principle is good: market/API/news facts age much faster than durable engineering/history facts.

A JarvisOS version should use explicit domain/provenance metadata and deterministic policy, not keyword classification. Reflexive/user rules and immutable evidence need separate policies. Stale facts should become candidates for re-verification rather than silently being treated as equally current forever.

## REF-025 — ZYRAXON-AI

The code audit demystifies “self evolution”: the inspected implementation mainly lets the agent write new local MCP configuration with command/args/environment after a broad permission request.

Useful concept to redesign safely:

`CapabilityInstallProposal` containing source/package identity, pinned version/hash, requested permissions, network/resource needs, install plan, validation/attestation and explicit activation approval.

Capability installation is a **supply-chain and authority event**, not an ordinary tool call. Never copy broad wildcard permission such as `patterns:["*"]`, and do not let the agent install arbitrary commands merely because a needed tool is missing.

Its JSON memory store adds a small ranking idea: relevance + importance + recency + access frequency. Access frequency can create feedback loops, and “latest N memories” auto-injection is weaker than the progressive retrieval patterns already captured in REF-007/008.

## REF-026 — solnest-jarvis

### Fast lane

A small direct native-tool lane handles common low-latency operations; expensive specialist work is delegated separately. This can inform JarvisOS latency/cost design, but policy/routing must remain server-owned and deterministic rather than persona-driven.

### Background specialist lifecycle

The job manager contains several strong patterns:

- only read-only specialists run in background; mutating ones remain foreground;
- concurrency cap;
- per-job timeout;
- epoch tagging so results from a superseded/restarted conversation are discarded;
- persisted worker PIDs and orphan reaping on startup;
- kill switch for all running workers/process groups;
- completed-but-undelivered results are retained for next-turn delivery.

The **epoch/stale-result rule** is especially valuable: an old research/coding result must not silently land into a new task state after the user has moved on.

### Guardrail corpus

The central guardrail file has a useful corpus of destructive shell/outbound/financial/sensitive-path cases. Treat it as test data/fallback heuristics only; regex classification must not replace typed capability policy.

## REF-027 — MAYA-AIt

Code inspection found a conventional mostly single-turn LangGraph router with prompt-based specialist nodes, several explicitly placeholder. It does not add a strong authority or execution primitive.

One minor pattern is valid: retrieve real DB records deterministically, ask the LLM only to rank/explain them, then map output back through existing record IDs with fallback. This is already covered more strongly by REF-017 and JarvisOS's backend-led design, so the repo is rejected as a primary architecture reference.

## REF-028 — IRIS-GO

Negative evidence. The README describes a working local multi-agent Browser/File/OS/Coder/Research team, while the inspected repository has each corresponding agent source file at 0 bytes and the roadmap itself marks those agents unfinished.

Keep this as another explicit reminder: architecture diagrams and “working system” claims are not evidence until the execution path exists in code/tests.

## REF-029 — arpitrajjj/OnyxBridge + OnyxDashboard

Audited after the public GitHub account began following the maintainer. A follow is not evidence of malicious intent; this entry records only reusable public technical patterns.

The six public repositories visible in the audit did not include a JarvisOS fork/name match. The public profile describes the author as a penetration tester/web-security analyst, which is context, not a threat finding.

### Edge-device registration and heartbeat

The useful Onyx subsystem is not its SMS/native-bridge purpose but its device-to-dashboard reliability model:

- persistent device UUID/config;
- idempotent registration/upsert;
- periodic WorkManager heartbeat with network constraint;
- exponential retry/backoff;
- bounded file-backed offline queue (100 entries, oldest dropped at bound);
- successful connectivity drains pending telemetry;
- missing-device heartbeat can trigger re-registration;
- dashboard derives online/offline from `last_seen` timeout.

This is directly relevant to future BlueRev sensor/edge gateways and to a distributed Jarvis worker fleet.

### Live fleet UI

OnyxDashboard uses:

- SQLite WAL for a tiny self-hosted state store;
- Server-Sent Events for registration/update/heartbeat/delete events;
- client live/connecting/polling/disconnected state;
- polling fallback when the stream is unavailable;
- health endpoint and container smoke tests.

Candidate BlueRev/Jarvis pattern:

`EdgeNode -> register/attest -> heartbeat/telemetry queue -> backend state -> SSE event stream -> operator UI`, with polling fallback.

### Important security caveat

The inspected dashboard endpoints do not establish the authentication/attestation boundary JarvisOS would require. Registration/heartbeat/device mutation therefore must be redesigned around authenticated node identity, replay resistance, scoped credentials and authority checks. Use Onyx as resilience/UX reference, not a security reference.

## REF-030 — arpitrajjj/Mishri

Mishri implements a low-stakes utility-AI behavior loop: each behavior gets a score from state/drives, random noise is added, recent repeated behaviors are penalized, and the maximum is executed after variable pacing.

Potential use is narrow: ambient/persona behavior, UI animation or non-critical proactive suggestions where perfect determinism is undesirable. It should **not** control engineering actions, permissions or system authority because deliberately injected randomness and imperfection conflict with those domains.

## REF-031 — arpitrajjj miscellaneous repositories

### rich-editor-bot

A substantial Telegram bot + built-in mini-app rich editor. Potentially useful only as UX reference for remote rich-message composition, local drafts/live preview, owner panel, channel selector and bot/web-app cohosting. It does not currently justify a JarvisOS architecture candidate beyond existing remote/mobile UI ideas.

### rippercasted

A clean but generic C++17/CMake library scaffold with public-header/source split, tests/examples, install targets and `find_package` config. Good packaging hygiene, but no unique BlueRev/Jarvis capability worth promoting.

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
```

Additional cross-cutting principles now supported by multiple audits:

- **visibility is not authority**: a model may know a capability exists without receiving permission to invoke it;
- **untrusted information is not instruction authority**;
- **stale execution state is dangerous**: bind GUI actions to perception snapshots and background results to task epochs;
- **parallelism is a resource-safety decision**, not merely a model-output optimization;
- **large tool output should spill, not destroy context**;
- **confidence is provenance-dependent and time-sensitive**, not a permanent scalar emitted by a model;
- **edge workers need identity/readiness/heartbeat/attestation**, not just an IP address;
- **Markdown is usually a view**, while canonical state should be machine-readable where automation depends on it.

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

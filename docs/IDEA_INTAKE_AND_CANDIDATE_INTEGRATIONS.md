# JarvisOS / BLUECAD / BlueRev idea intake and candidate-integration register

Status: canonical intake register; **not implementation authority**  
Created: 2026-08-19  
Owner: repository maintainer

This document is the durable cross-chat register for external projects, papers, products, repositories, architectural patterns, engineering ideas, hardware concepts, and other material that may be useful to JarvisOS, BLUECAD, or BlueRev.

Its purpose is to prevent potentially useful ideas from being lost when discussion moves between ChatGPT conversations.

This document is deliberately **not** a second roadmap. `docs/specs/STATUS.md` remains the sole live authority for specification state, dependencies, queue order, and implementation authorization. Nothing in this register may be implemented merely because it appears here. Promotion into product work still requires the normal backlog/spec/readiness/implementation process.

## Mandatory intake rule

When a maintainer conversation proposes, links, uploads, or discusses something that might materially improve JarvisOS, BLUECAD, or BlueRev, the coordinating agent must:

1. read this register before claiming that an idea is new, already covered, or absent;
2. inspect the new source deeply enough to separate actual implementation from README/marketing claims when source access permits;
3. add a new entry or update the closest existing entry instead of leaving the useful result only in chat context;
4. preserve the source name/link or other provenance, the concrete reusable idea, major caveats, and current disposition;
5. avoid converting the entry into implementation authority; if the idea is later promoted, link the governing spec/ADR rather than duplicating its live state here;
6. keep rejected and superseded entries when they carry useful negative evidence, so the same weak pattern is not rediscovered and re-audited repeatedly.

This rule applies to, for example, a newly discovered GitHub project, Rizzo-PI/Rizzo-pii-like system, research paper, engineering software, CAD/CFD/FEM workflow, local-AI runtime, agent framework, hardware module, sensor, photobioreactor component, or BlueRev process idea.

## Entry states

- `CAPTURED`: potentially relevant source or idea recorded, but not yet audited deeply enough.
- `AUDITED`: source was inspected and concrete reusable patterns were identified.
- `CANDIDATE`: audited and considered materially worth adapting when an authorized product need reaches it.
- `PARKED`: useful, but premature or lacking a current trigger.
- `REJECTED`: inspected and not worth importing/adapting in its current form; retain the reason.
- `PROMOTED`: one or more ideas have entered a governing spec/ADR. The spec/ADR, not this file, owns implementation details and live state.
- `SUPERSEDED`: a better reference or pattern replaced this entry's role.

## Evidence labels

- `CODE-FIRST`: concrete code/tests/contracts inspected.
- `DOCS-FIRST`: documentation inspected, but implementation claims were not fully proven.
- `CONCEPT`: useful architectural idea retained without treating the source as implementation evidence.

## Value grade

Grades are **reference value**, not implementation priority:

- `S`: unusually strong reference with direct architectural/product relevance.
- `A`: strong reusable patterns.
- `B`: useful selected ideas, but substantial adaptation required.
- `C`: limited/overlapping value.
- `D`: weak reference, misleading implementation claims, or better upstream source exists.

---

# Current candidate register

| ID | Source / idea family | Area | Evidence | Grade | State | Main reusable value |
| --- | --- | --- | --- | --- | --- | --- |
| REF-001 | PHENOMVALENCE/JARVIS-OS | agent authority / desktop actions | CODE-FIRST | A | CANDIDATE | typed actions, permission/risk boundary, deterministic requests bypass LLM, effect verification, safer deletion/audit patterns |
| REF-002 | Ouru77/ev-assistant | local desktop assistant | DOCS-FIRST | B | PARKED | offline-first voice/browser/screen routing, destructive confirmations, memory and desktop-assistant UX |
| REF-003 | moeru-ai/airi | computer-use / desktop character | DOCS-FIRST | A | CANDIDATE | computer-use and local desktop-agent reference, RAG/memory/UI patterns; stronger reference than generic Jarvis clones |
| REF-004 | IRISX-AI/IRIS-Mini | realtime multimodal desktop UI | DOCS-FIRST | B | PARKED | Gemini Live-style realtime interaction, React/Tailwind/Framer/Three.js UI, Socket.io and Windows setup/integration patterns |
| REF-005 | SreejanPersonal/JARVIS-AGI | legacy Jarvis clone | DOCS-FIRST | C | PARKED | conceptual comparison only; older/stale and license metadata requires care before any reuse |
| REF-006 | Wayfinder | routing / evaluation architecture | CODE-FIRST | A | CANDIDATE | pure preprocess -> feature extraction -> scoring -> recommendation -> explanation pipeline; validated config, JSON dry-run CLI, benchmark harness, offline tests, ADR discipline |
| REF-007 | Cavemem/Caveman reference family | memory / retrieval | CONCEPT | A | PARKED | local-first write boundary, progressive retrieval, technical-token preservation, internal-only compression; adapt rather than vendor |
| REF-008 | BlueRev Obsidian vault bridge | knowledge architecture | CONCEPT | A | CANDIDATE | Obsidian as source of truth, read-only indexing/retrieval, context-pack builder, gated canonical-memory promotion, explicit evidence/status classes |
| REF-009 | Solnest coding agent | autonomous coding gates | CODE-FIRST | B | CANDIDATE | post-edit deterministic quality gates; retain concept but replace shell `eval` and regex-only secret scanning with declared runners and real scanners |
| REF-010 | reverse-skill | capability routing / experience | CODE-FIRST | B+ | CANDIDATE | machine-readable authoritative routing, local tool index, field journal; experience promotion must be controlled rather than automatic |
| REF-011 | HyperClaw | authority / sandboxing | CODE-FIRST | A | CANDIDATE | monotonically restrictive authority layers, per-agent credentials, workspace none/ro/rw, network isolation and CPU/RAM limits |
| REF-012 | nexu-io/open-design | BLUECAD artifacts / agent runtimes | CODE-FIRST | S | CANDIDATE | refreshable Live Artifacts with provenance/snapshots/connector policy; declarative agent-runtime adapters |
| REF-013 | isdvsv/bug-hunter | autonomous coding runtime | CODE-FIRST | A | CANDIDATE | canonical JSON run state, single-writer lock, baseline, dry-run, resume, chunking, hash cache, payload validation, canary-first changes, exact scope |
| REF-014 | avivl/claude-007-agents | multi-agent orchestration | CODE-FIRST | D | REJECTED | negative reference: several components advertised as real use simulated MCP/task execution/mock analysis and random architecture detection |
| REF-015 | mrveiss/AutoBot-AI | approvals / workflow orchestration | CODE-FIRST | A+ | CANDIDATE | persistent approval lifecycle, revision/resubmit, workflow DAG, explicit dependency semantics, approval inbox, bounded remembered approvals |
| REF-016 | Jacobdrosol/NexusAI | distributed workers / authority | CODE-FIRST | A+ | CANDIDATE | worker readiness/capability attestation, typed least-privilege bot blueprints, credential references, payload-bound one-shot approvals, robust scheduler |
| REF-017 | Solnest-AI/echo-agent | untrusted-content boundary | CODE-FIRST | A | CANDIDATE | deterministic lanes before model calls, sealed no-tool reasoning for untrusted text, strict structured output, ID whitelist, fail-soft deterministic fallback |
| REF-018 | grabbly/lanehub | multi-agent identity | CODE-FIRST | B+ | CANDIDATE | stable actor identity independent of model prose, per-agent credential/endpoint, merged provenance-preserving feed |
| REF-019 | Lessan / linux-autonomos-agent | learning / tool effectiveness | CODE-FIRST | B- | PARKED | empirical tool-effectiveness journal and retrieval of past approaches; needs contextual metrics and must never expand authority automatically |
| REF-020 | ZYRAXON browser / Jarvis browser family | browser/computer use | CODE-FIRST | C | SUPERSEDED | selected browser automation ideas only; AIRI/Hermes/Nexus-style references are stronger for the relevant boundaries |
| REF-021 | zyraxon-code | coding UI/editor | CODE-FIRST | D | REJECTED | insufficient unique value over studying VS Code/upstream coding-agent primitives directly |
| REF-022 | Hermes Agent family | local agent / browser / tools | CAPTURED | A? | CAPTURED | potentially strong local-agent and browser/tool infrastructure reference; requires focused code-first audit before promotion |
| REF-023 | Rizzo-PI / Rizzo-pii and similar specialist inference systems | engineering AI efficiency | CAPTURED | — | CAPTURED | future intake family: software-side inference/engineering specialization may matter more than raw hardware scaling; re-audit exact version/repo before extracting JarvisOS requirements |

---

# Detailed reusable patterns

## REF-001 — PHENOMVALENCE/JARVIS-OS

### Keep / adapt

- The model should propose a **typed action**, not receive an unrestricted shell.
- Explicit permission and risk metadata belongs to the action contract.
- Deterministic requests should bypass the LLM when their intent is already known.
- Destructive file operations should prefer recoverable semantics such as Recycle Bin/trash instead of permanent deletion where feasible.
- Action execution should verify the resulting effect rather than assume that a command succeeded because the process returned.
- Audit history should resist silent tampering; hash-chained or otherwise integrity-protected local action history is worth evaluating.

### Do not copy blindly

JarvisOS already has stronger product-specific authority invariants. Any imported action abstraction must fit the existing execution spine rather than creating a parallel authority system.

## REF-002 — ev-assistant

Potentially useful as an end-user interaction reference for:

- offline-first assistant UX;
- voice -> backend router -> local model -> TTS flow;
- browser/screen tool integration;
- destructive-action confirmations;
- long-term memory and optional screen vision.

Do not treat its routing or safety model as authoritative without a deeper code-first audit.

## REF-003 — AIRI

Use primarily as a mature comparison target for:

- desktop agent embodiment and continuous presence;
- computer-use interaction;
- local memory/RAG integration;
- multimodal/animated operator UX;
- separation between character/persona presentation and underlying tools.

AIRI is a stronger comparison point than small generic “Jarvis clone” repositories for desktop interaction design.

## REF-004 — IRIS-Mini

Potentially useful UI/runtime references include realtime multimodal interaction, a polished React/Tailwind/Framer/Three.js presentation layer, Node/Socket.io realtime transport, and Windows integration/setup flows. These are reference ideas, not a reason to introduce those frameworks into JarvisOS without a spec.

## REF-005 — JARVIS-AGI

Retain only as a historical/popular-comparison reference. It is older/stale relative to better current projects, and its license metadata was not a clean basis for direct reuse. Prefer extracting generic concepts rather than code.

## REF-006 — Wayfinder

### Strong patterns

A small deterministic decision core structured as:

`preprocess -> feature extraction -> scoring -> recommendation -> explanation`

Other useful practices:

- validated configuration with reliable round-trip behavior;
- deterministic `--dry-run` and machine-readable JSON output;
- benchmark/evaluation harness treated as product infrastructure;
- offline tests;
- explicit ADRs for durable decisions.

### Explicit non-goals

Do not copy a simplistic local-vs-cloud binary, complexity-only routing, or premature gateway/API/key infrastructure merely because the reference contains it. JarvisOS provider and authority rules are already more specific.

## REF-007 — Cavemem/Caveman memory patterns

Candidate memory principles:

- local-first write authority;
- progressive retrieval rather than indiscriminate context loading;
- preserve engineering identifiers, units, chemical names, equations, filenames, IDs, and other technical tokens through compression;
- compression/summarization should remain an internal representation optimization, not silently replace canonical evidence;
- promotion into durable memory should be gated.

## REF-008 — BlueRev Obsidian vault bridge

Retain the hybrid architecture:

- Obsidian remains the human-readable/source-of-truth knowledge vault where appropriate;
- JarvisOS gets a read-only vault index/retrieval layer before any write integration;
- a Context Pack Builder selects bounded source material for a task;
- only stable summaries/decisions are candidates for canonical JarvisOS memory;
- source cards, protocols, and papers remain retrievable evidence rather than copied wholesale into another database;
- explicit statuses such as `canonical`, `candidate`, `measured`, `to_measure`, `future`, and `archive` prevent uncertain engineering knowledge from becoming fact accidentally.

## REF-009 — Solnest coding agent

The valuable concept is **automatic deterministic feedback immediately after an agent edit**. Test, lint, type, secret, or policy gates should be hooks in the execution loop rather than instructions that the model may forget.

Do not reproduce weak implementation details observed in the reference:

- shell `eval` for test commands;
- regex-only secret scanning;
- staged-diff-only coverage where broader repository evidence is required;
- exclusions that create obvious scanning blind spots.

Use declarative command definitions and purpose-built scanners.

## REF-010 — reverse-skill

Candidate architecture:

- machine-readable routing is canonical;
- Markdown is a human-readable view, not the authority database;
- maintain a local capability/tool index so agents can discover what actually exists;
- record completed-task outcomes and failure patterns in a field journal;
- promotion from one observed case into a canonical routing rule requires deterministic criteria or explicit review.

## REF-011 — HyperClaw

Adopt the **monotonic restriction** principle:

`global policy -> provider/runtime -> agent -> sandbox -> subagent`

Each lower layer may remove authority but must not re-grant a capability denied above it.

Useful resource boundaries include:

- workspace access `none / read-only / read-write`;
- network `none / isolated bridge / host` or equivalent bounded postures;
- per-agent credentials instead of shared ambient secrets;
- CPU/RAM limits;
- distinct blast radii for conversational/UI, coding, browser, remote/mobile, and engineering agents.

## REF-012 — open-design

### Live Artifacts for BLUECAD

An artifact can be persisted as a refreshable object rather than a one-off static file:

`template + data binding + provenance + connector policy + snapshots + refresh history`

Candidate BLUECAD applications:

- reactor temperature/pressure profiles;
- mass/energy balance summaries;
- Sankey diagrams;
- equipment datasheets;
- convergence dashboards;
- sensitivity/parametric plots;
- economic reports;
- simulation validation reports;
- PFD or scene overlays with live values.

When underlying engineering state changes, the artifact can refresh without asking an LLM to recreate its presentation from scratch. Failed refresh should preserve the last known-good snapshot.

### Declarative agent runtimes

Treat Codex, Claude Code, Qwen/Hermes/local CLIs, and future agent runtimes as data-driven runtime definitions containing executable/version probe, authentication mode, stream format, prompt transport, model selection, and capabilities rather than bespoke orchestration classes for every model.

## REF-013 — bug-hunter

Strong patterns for autonomous repository work:

- canonical machine-readable run state; Markdown only renders it;
- single-writer lock;
- baseline captured before modifications;
- dry-run as a first-class mode;
- resume after interruption;
- chunking for large codebases;
- content/hash cache to avoid reprocessing unchanged files;
- schema/payload validation before subagent launch;
- canary-first autonomous modifications before bulk application;
- retry/backoff and execution journal;
- exact branch/PR/file scope.

A future JarvisOS coding run record could include:

`run_id, exact_base_sha, scope, objective, constraints, files_owned, baseline, produced_changes, evidence, findings, retries, state`.

## REF-014 — claude-007-agents

Retain as negative evidence. During audit, components described as “real implementation” contained simulated MCP connections, synthetic task objects, `simulateAgentExecution()`, mock filesystem lists, and even random architecture-pattern detection. Do not import an architectural claim from a README until the relevant execution path is proven in code/tests.

## REF-015 — AutoBot-AI

### Persistent approval lifecycle

Approval should be a durable workflow object rather than a transient yes/no modal. Candidate states include:

`pending -> approved / rejected / revision_requested -> resubmitted`

Useful fields include requester agent, workflow/step, resource, before/after intent, evidence/reason, decision maker, comments, linked task, timestamps, and risk.

### Approval memory

Remembered approvals may be useful only when scoped structurally by project/user/capability/resource/risk/expiry. Do **not** copy broad shell wildcarding such as treating `npm install *` as equivalent authority.

### Dependency semantics

Different workflow dependencies should be explicit:

- `DATA`: B consumes A's output;
- `RESOURCE`: actions contend for the same mutable resource;
- `ORDER`: only execution ordering is required;
- `TRANSACTIONAL`: actions must complete as one rollback/commit unit;
- `NONE`: independent and safe to parallelize.

This is directly relevant to future BLUECAD simulation/mesh/solver/report pipelines.

## REF-016 — NexusAI

### Worker readiness and capability attestation

A configured agent/worker is not automatically dispatchable. Readiness should verify, as applicable:

- enabled state;
- registered/online worker;
- declared provider/model capability;
- required tool availability;
- runtime probe/attestation;
- authentication readiness;
- model catalog availability;
- referenced credential existence without exposing the credential.

This is a strong reference for a future JarvisOS distributed-worker registry spanning workstation, secondary PC, Raspberry Pi/edge hardware, GPU nodes, sensors, or BlueRev gateways.

### Typed least-privilege agent blueprint

An agent definition should eventually describe more than a system prompt:

`role, accepted inputs, produced outputs, capabilities, resource scope, risk ceiling, network posture, model policy, credential references, completion contract`.

Raw credentials should never be embedded in exportable agent configuration; store opaque references to a vault/environment/credential service.

### One-shot payload-bound approval

For high-impact mutations, bind the approval to:

`actor + action key + canonical payload digest + expiry + unused state`.

If any action parameter changes, the approval is invalid. Consumption is one-time and fail-closed.

Keep this distinct from a broader standing grant such as “may create plots in this workspace”.

### Scheduling

Prefer:

`schedule -> validated target -> dedupe -> readiness/authority guard -> run record -> bounded retry/backoff -> terminal outcome`

rather than `cron -> prompt`.

Track run identity, scheduled time, overlap policy, retries, dedupe key, terminal state, and retention.

## REF-017 — echo-agent

Strong trust rule:

> Untrusted content may inform model judgment, but must not automatically enter a tool-enabled authority context.

Candidate ingestion flow:

`email/web/PDF/document -> sealed no-tool reasoner -> strict structured output -> deterministic validation/whitelist -> separately authorized action path`

Additional useful patterns:

- deterministic VIP/mute/reply lanes before model calls;
- bounded context bundle;
- no inherited tools/settings for the untrusted-text model call;
- whitelist model-generated references against IDs that actually existed in the input bundle;
- deterministic fallback when the model fails or emits invalid structure;
- soft/stateful changes with visible read-back instead of silent destructive deletion;
- idempotent/dry-run unattended jobs.

This should inform future handling of email, external documents, websites, issue text, pasted prompts, and uploaded third-party artifacts.

## REF-018 — LaneHub

Do not copy Telegram-specific architecture unless needed. Retain the identity principle:

- each agent has a stable authenticated `actor_id` independent of its prose/persona;
- credentials are isolated by actor/lane;
- messages/events preserve actor provenance;
- a shared feed can be merged without losing who produced each item.

For future Codex/Claude/Jarvis/local-agent collaboration, “Claude said X” should be backed by authenticated run/actor provenance rather than a text prefix that any process can imitate.

## REF-019 — Lessan / linux-autonomos-agent

Potentially useful:

- action journal;
- empirical tool success/failure tracking;
- retrieval of similar previous tasks before choosing a tool;
- effectiveness ranking that discounts tiny sample sizes.

JarvisOS would need a stricter model. Tool effectiveness should be segmented by capability, environment/version, input class, latency, cost, failure mode, and deterministic verifier. Historical success may influence routing, but it must **never grant additional authority**.

## REF-020 — ZYRAXON browser family

Keep only isolated browser/grounding observations that are not already covered by stronger references. Do not prioritize a dedicated adoption path while AIRI/Hermes/Nexus-style boundaries provide stronger material.

## REF-021 — zyraxon-code

Rejected as a primary reference because most useful editor/coding-agent concepts are better studied in their actual upstream projects (for example VS Code or the relevant agent runtime) instead of through a derivative/rebranding layer.

## REF-022 — Hermes Agent

Captured for a future dedicated code-first audit because it may be valuable for:

- local/open agent operation;
- browser/tool execution;
- coding and shell/tool orchestration;
- model portability.

Do not promote any of these as JarvisOS requirements until exact current code and licensing are audited.

## REF-023 — Rizzo-PI / Rizzo-pii family

This entry intentionally records the **intake trigger**, not an assumed implementation. The useful hypothesis is that European/local AI independence and engineering usefulness may improve substantially through software/inference innovations, specialization, routing, compression, and task-specific execution rather than only through larger hardware investment.

When a new Rizzo-PI/Rizzo-pii version or related project is proposed, re-open the exact repository/version and extract only verified engineering-relevant mechanisms. Do not infer features from social-media descriptions.

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
       v
Monotonic Authority Chain
       |
       v
Workflow Graph
(DATA / RESOURCE / ORDER / TRANSACTIONAL)
       |
       +---- Standing Grant
       +---- Payload-bound One-shot Permit
       |
       v
Worker Readiness / Capability Attestation
       |
       v
Checkpoint / Baseline / Exact Scope
       |
       v
EXECUTION
       |
       v
Deterministic Verifier
       |
       v
Domain State / Live Artifact
       |
       v
Audit + AgentRun + Experience Journal
```

This synthesis currently draws primarily from REF-001, REF-006, REF-010 through REF-019.

---

# BlueRev / engineering-specific intake rule

This register is not limited to software projects. Future BlueRev material belongs here when it may alter product or engineering capability, including:

- photobioreactor geometry, materials, membranes, ETFE, pumping, gas exchange, mixing, sensors, harvesting, fouling control, microorganism viability, illumination, thermal control, mooring, offshore power, and field instrumentation;
- CFD/FEM/process simulation methods;
- digital twins, state estimation, optimization, control, uncertainty, data reconciliation, and experiment design;
- CAD/manufacturing methods;
- scientific papers, patents, standards, datasets, hardware boards, cameras, edge computers, pumps, valves, probes, or lab equipment;
- funding-relevant technical capabilities that may be difficult to acquire later.

Record the engineering claim separately from the source's marketing language, and mark uncertain technical claims as such until supported by primary evidence.

---

# Promotion rule

When a candidate becomes relevant to current product work:

1. revalidate the source against its current version when recency matters;
2. check licensing before copying code or substantial implementation detail;
3. state the concrete JarvisOS/BLUECAD/BlueRev problem it solves;
4. run the minimum-necessary test;
5. create or update the appropriate backlog/spec/ADR through the normal repository process;
6. change this entry to `PROMOTED` and link the authoritative record;
7. keep implementation status exclusively in `docs/specs/STATUS.md`.

# Maintenance rule

Prefer updating an existing entry over creating synonyms. Preserve negative findings. When an audit changes an earlier conclusion, append the new evidence and mark the old conclusion superseded rather than silently erasing provenance.

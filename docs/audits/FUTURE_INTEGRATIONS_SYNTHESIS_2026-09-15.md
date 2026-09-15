# Future integrations synthesis — 2026-09-15

Status: maintainer-directed strategy/intake synthesis; **not implementation authority**  
Base: `master` `74594515e6ece89dba78923230f263bc6091d9f6`  
Canonical implementation state remains exclusively in `docs/specs/STATUS.md`.

## Purpose

Preserve the future JarvisOS directions discussed after BRAINSTORM-1 without creating a second roadmap or prematurely authorizing implementation.

This document translates recent external candidates and product ideas into the architecture that now exists in the repository:

- JarvisOS remains the authoritative control plane for canonical project/domain state, provider credentials, sensitivity, egress, budget/ledger, approvals, promotion and repository/development authority.
- NousResearch Hermes Agent is the selected replaceable conversation/agent runtime underneath JarvisOS: session/agent loop, tool orchestration, bounded delegation/subagents and related runtime mechanics. `docs/DECISIONS.md` owns that boundary.
- The frozen Jarvis persona roster remains `docs/strategy/JARVISOS_CORE_TEAM_V1.md`; persona identity is independent from the model/provider used on a given turn.
- Existing context/action contracts, Project Knowledge, Development, Coding, Brainstorm, Roadmap, repository truth and development-pipeline owners are reused rather than duplicated.
- Local/open-weight inference is the default private/cheap compute path where qualified; external frontier compute is an escalation path behind Jarvis-owned policy, sanitization, credentials and accounting.
- Engineering capability should be assembled by capability-slot bake-offs against strong upstreams, not by installing every interesting project.

## Near-term sequencing direction

This is strategic sequencing only; each implementation still requires normal spec/readiness authority.

1. Finish `122 JARVIS-DEVELOPMENT-ACTIONS-1` and expand the current development pipeline with GitHub Education/Copilot Student and Google AI Pro/Jules without creating a second delivery authority.
2. Run the local Qwen3.8-27B bake-off: current Unsloth GGUF versus ISTA-DASLab GSQ-RCO GGUF candidates under the same llama.cpp/runtime/evaluation harness.
3. Integrate pinned Hermes as the Jarvis sidecar runtime with persistent sessions, memory/session retrieval, profiles and bounded subagent/council orchestration.
4. Make llama.cpp/Qwen a first-class local inference backend and qualify agent/tool behavior rather than assuming model fitness from general benchmarks.
5. Add the Jarvis agent-inference/provider boundary required for Hermes tool-call loops; keep credentials, egress, budget and route authority in JarvisOS.
6. Add secure cloud/frontier escalation with local sensitivity classification, PII/IP sanitization, included/free quota first, and no silent PAYG fallback.
7. Move to real engineering capability bake-offs, using the existing S/A candidate families and the PBR/BlueRev stack as the first serious vertical integration target.
8. Keep self-update, generic PTY, broad computer-use and uncontrolled self-improvement deferred unless a concrete beta blocker makes them necessary.

## Hermes product direction

### Named persistent experts

Use the frozen roster rather than inventing new agents. Initial council-capable personas include Jarvis, Tony, Sheldon, Linus, Isaac, Gregor, Spock, TARS, Sherlock, Q and Alfred.

- A persona is configuration/mission/tool/skill/memory policy, not a fixed model.
- Persistent named experts should map naturally to Hermes Profiles or the closest upstream-supported persistent-profile abstraction.
- Disposable one-off work should use bounded Hermes delegation/subagents rather than creating more permanent personas.
- Jarvis remains chair/orchestrator and authority interface; expert agents provide proposals, critiques, evidence and implementation suggestions.
- A council transcript must remain user-steerable. The operator may interrupt, approve/reject reasoning, request another round, or authorize a downstream proposal/action.
- Same-weight agents are acceptable for routine debate, but high-value decisions should add model diversity or frontier escalation when independent failure modes matter.

### Memory and retrieval

Use Hermes session/memory/search mechanics for conversational continuity where they fit, but preserve the authority split:

- Hermes: session continuity, conversational memory, user/persona procedural memory, session search/retrieval, subagent context mechanics.
- JarvisOS: Project Knowledge, engineering evidence, canonical assumptions/parameters/decisions, Roadmap, Brainstorm promotion, Development/Coding state, provider policy and audit.
- Memory must never silently promote a remembered statement into canonical engineering truth.
- Useful conversational material may be promoted through the existing proposal/promotion mechanisms with provenance back to the source conversation.
- Workspace/project isolation is required so retrieval cannot leak unrelated project history.

### Runtime/deployment

Prefer a pinned direct Hermes dependency behind a process boundary/adapter rather than copying or recreating the runtime. Local Windows is the first beta path; persistent VPS/container/serverless deployment remains a later topology option. Moving Hermes off the laptop must not move authority, secrets or canonical state out of JarvisOS.

Hermes background self-review, auto-skill mutation, cron, raw host terminal/browser access and canonical Kanban ownership remain disabled/deferred until separately justified and bounded. Reuse upstream mechanics aggressively only where they do not create a second authority plane.

## Local-model direction

### Qwen3.8-27B

Treat local Qwen as the default candidate compute for many personas, not as the persona identity itself.

Benchmark at least:

- current Unsloth Qwen3.8-27B GGUF baseline already used by the maintainer;
- ISTA-DASLab GSQ-RCO Qwen3.8-27B GGUF candidates sized to fit the current 12 GB laptop GPU / 32 GB RAM envelope, especially the most promising ~3-bit operating points.

Use the existing/local-eval philosophy and measure Jarvis-relevant behavior:

- tool-call correctness and tool-result continuation;
- JSON/schema adherence;
- multi-turn stability;
- engineering reasoning/error finding;
- coding quality;
- persona adherence;
- memory/session-search tool usage;
- context-length degradation;
- TTFT, tokens/s, VRAM/RAM and failure recovery.

Keep llama.cpp as a first-class local backend rather than forcing every GGUF through Ollama. Generalize only after two real runtime backends expose stable duplication.

## Cloud/frontier compute direction

JarvisOS should expose model aliases/routes to Hermes rather than provider credentials.

Preferred order of use:

1. local qualified models;
2. already-included subscription entitlements where machine-accessible and policy-compliant;
3. free API/router quotas suitable for bounded external critique/fallback;
4. explicit paid APIs only when configured and permitted by the maintainer.

No silent transition from free/included quota to PAYG.

### Privacy/egress

Use REF-023 Rizzo PII or a stronger later candidate as the local PII/pseudonymization stage, but do not confuse PII with project IP. External packets also require Jarvis-owned sensitivity/IP sanitization and an honest decision when sanitization removes too much information for the remote model to be useful.

Useful route classes include:

- `LOCAL_ONLY`;
- `SANITIZABLE_EXTERNAL`;
- `EXTERNAL_WITH_CONFIRMATION`;
- `EXTERNAL_FORBIDDEN`.

Provider prompt caching should be treated as an optimization inside the Jarvis provider gateway/accounting plane, never as a new state authority.

## Knowledge/document ingestion directions

### `baidu/Unlimited-OCR`

Candidate document-ingestion engine for PDFs/scans/long technical documents. Potential role: extract structured text/Markdown and page provenance before Literature/Project Knowledge ingestion.

Do not let OCR output become canonical truth directly. Preserve original file/page references, extraction provenance, confidence/failure state and explicit promotion/reconciliation. Hardware fit on the current laptop and long-document quality require a local benchmark before promotion.

### Annota AI

Commercial/reference benchmark for OCR -> structured knowledge/wiki -> annotation/dataset -> model-training/MCP workflows. Useful primarily as product/UX/workflow reference and possible external integration, not as an automatic canonical knowledge store. Compare against the Jarvis Literature/Project Knowledge/Brainstorm pipeline before adopting overlapping storage.

### Anchor (`trybacked/anchor`)

Candidate semantic-model/provenance layer and MCP/query reference. Useful for entity/relation/definition modeling, provenance/confidence and human review patterns.

Jarvis Project Knowledge remains canonical. If Anchor is integrated, prefer read/export/interchange or derived semantic projection rather than a second authoritative project database.

### PESD / engineering-source intake

IChemE Process Engineering for Sustainable Development and similarly strong domain sources may be added as Literature/research-source connectors or curated source families. Source ingestion must preserve provenance/licensing/access terms and remain separate from canonical engineering acceptance.

## Meeting / speech / decision capture

Preserve the existing deferred speech-capture direction but broaden it from isolated voice notes to meeting/brainstorm ingestion.

Target flow:

`audio/recording -> immutable raw media reference -> transcript -> speaker/time provenance -> extracted summary/decisions/actions -> explicit promotion to Brainstorm/Roadmap/Project Knowledge/Coding`.

PLAUD-like hardware/services may be supported through import/export adapters when privacy, retention, API/export terms and user consent are acceptable, but the core feature should not depend on one vendor.

Do not add always-on/background recording by default. Raw audio/transcript and derived decisions must remain distinguishable. A model-generated summary is proposal evidence, not the meeting record itself.

## Desktop / companion UX

### Clicky / AI-buddy reference

Use Clicky/`heyclicky.com` as a UX benchmark for persistent assistant presence, lightweight summon/interruption, ambient status and conversational continuity. It is not an authority/runtime reference.

Any Jarvis desktop-companion treatment must reuse the existing sidecar/app shell and Hermes session identity rather than introducing another chat store, background agent authority or hidden provider path.

## Development/product bridge directions

### Design -> Coding promotion

Add a future bounded `Send request to Coding`/promotion path from Design/engineering context into the existing Coding/Development authority.

The promoted request should carry exact context/provenance, target subsystem, requested behavior, acceptance criteria, relevant repository/head identity and risk/action class. It creates a coding proposal/workpack; it must not directly mutate source code or merge.

This feature should become a natural consumer of Hermes reasoning/council output while keeping existing Coding and Development owners authoritative.

### Dev-pipeline worker expansion

GitHub Copilot Student, Jules/Google AI Pro, Codex/ChatGPT Plus, Claude Code/Claude Pro and existing GitHub Actions should remain workers/evidence sources inside one development control plane. Do not create one canonical queue per vendor. Preserve exact-head/CAS, independent review and deterministic CI.

Hermes DEV remains deferred unless later evidence shows a specific orchestration bottleneck that materially outweighs the complexity of adding it.

## Engineering directions

The S/A candidate families already in the canonical register remain the main engineering pool. The goal is capability-slot bake-off, not dependency accumulation.

### Thermo/process/bioprocess

Retain the current strong families: CoolProp/ChEDL/ThermoSTEAM, BioSTEAM/QSDsan, IDAES/Pyomo/WaterTAP, DWSIM/CAPE-OPEN and specialized engines such as Cantera/Reaktoro/TESPy/pycalphad.

### CAD/mesh/CFD/FEM

Retain CadQuery/OCCT, PicoGK family, Gmsh/Netgen/OpenFOAM/SU2/FEniCSx/CalculiX/Code_Aster and VTK/PyVista/ParaView/meshio behind typed adapters and canonical Jarvis engineering IR/evidence.

#### `isoAdvector/dictator`

Narrow deterministic OpenFOAM dictionary/configuration helper candidate. Potentially valuable because it reduces fragile hand-authored dictionary mutation. Treat it as a tool behind the OpenFOAM adapter, not a new modeling authority.

#### GenCFD / generative CFD research

Research candidate for future surrogate/generative field prediction or acceleration. Do not substitute it for validated CFD evidence in the first engineering beta. Promote only after deterministic solver baselines/evaluators exist and code/data/license/hardware quality are verified.

### Numerical and compiled tooling

#### CppJIT

Candidate for bounded JIT/native acceleration of engineering kernels or extension code. Before adoption compare it against existing Python/native-extension approaches and prove Windows/toolchain reproducibility, sandboxing, cache identity, deterministic build inputs and failure isolation. Never expose arbitrary model-authored C++ execution as an unrestricted Jarvis capability.

### Forecasting/environmental models

#### TimesFM 3

Candidate specialist time-series forecasting backend for telemetry/process/environmental series. Verify official release/license/features and benchmark against simpler statistical/baseline models before adoption. Treat forecasts as derived evidence with uncertainty, not canonical future truth.

#### WeatherNext 3

Candidate environmental/weather forecast source/backend relevant to outdoor PBR operations and digital-twin scenarios. Verify official access/license/runtime first. Environmental forecasts should enter through typed external-data provenance and uncertainty contracts.

### Wolfram

Extend the existing Wolfram family candidate to include Wolfram Cloud/MCP as a possible deterministic/symbolic computation tool. Preserve auth/privacy/budget boundaries and treat returned calculations as tool evidence, not state authority.

## Model specialization / training

Retain the existing REF-057 specialization/training family and the recent small-specialist-model lesson: a small model may outperform a frontier model on a narrow product task if the task/evaluator/data are strong.

Do not start broad fine-tuning before task-specific evaluators exist. First collect real Jarvis failures, build deterministic/graded evals, then compare prompt/skill/routing improvements against LoRA/fine-tuning/specialist models.

## Multi-agent/team references

### Paperclip and Hermes swarm/company demonstrations

Use Paperclip-style team organization and public Hermes multi-agent/swarm demonstrations as scenario/UX references only. The product should expose one coherent Jarvis with internal named experts from the frozen roster rather than a second visible company/queue manager.

Jarvis owns council composition, operator steering and action authority; Hermes supplies profiles/session/delegation/runtime mechanics.

## Deployment / sovereign infrastructure

### Persistent Hermes cloud/VPS/serverless

Keep DigitalOcean/VPS/container/serverless Hermes deployments as a future availability option so Jarvis is not tied to the maintainer laptop. Required before promotion: process isolation, secrets boundary, network policy, persistence/backup/restore, upgrade pinning, cost caps and reconnect semantics.

### Z.ai sovereign/partner direction

Treat Z.ai sovereign/partner infrastructure as a strategic deployment/provider option, not a product dependency. Revisit when Jarvis requires persistent local-region/private inference or when a concrete partner/credit programme materially changes cost/control.

## Provider/free-compute strategy

Use OpenRouter/free routes and other legitimate free monthly quotas only as opportunistic external compute behind Jarvis routing. They are not reliability-critical dependencies and must record the actual model/provider selected.

The provider gateway should know whether a route is `local`, `included_subscription`, `free_quota`, or `paid`, and fail closed rather than silently crossing economic class.

## Deferred directions retained deliberately

The following remain worth preserving but are not beta prerequisites:

- Hermes automated skill/background self-improvement beyond bounded, auditable promotion;
- Honcho or another shared semantic long-term memory layer beyond native Hermes memory/session search + Jarvis canonical knowledge;
- generic desktop/computer-use authority;
- 125 self-update;
- 126 generic PTY;
- broad always-on recording;
- autonomous provider/credential acquisition;
- unbounded model-generated code execution;
- a second canonical Kanban/task manager;
- replacing deterministic engineering solvers with generative approximators before validated evaluators exist.

## Promotion rule for this synthesis

An item in this document becomes implementation work only when:

1. the exact current Jarvis owner/gap is demonstrated;
2. the upstream/product/source is freshly revalidated;
3. reuse mode and licensing/security/deployment are resolved;
4. minimum prototype/evaluator evidence closes the real uncertainty;
5. canonical ownership and failure semantics are explicit;
6. the normal ADR/spec/readiness path promotes it into `docs/specs/STATUS.md`.

Until then, this file preserves direction and intent only.
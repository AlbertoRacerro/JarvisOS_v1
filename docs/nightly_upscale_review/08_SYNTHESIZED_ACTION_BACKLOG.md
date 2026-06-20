# Synthesized Action Backlog

This document consolidates the nightly upscale review into a smaller, ordered backlog. It keeps the foundation work that protects future scale-up and removes items that are useful only after provider, runner, artifact, or Workbench expansion begins.

## Synthesis Rules

- Keep items that protect safety, data durability, or provider neutrality before the next implementation milestone.
- Defer items that are only needed after a second provider, second runner script, artifact viewer, or BlueRev Workbench exists.
- Reject infrastructure that would make a local-first V0 heavier without solving an immediate risk.
- Prefer design gates and narrow contracts before broad runtime refactors.

## Action Backlog

| ID | Title | Severity | Action Type | Prerequisite | Reason | Risk If Skipped | Affected Modules | Complexity | Testing Requirement | Recommended Milestone |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AI-01 | Pragmatic AI policy modes | blocker | narrow foundation | completed 0C-D and 0E-D2 adapter hardening | Early JarvisOS needs FAST_DEV speed while preserving structural secret protection and a future STRICT_IP path. | Strict content blocking slows public/internal exploration, while no policy mode leaves future stricter behavior unclear. | `backend/app/modules/ai`, docs | low | default mode tests; FAST_DEV allow/block tests | 0E-D3 |
| AI-02 | Provider-neutral AI status and settings shape | blocker | design then narrow refactor | AI-01 policy mode foundation | Current settings and status are still Scaleway-shaped in places. | A second provider will force duplicate flags and confusing UI wording. | AI settings/status routes, frontend AI page, docs | medium | settings/status response tests; frontend build when touched | 0E-D3/0E-D4 |
| AI-03 | Provider-neutral usage accounting shape | high | narrow schema/service refactor | AI-02 | Usage counters are currently tied to Scaleway smoke behavior. | Cost guard and token caps become inconsistent across providers or task types. | AI settings, token guard, schema, tests | medium | usage cap tests; old DB compatibility test | 0E-D4 |
| AI-04 | Minimal AI audit event envelope | high | contract and helper refactor | AI-01 | AI event payloads are useful but remain free-form. | Future router/provider paths become difficult to audit and redact consistently. | AI services, events service, tests | low | event shape tests; prompt/key redaction tests | 0E-D5 |
| AI-05 | No-network provider test fixture | medium | test hardening | before next AI provider code | Provider tests currently rely on local monkeypatch discipline. | Future tests could accidentally call external providers. | backend test fixtures, AI tests | low | fixture proves sockets/network are blocked unless explicitly allowed | 0E-D5 |
| AI-06 | Reconcile fake provider with provider-neutral adapter interface | medium | small compatibility refactor | before second provider | The live Scaleway path now has an adapter, while fake provider behavior still follows older assumptions. | Provider-neutral status/router work may need special cases for fake mode. | AI providers, gateway tests | low | fake provider response envelope tests | before 0F-C |
| ART-01 | Data-root-relative artifact storage key for new writes | high | storage hardening | before artifact viewer or file ingestion | Absolute filesystem paths are fragile across data-root moves, backup restore, and future storage backends. | Artifacts may become non-portable or unsafe to expose in UI. | files/artifact registry, runner artifacts, schema | medium | relocation tests; path traversal tests | 0E-E |
| ART-02 | Minimal artifact taxonomy and immutable metadata | high | small schema/service refactor | ART-01 or same milestone | Artifacts need safe type handling before previews, downloads, or imports. | Unsafe parser assumptions or untraceable generated files. | file/artifact registry, runner service, docs | medium | metadata tests for type, size, hash, storage key | 0E-E |
| DB-01 | Old SQLite snapshot tests and formal migration trigger | high | test/policy hardening | before next schema-heavy change | Local users will keep existing SQLite files between milestones. | A schema change can silently break existing installations. | schema, database init, tests, docs | medium | open older DB fixture; initialize without data loss | 0E-F |
| DB-02 | Payload schema version invariant | medium | documentation and light validation | before more JSON payloads | JSON payloads are useful now but need version markers where long-lived. | Future migrations cannot distinguish payload generations. | schema, services, docs | low | tests for new long-lived payload writes when implemented | 0E-F or next schema change |
| RUN-01 | Runner V1 manifest design gate | high | design gate | before second reviewed script | V0 can run one reviewed deterministic kind; a second script needs declared inputs, outputs, limits, and artifacts. | Runner safety weakens by accumulating implicit script assumptions. | runner docs, future manifest validator | medium | manifest validation test plan | 0F-A |
| RUN-02 | Runner service split only when expansion starts | medium | conditional refactor | second script or runner UI approved | Runner service coordinates implementation lookup, jobs, execution, logs, artifacts, and SimulationRun updates. | It becomes a monolith if expanded without separation. | runner service, tests | medium | existing runner tests plus split-specific unit tests | 0F-B |
| FE-01 | Split frontend API client by domain | medium | frontend refactor | next frontend-touching AI/status milestone | The current client is convenient but will grow quickly with AI, runner, and artifacts. | UI changes become harder to review and type safely. | `frontend/src/api` | low | frontend build | 0E-G |
| FE-02 | Split AI page into thin panels | medium | frontend refactor | provider-neutral AI UI change | The AI page mixes status, settings, smoke tests, smoke console, and cost display. | Future Supervisor or provider UI work becomes high-risk. | AI page components | medium | frontend build; no UI redesign | 0E-G |
| DOC-01 | Current operating model and backup/export runbook | medium | documentation | ART-01 planned | Milestone history is detailed, but current operating rules and backup assumptions are scattered. | Users may confuse repo path, data root, DB, artifact bytes, and provider settings. | README, docs | low | docs review only | 0E-E or 0E-F |
| WORK-01 | BlueRev Workbench design gate prerequisites | blocker | design gate | AI-01 through ART-02, RUN-01, DB-01 | Workbench combines AI, runner, artifacts, decisions, SimulationRuns, and domain objects. | Product UI could lock in unstable boundaries. | backend domain, frontend Workbench docs | high | design checklist; no runtime tests initially | 0G-A |

## Items Simplified From The Previous Backlog

- Generic credential handling is folded into provider-neutral AI status/settings unless a second provider is approved. For now, no plaintext secrets in SQLite remains the invariant.
- Event retention/export is folded into the operating model and backup/export runbook until event volume becomes a measured problem.
- Source/provenance schema is deferred until Scientific Data Connectors or file parsing is explicitly approved.
- Artifact viewer design remains deferred until relative storage keys and taxonomy exist.
- CAD/PFD handling remains an opaque artifact policy question for a later design gate.
- Shared API error envelope is deferred until the next route family starts duplicating error parsing.

## Items Rejected For The Near Term

- Object storage implementation.
- Container, queue, worker, or remote runner execution.
- Universal file parser or ingestion framework.
- CAD, CFD, FEM, PFD, or geometry tooling.
- Full BlueRev Modeling Workbench UI.
- Supervisor AI endpoint.
- Provider-specific bot UI.
- AI router that can make final authority decisions.

## Immediate Blockers Before The Next Implementation Milestone

1. Keep `FAST_DEV` as the current default policy mode.
2. Preserve structural secret protection at boundaries.
3. Continue provider-neutral AI status/settings/usage contracts.
4. Define the minimal AI audit event envelope before router or second-provider work.
5. Add or plan a no-network provider test fixture before more provider work.

These blockers do not require a new provider, a router, a Supervisor endpoint, or BlueRev modeling.

# Final Upscale Decision Gate

This decision gate reviews the nightly upscale documents as a second pass. It decides what to keep, what to delay, and what must be true before JarvisOS moves toward larger AI, runner, artifact, or BlueRev workflows.

## What Was Inspected

- `00_NIGHTLY_UPSCALE_REVIEW_INDEX.md`
- `01_SYSTEM_UPSCALE_THREAT_MODEL.md`
- `02_STORAGE_AND_ARTIFACT_STRATEGY.md`
- `03_DATABASE_SCALEUP_AND_MIGRATION_STRATEGY.md`
- `04_AI_ROUTER_AUTHORITY_AND_PROVIDER_STRATEGY.md`
- `05_RUNNER_SANDBOX_AND_EXECUTION_STRATEGY.md`
- `06_FRONTEND_API_MODULARITY_STRATEGY.md`
- `07_FINAL_ARCHITECTURE_HARDENING_BACKLOG.md`

The review covered storage and artifacts, database scale-up, SQLite/PostgreSQL readiness, AI router and AuthorityPolicy boundaries, provider neutrality, secrets handling, runner safety, frontend/API modularity, tests, documentation, and future BlueRev Workbench readiness.

## Completeness Decision

The nightly review is complete enough to guide the next foundation milestones. It does not need another broad architecture review before implementation resumes.

However, the previous documents should be treated as source material, not as an implementation order. The authoritative output is now:

- `08_SYNTHESIZED_ACTION_BACKLOG.md`
- this decision gate

## Contradictions Resolved

### AuthorityPolicy Versus Provider-neutral Status

One document recommends provider-neutral status/settings before AuthorityPolicy. Another recommends AuthorityPolicy first.

Decision: define pragmatic policy modes first. `FAST_DEV` is the current default and should allow normal public/internal technical prompts while protecting structural secrets at boundaries. Deterministic AuthorityPolicy remains future architecture for stricter `STRICT_IP` mode and should not block early-stage development.

### Artifact Storage Timing

One thread recommends relative artifact paths before Workbench or artifact viewer work. Another warns against immediate migration.

Decision: do not perform a broad migration now. The next artifact milestone should make new writes use data-root-relative storage keys and keep compatibility reads for older absolute paths.

### Migration Tooling Timing

One document says not to add Alembic yet. Another lists migration trigger and old DB tests as high priority.

Decision: add old SQLite snapshot tests and a formal migration trigger policy before the next schema-heavy milestone. Do not add Alembic until schema churn justifies it.

### Frontend Split Timing

One document places frontend splitting after AI/storage work. Another recommends splitting during provider-neutral AI work.

Decision: do not split as a standalone project. Split frontend API modules and AI page panels when the provider-neutral AI UI is already being touched.

### Runner Manifest And Service Split

One document recommends manifest and split before expansion. Another separates the two into later milestones.

Decision: perform the runner manifest design gate before a second script. Split runner service only when a second script or runner UI is approved.

### Future Infrastructure

Object storage, container sandboxing, remote execution, queues, universal parsers, and broad repository layers were mentioned as future-compatible ideas.

Decision: keep them only as compatibility constraints. Do not implement them in the next milestones.

## Overengineering Removed

- Object storage implementation is not needed for local V0.
- Docker/container sandboxing is not needed for the next runner step.
- Remote execution, queues, workers, and scheduling remain out of scope.
- A universal file ingestion/parser framework is out of scope.
- CAD, CFD, FEM, PFD, and geometry handling remain out of scope.
- A full Workbench UI is premature.
- A Supervisor endpoint is premature.
- A provider-specific bot UI should not be built.
- A broad repository/service layer rewrite is not justified.

## Underengineering Risks Added

- Absolute artifact paths need a forward-compatible storage key policy before any viewer or file ingestion.
- AI audit events need a small typed envelope before router or second-provider work.
- Provider usage accounting should stop being Scaleway-shaped before more providers exist.
- Backup/export needs a simple manifest, artifact hashes, and data-root guidance.
- Frontend error parsing will become brittle as route families grow.
- Old SQLite database compatibility tests should exist before the next schema-heavy change.
- The fake provider path should be reconciled with provider-neutral adapter assumptions before adding another provider.
- Automated provider tests need a no-network guard fixture before more provider code is added.

## Final Architecture Invariants

- No plaintext secrets in SQLite, frontend state, docs, events, or logs.
- AI may recommend, but local policy decides.
- `FAST_DEV` is the current default AI policy mode.
- Structural secrets are blocked locally before any external provider call.
- Deterministic AuthorityPolicy is future `STRICT_IP` architecture, not a current blocker.
- Provider, model, status, settings, and usage concepts must be provider-neutral.
- No provider-specific bot UI.
- SimulationRun remains the canonical execution record.
- RunnerJob remains operational state, not the durable scientific result.
- Decision remains the canonical human acceptance record.
- Artifact bytes stay outside SQLite; artifact metadata stays inside SQLite.
- New durable artifact identity should be data-root-relative, not absolute-path-based.
- Every major durable object needs an explicit workspace strategy.
- Every long-lived JSON payload needs a version strategy.
- Creating a RunnerJob must not execute it.
- AI-generated code must not execute without human review and a recorded script hash.
- File parsing, CAD, CFD, and scientific data connectors require their own design gates.
- Automated provider tests must not call the network.

## Final Milestone Sequence

1. `0E-D3` Pragmatic AI policy mode plus provider-neutral AI status/usage foundation.
2. `0E-D4` Continue provider-neutral AI settings/usage/audit implementation, still with no new provider.
3. `0E-D5` AI audit event envelope and no-network provider test fixture.
4. `0E-E` Artifact storage key and taxonomy hardening.
5. `0E-F` Database migration snapshot tests and migration trigger hardening.
6. `0E-G` Frontend API and AI page modularization during provider-neutral UI work.
7. `0F-A` Runner V1 manifest design gate.
8. `0F-B` Runner service split only if a second script or runner UI is approved.
9. `0F-C` Second provider design and implementation gate.
10. `0F-D` AI-assisted router design, after AuthorityPolicy exists.
11. `0F-E` Narrow Supervisor AI endpoint design gate.
12. `0G-A` BlueRev Modeling Workbench design gate.

## Immediate Next Recommended Codex Task

Perform `0E-D3 Pragmatic AI Policy Mode + Provider-neutral AI Status/Usage Foundation`.

Constraints:

- docs/contracts only unless a tiny placeholder is strictly necessary;
- do not add a new provider;
- do not add an AI router;
- do not add Supervisor;
- do not implement BlueRev modeling;
- define `FAST_DEV`, `STRICT_IP`, and disabled policy modes;
- keep structural secret protection;
- expose provider-neutral status/usage fields;
- avoid broad prompt blocking for normal public/internal technical material.

## Readiness Decision

JarvisOS is ready for the next implementation milestone only if the next milestone is `0E-D3` as defined above.

JarvisOS is not ready for:

- a second AI provider;
- AI-assisted routing;
- Supervisor;
- BlueRev Modeling Workbench;
- Scientific Data Connectors;
- CAD, CFD, FEM, or geometry tooling;
- runner expansion beyond the reviewed deterministic V0 model.

## BlueRev Decision

BlueRev modeling should remain paused.

Reason: BlueRev Workbench depends on stable AI authority, artifact identity, migration policy, runner manifest design, and frontend modularity. Implementing BlueRev before these are settled would turn domain modeling into the place where unresolved infrastructure decisions leak into product behavior.

## Runtime Code Changes

None. This decision gate is documentation-only.

## Tests And Build

No backend tests, compile checks, or frontend builds are required for this documentation-only decision gate.

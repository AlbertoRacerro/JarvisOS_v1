# System Upscale Threat Model

## Method

Each major area uses a bounded Proposer, Critic, Synthesizer structure:

1. Proposal v1.
2. Critique v1.
3. Improved proposal v2.
4. Critique v2.
5. Final synthesis.

The goal is not to solve every future problem now. The goal is to prevent expensive architectural traps before JarvisOS grows.

## Risk Matrix

| Area | Severity | Risk Statement | Why It Matters | Current Protection | Missing Protection | Scale-up Failure Mode | Proposed Solution | Critique | Improved Solution | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Many workspaces | medium | Workspace isolation is implicit in queries, not enforced by a shared repository layer. | A Workbench will load many related records per workspace. | Most tables carry `workspace_id`; tests cover core flows. | Consistent repository helpers and indexes for every workspace query. | Cross-workspace leakage or slow workspace dashboards. | Add workspace-scoped repository helpers. | Could over-abstract too early. | Add only when the first repeated query cluster appears. | refactor before BlueRev workbench |
| Many ModelSpecs | medium | ModelSpec records are minimal and will need versioned payloads. | Modeling capital depends on long-lived specs and revisions. | `schema_version`, status, raw payload fields exist. | Explicit provenance, revision, and acceptance policy. | Workbench cannot explain which spec generated which run. | Add ModelSpec revision table now. | Premature schema. | Document invariants now; add revisions when Workbench design demands it. | design before Workbench |
| Many SimulationRuns | high | SimulationRun is canonical but has limited indexing and lifecycle semantics. | Runs will become the main audit object. | UUID, workspace, model version, status, payloads, runner links. | Run status enum policy, provenance, run grouping, retention. | Slow run history and ambiguous failed/timed-out/cancelled states. | Normalize run lifecycle immediately. | Current V0 runner does not need it yet. | Define lifecycle now; implement next runner expansion. | refactor before runner expansion |
| Many artifacts | high | Artifact metadata is too path-centric and type-loose. | Files become central once plots, PDFs, CSVs, CAD placeholders, and AI outputs exist. | Artifact table, hashes, run artifact links. | Relative storage identity, taxonomy, retention, export policy. | Broken links after data-root move; unreadable artifact browser. | Move to object storage. | Too early and not local-first. | Keep filesystem data root, store relative keys and hashes, design object storage compatibility. | harden before artifact viewer |
| Many file types | high | File types are not classified enough for safe viewers and parsers. | PDFs, DOCX, LaTeX, CAD placeholders, logs, and source extracts carry different risks. | `artifact_type`, `mime_type`, `sha256`. | Taxonomy, parser safety, preview policy, max size by type. | Unsafe parsing or generic UI that cannot inspect files responsibly. | Build universal ingestion now. | Forbidden and risky. | Define taxonomy now; implement per type only when needed. | refactor before scientific connectors |
| Multiple providers | blocker | Provider contracts exist but authority and settings are not provider-neutral yet. | A second provider multiplies safety and cost paths. | `AIProviderAdapter`, `AIRequest`, `AIResponse`, Scaleway adapter. | AuthorityPolicy, provider-neutral settings/status/usage. | Provider-specific branching leaks into UI and routes. | Add router and provider selector. | Too unsafe. | First add deterministic authority and status design. | before second provider |
| Multiple AI task types | high | `AITaskType` exists, but task-specific gate rules are not centralized. | Different tasks need different egress, cost, and output contracts. | Enum and request/response contracts. | Task policy registry and authority matrix. | Smoke rules accidentally reused for model review or source extraction. | Put policy in each service. | Duplicates safety logic. | Central task policy plus service-level checks. | before Supervisor AI |
| Larger frontend | medium | `client.ts` and `AIDraft.tsx` are temporary monoliths. | Supervisor, artifacts, runner, Workbench panels will all need UI. | Small app and simple navigation. | Domain API clients and panel components. | Local operator UI becomes hard to change safely. | Rewrite UI now. | Too broad. | Split by domain before adding next major AI or artifact UI. | refactor before provider-neutral UI |
| More runner scripts | high | Runner service handles too many orchestration concerns for multiple scripts. | Different scripts need manifests, schemas, artifacts, and dependency rules. | Safety module, local subprocess boundary, hash checks. | Script manifest, implementation registry, execution service split. | New scripts bypass V0 safety or make service unreadable. | Add a script plugin system now. | Too much. | Add V1 manifest and split service first. | before runner expansion |
| Future CAD/PFD/plots | high | Rich artifacts require safe preview and metadata without executing/parsing unsafe content. | CAD/PFD outputs are likely high-value and high-risk. | Artifact registration only. | Preview policy, converter policy, file size limits, no active content. | Unsafe parser dependency or broken artifact UX. | Implement CAD/PFD now. | Forbidden. | Store placeholders and metadata only until a design gate. | before CAD/PFD outputs |
| Scientific source ingestion | high | Source ingestion would introduce untrusted files and provenance complexity. | Literature PDFs and source documents can be large, copyrighted, or sensitive. | No ingestion yet. | Source table, extraction record, citation policy, parser sandbox. | Raw documents get mixed with derived facts without provenance. | Add parser pipeline. | Too early. | Design provenance and artifact policy first. | before scientific connectors |
| BlueRev Workbench | blocker | Workbench would combine every immature subsystem. | It is the main product direction. | Domain objects, runner, artifacts, AI draft exist. | Artifact viewer, provenance, authority, frontend split, decision workflow. | Workbench becomes a large UI over unstable foundations. | Build initial Workbench now. | Too risky. | Keep paused until backlog blockers close. | keep paused |
| Local/remote provider mix | high | Egress rules are not yet modeled as first-class authority decisions. | Local and remote providers have different privacy properties. | Privacy classes and smoke gates. | Provider locality, data egress policy, task authority matrix. | Sensitive content sent to remote classifier/router. | Trust provider adapters. | Unsafe. | Deterministic local hard prefilter first. | before router |

## Architecture Area Review

### Storage And Artifacts

Proposal v1: Keep SQLite metadata and filesystem artifacts under the data root, and continue storing absolute paths in `artifacts.stored_path`.

Critique v1: Absolute paths are convenient but make artifacts depend on one machine and one data-root location. They also make future export, backup, and object storage migration harder.

Improved proposal v2: Keep SQLite for metadata and filesystem for bytes, but store a logical artifact key relative to the data root as the durable identity. Compute absolute paths only at runtime through `app/core/paths.py`.

Critique v2: A pure relative path policy still needs migration for existing absolute paths and needs a rule for external references that JarvisOS should not copy.

Final synthesis: Document relative keys now. Implement a compatibility migration later that preserves existing absolute-path records but writes new artifacts with relative keys, hash, size, type, and storage backend fields.

Residual risk: Existing records may need one-time cleanup if data root moves.

### Database Evolution

Proposal v1: Continue using the current in-code schema and lightweight migration ledger.

Critique v1: This is readable for a small local project, but schema changes are already accumulating and old local databases matter.

Improved proposal v2: Keep the current approach for documentation-only and small compatibility fields, but introduce formal migration tooling before the next schema-heavy milestone.

Critique v2: Alembic adds complexity and may be awkward while schema churn is still exploratory.

Final synthesis: Do not add Alembic now. Set a trigger: add formal migrations when any milestone changes more than two tables, renames fields, or needs backfill logic.

Residual risk: Manual migration statements can drift from baseline schema if not tested against older snapshots.

### AI Provider Growth

Proposal v1: Add more adapters using `AIProviderAdapter` and let each service choose what it needs.

Critique v1: That repeats the old Scaleway-shaped growth pattern with a new interface name. It does not solve authority, settings, cost, or audit.

Improved proposal v2: Build provider-neutral status/settings/usage and a deterministic AuthorityPolicy before adding another provider.

Critique v2: This slows provider expansion.

Final synthesis: Slowing provider expansion is the correct trade. The next AI milestone should design and test authority and usage before any new network integration.

Residual risk: The fake provider still uses an older provider base interface and should be reconciled before second-provider work.

### Runner And Execution

Proposal v1: Keep Python Runner V0 as-is and add script kinds case by case.

Critique v1: Case-by-case script addition will turn `runner/service.py` into a workflow engine and will weaken reviewed-script guarantees.

Improved proposal v2: Freeze V0 for one reviewed script. Require a script manifest, schema validation, artifact policy, and service split before adding the second kind.

Critique v2: It may feel heavy for small deterministic models.

Final synthesis: Require the manifest design before expansion, but keep implementation minimal. A manifest can be a small static Python dict or JSON file at first.

Residual risk: V0 is not a hostile-code sandbox, so only reviewed scripts should run.

### Frontend And API Modularity

Proposal v1: Keep the current frontend until a full Workbench exists.

Critique v1: Waiting until the Workbench exists means the Workbench will start from oversized pages and a mixed API client.

Improved proposal v2: Split API clients and AI panels before adding provider-neutral status/settings or Supervisor UI.

Critique v2: Splitting without new UX can feel like churn.

Final synthesis: Do one small non-visual modularization milestone before the next frontend feature. No redesign, only file boundaries.

Residual risk: Type drift between backend Pydantic models and frontend TypeScript remains manual.


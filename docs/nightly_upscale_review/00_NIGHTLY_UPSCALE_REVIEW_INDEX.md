# Nightly Upscale Review Index

Date: 2026-06-19

## Executive Judgement

JarvisOS is architecture-strong enough to continue with design and targeted hardening, but it is not ready for broad feature expansion yet.

The current system is still correctly local-first, feature-thin, and guarded. The highest risk is not one failing module. The highest risk is growth pressure: more providers, more file types, more runner scripts, more artifacts, and a larger frontend will turn today readable modules into accidental platforms unless the next milestones establish explicit storage, migration, authority, artifact, and frontend modularity rules.

Recommended stance:

```text
Proceed with architecture hardening and design milestones.
Do not add a second provider yet.
Do not implement Supervisor AI yet.
Do not resume BlueRev modeling yet.
```

## What Was Inspected

- `backend/app/core/`
- `backend/app/main.py`
- `backend/app/modules/modeling/`
- `backend/app/modules/ai/`
- `backend/app/modules/ai/contracts.py`
- `backend/app/modules/ai/providers/`
- `backend/app/modules/secrets/`
- `backend/app/modules/runner/`
- `backend/app/modules/events/`
- `backend/app/modules/files/`
- `backend/tests/`
- `frontend/src/api/client.ts`
- `frontend/src/pages/AIDraft.tsx`
- `frontend/src/pages/DomainFoundation.tsx`
- `frontend/src/App.tsx`
- `frontend/src/components/Layout.tsx`
- `docs/`
- `README.md`
- `docs/RUNBOOKS.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- current 0E architecture documents

## What Changed

Documentation only.

Created:

- `docs/nightly_upscale_review/00_NIGHTLY_UPSCALE_REVIEW_INDEX.md`
- `docs/nightly_upscale_review/01_SYSTEM_UPSCALE_THREAT_MODEL.md`
- `docs/nightly_upscale_review/02_STORAGE_AND_ARTIFACT_STRATEGY.md`
- `docs/nightly_upscale_review/03_DATABASE_SCALEUP_AND_MIGRATION_STRATEGY.md`
- `docs/nightly_upscale_review/04_AI_ROUTER_AUTHORITY_AND_PROVIDER_STRATEGY.md`
- `docs/nightly_upscale_review/05_RUNNER_SANDBOX_AND_EXECUTION_STRATEGY.md`
- `docs/nightly_upscale_review/06_FRONTEND_API_MODULARITY_STRATEGY.md`
- `docs/nightly_upscale_review/07_FINAL_ARCHITECTURE_HARDENING_BACKLOG.md`

## What Did Not Change

- No runtime backend code changed.
- No frontend code changed.
- No schema changed.
- No provider was added.
- No routing policy was implemented.
- No Supervisor AI endpoint or UI was implemented.
- No runner behavior changed.
- No artifact storage backend changed.
- No BlueRev model work resumed.

## Top 10 Risks

| Rank | Severity | Risk |
| ---: | --- | --- |
| 1 | blocker | Adding a second AI provider before a deterministic AuthorityPolicy would make routing unsafe and opaque. |
| 2 | high | Artifact records store path identity too directly; data-root moves or future object storage would break links. |
| 3 | high | `runner/service.py` is acceptable for one reviewed script but will become a monolith if a second model kind lands there. |
| 4 | high | SQLite schema evolution is still manual; another schema-heavy milestone needs migration discipline. |
| 5 | high | AI settings/status remain Scaleway-shaped while provider contracts are provider-neutral. |
| 6 | high | Event payloads are useful but free-form; audit quality will suffer as AI/router/runner complexity grows. |
| 7 | medium | `frontend/src/api/client.ts` mixes all API domains and will become brittle as UI surfaces grow. |
| 8 | medium | `frontend/src/pages/AIDraft.tsx` combines settings, secrets, smoke tests, console, token meter, and draft UI. |
| 9 | medium | File/artifact type taxonomy is too loose for PDFs, CAD placeholders, notebook exports, logs, and AI outputs. |
| 10 | medium | Provider-neutral registries are in-process contracts, not persisted configuration or audited selection records. |

## Top 10 Recommendations

| Rank | Priority | Recommendation |
| ---: | --- | --- |
| 1 | blocker | Define deterministic `AuthorityPolicy` before any AI-assisted router or second provider. |
| 2 | high | Convert artifact path policy to data-root-relative storage before artifact viewer or large file workflows. |
| 3 | high | Split provider-neutral AI settings/status from Scaleway-specific compatibility fields before adding another provider. |
| 4 | high | Create typed AI audit payload conventions for gate, route, authority, provider attempt, and usage events. |
| 5 | high | Split runner orchestration before adding a second runner script kind or runner UI. |
| 6 | high | Define artifact taxonomy, hash policy, retention policy, and export policy before file ingestion. |
| 7 | medium | Introduce formal migration tooling when the next schema-heavy milestone begins. |
| 8 | medium | Split frontend API clients by domain before Supervisor AI or Workbench UI. |
| 9 | medium | Split the AI page into panels before adding provider-neutral status/settings. |
| 10 | medium | Add migration tests from old SQLite snapshots before depending on long-lived local data. |

## Immediate Blockers

Before adding a second provider:

- Deterministic AuthorityPolicy design.
- Provider-neutral settings/status design.
- Provider-neutral usage record design.
- AI audit event conventions.
- Credential abstraction beyond Scaleway naming.

Before implementing AI-assisted routing:

- Local hard prefilter definition.
- Router input minimization policy.
- Routing proposal object.
- Final authority decision object.
- Audit of proposal versus decision.

Before BlueRev Modeling Workbench:

- Artifact taxonomy and path policy.
- ModelSpec and SimulationRun provenance conventions.
- Frontend module split.
- Runner V1 manifest design.
- Decision record acceptance workflow.

## Recommended Next Milestones

1. 0E-D3 Provider-neutral AI Status, Settings, Usage, and Authority Design.
2. 0E-D4 AI AuthorityPolicy and Audit Event Contracts.
3. 0E-E Artifact Storage Strategy Implementation, relative path metadata only.
4. 0E-F Frontend API and AI Page Modularization.
5. 0F-A Runner V1 Manifest Design Gate.
6. 0F-B Modeling Workbench Design Gate.

## Files Created Or Modified

Created this directory:

```text
docs/nightly_upscale_review/
```

Created eight review documents listed in "What Changed".

## Tests And Builds Run

None.

Reason: this milestone changed documentation only. No backend runtime code, frontend code, schema, or generated artifacts were changed.


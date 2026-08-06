# Spec 084 — BLUECAD-READ-MODEL-1

**Definition status:** complete specification; implementation remains unauthorized until a separate readiness decision promotes registry row 084.

**Registry status at definition:** `planned`

**Depends on:** 006, 044, 050, 051, 083

**Authority:** `AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/specs/STATUS.md`, `docs/specs/081-frontend-beta-authority-0.md`, merged specs 006, 044, 050, 051 and 083, and this specification.

**Exact derivation baseline:**

```text
repository: AlbertoRacerro/JarvisOS_v1
branch: master
commit: 03343df616a0156556a75c876c6f5c39cccd665d
```

**Visual boundary:** this slice is data-contract and backend-read-surface work only. It does not choose or alter Penpot identity, font, palette, token values, iconography, assets, borders, radii, shadows, global motion or component styling.

---

## 1. Purpose

Add the smallest workspace-scoped, candidate-scoped read model needed by the new application shell to load one coherent BLUECAD candidate aggregate without duplicating engineering truth or changing lifecycle authority.

The aggregate must expose, through one bounded read endpoint:

- candidate identity, origin, lifecycle status and promotion linkage;
- candidate artifact references and safe metadata;
- ordered attempt summaries and their artifact/job references;
- canonical evidence references associated with the candidate or its attempts;
- existing modeling/run references that are already traceable to the candidate or its attempts;
- freshness/staleness information derived from existing dependency authority;
- explicit partial-data diagnostics when a referenced object is absent, stale, malformed or inaccessible.

084 is an integration read model. It must not create a second candidate ledger, artifact catalogue, evidence store, dependency graph, run store, cache, search index or frontend state authority.

## 2. Verified current state

At the exact baseline:

1. `backend/app/modules/bluecad/routes.py` exposes workspace-scoped candidate list/detail, creation, archive, promotion, CAD-link and artifact-content routes.
2. `BluecadCandidateRead` already contains candidate lifecycle fields, candidate artifact IDs, promotion linkage, origin/parent identity and an embedded ordered attempt list.
3. `BluecadAttemptRead` already contains proposal job, build, validation, artifact and error-detail references.
4. `backend/app/modules/bluecad/ledger.py` reads candidate and attempt rows directly from the canonical BLUECAD ledger and attaches attempts to each candidate.
5. Artifact authority remains the canonical `artifacts` table and the existing workspace-scoped content route; the current candidate response exposes IDs but not a bounded metadata projection.
6. Specs 044, 050 and 051 already own evidence, dependency/provenance and stale-propagation semantics. 084 must consume those semantics rather than infer freshness from timestamps or duplicate graph logic.
7. Spec 083 mounts the current BLUECAD workbench once inside ModelStage and leaves candidate/record selection as a typed seam. It does not implement a candidate aggregate read contract.
8. No implementation branch or implementation PR for 084 exists at this baseline.

If master moves before readiness, the readiness audit must re-read these files and the accepted 044/050/051 services and tests, then amend this specification if the current authority differs materially.

## 3. Minimum-necessary decision

### 3.1 Selected shape

Implement one detail endpoint adjacent to the existing candidate detail route:

```text
GET /workspaces/{workspace_id}/bluecad/candidates/{candidate_id}/aggregate
```

The endpoint returns one typed `BluecadCandidateAggregateRead` assembled at request time from existing canonical stores.

This is selected because the shell needs one coherent snapshot and the current client would otherwise issue multiple weakly coordinated reads and reproduce joining/freshness rules in TypeScript.

### 3.2 Rejected alternatives

| Alternative | Rejection reason |
| --- | --- |
| Expand `BluecadCandidateRead` globally | changes the existing list/detail payload and can make candidate lists expensive; weakens the bounded detail/read-model separation |
| Add several narrow frontend calls and join client-side | duplicates source-reference and freshness semantics in the frontend and permits inconsistent snapshots |
| Create a materialized aggregate table or cache | unnecessary durable state, invalidation and migration burden; canonical data already exists |
| Add GraphQL, a generic projection framework or runtime schema registry | capability far beyond this static slice and not minimum necessary |
| Read artifact files in the frontend | violates backend authority and hard invariant 3 |

## 4. Read contract

The implementation must define strict response models equivalent in meaning to the following. Exact class names may vary only when required by existing naming conventions.

```python
class BluecadArtifactRefRead(BaseModel):
    id: str
    role: str
    filename: str
    mime_type: str
    sha256: str
    status: str
    source_ref: str | None
    created_at: str
    content_url: str

class BluecadEvidenceRefRead(BaseModel):
    ref: str
    kind: str
    subject_ref: str
    status: str
    stale: bool | None
    created_at: str | None
    summary: str | None

class BluecadRunRefRead(BaseModel):
    ref: str
    kind: str
    status: str | None
    created_at: str | None
    source_ref: str | None

class BluecadReadDiagnostic(BaseModel):
    code: Literal[
        "missing_reference",
        "malformed_reference",
        "inaccessible_reference",
        "unsupported_reference",
    ]
    source: str
    reference: str
    message: str

class BluecadCandidateAggregateRead(BaseModel):
    candidate: BluecadCandidateRead
    artifacts: list[BluecadArtifactRefRead]
    evidence: list[BluecadEvidenceRefRead]
    runs: list[BluecadRunRefRead]
    freshness: Literal["fresh", "stale", "unknown", "mixed"]
    diagnostics: list[BluecadReadDiagnostic]
```

The contract rules are binding:

1. `candidate` is the existing canonical candidate projection, including ordered attempts.
2. `artifacts` contains only artifacts referenced by the candidate or its attempts and found in the same workspace.
3. Artifact payloads contain metadata and a server route URL only; never filesystem paths, file bytes, secrets or unrestricted download paths.
4. Duplicate artifact IDs across candidate and attempts appear once.
5. `evidence` contains only canonical evidence records reachable through existing accepted source/provenance relationships. It does not parse report JSON into a second evidence model.
6. `runs` contains only existing run/modeling references that are explicitly traceable through accepted source references or dependency/provenance relationships. It does not infer association from matching timestamps, titles, brief text or workspace membership alone.
7. `freshness` is derived from accepted 050/051 dependency/freshness authority. Timestamps alone never determine stale state.
8. Missing or malformed optional references do not convert an otherwise valid candidate into a 500 response. They produce deterministic diagnostics and preserve all valid aggregate sections.
9. Unknown candidate or cross-workspace candidate access returns 404 without disclosing whether the candidate exists elsewhere.
10. The response is deterministic for an unchanged database snapshot: stable ordering and no random identifiers or current-time fields.

## 5. Snapshot and query boundary

The aggregate must be assembled under one SQLite read transaction or another existing repository mechanism that provides one coherent read snapshot.

The implementation must:

- validate the workspace and candidate within the same snapshot;
- fetch candidate and attempts without opening a connection per attempt;
- batch-fetch referenced artifact metadata;
- resolve evidence, run and freshness references through existing accepted resolver/service functions when available;
- add a narrowly scoped pure resolver only when no accepted resolver exists;
- avoid N+1 queries proportional to the number of attempts or artifacts;
- never mutate, repair, promote, archive, recompute or mark stale during the read;
- never call a provider, model, tool, filesystem scanner or external network service.

A direct SQL read is permitted only where the current module already owns that canonical table and no accepted service contract exists. Cross-domain tables must be consumed through their owner service/resolver or a bounded owner-approved read helper, not copied into BLUECAD-specific SQL semantics.

## 6. Reference handling

### 6.1 Candidate and attempt artifact roles

The aggregate recognizes only explicit candidate/attempt fields:

```text
candidate.spec_artifact_id
candidate.glb_artifact_id
candidate.report_artifact_id
attempt.spec_artifact_id
attempt.report_artifact_id
attempt.manifest_artifact_id
```

Roles are derived from the field that supplied the reference, not guessed from filenames. When the same artifact appears under multiple roles, the response uses one stable primary role and may expose a sorted `roles` list instead of one role if implementation review proves that lossless multi-role reporting is necessary. It must not duplicate the artifact row.

### 6.2 Evidence and run links

Accepted reference syntax and supported kinds must be closed and testable. The implementation must reuse the shared `<kind>:<id>` resolver introduced by spec 050 wherever applicable.

Opaque or malformed strings remain diagnostics. The aggregate must not execute dynamic table names, import paths, URL fetches or provider-owned resolvers.

### 6.3 Error details

`attempt.error_detail_json` remains part of the existing attempt model. 084 does not reinterpret it as authority. Invalid JSON must remain observable without crashing the aggregate, and must not be silently replaced with fabricated structure.

## 7. Freshness semantics

The aggregate exposes one candidate-level summary while preserving per-reference stale state where the canonical owner supplies it.

Candidate-level freshness is:

- `fresh`: every resolved freshness-bearing reference is fresh and at least one exists;
- `stale`: every resolved freshness-bearing reference is stale and at least one exists;
- `mixed`: both fresh and stale resolved references exist;
- `unknown`: no accepted freshness-bearing reference can determine state.

Missing, malformed or unsupported references contribute diagnostics but do not by themselves become `stale`.

084 must not:

- create new stale flags;
- update 051 state;
- treat candidate `updated_at` as freshness;
- treat archived, parked, failed or unpromoted lifecycle status as stale;
- conflate validation verdict with dependency freshness.

## 8. API and frontend boundary

084 may add to `frontend/src/api/client.ts` only:

- response types matching the backend contract;
- one `getBluecadCandidateAggregate(workspaceId, candidateId)` client function.

No current page or stage may consume the endpoint in 084. UI migration and lifecycle presentation belong to spec 085.

The client function must:

- use the existing HTTP helper and error behavior;
- URL-encode path segments through the existing client convention;
- perform no joining, inference, persistence or caching;
- expose no filesystem path or unvalidated artifact URL.

## 9. Files likely touched

Implementation is expected to remain within the smallest subset of:

```text
backend/app/modules/bluecad/models.py
backend/app/modules/bluecad/ledger.py
backend/app/modules/bluecad/routes.py
backend/app/modules/bluecad/read_model.py          # only if separation is clearer than ledger growth
backend/app/modules/<owner>/...                    # one bounded read helper only when required
backend/tests/bluecad/test_read_model.py
frontend/src/api/client.ts
scripts/check_bluecad_read_model.py                # dependency-free conformance checker if justified at readiness
```

No schema, migration, package manifest, lockfile, workflow, appearance, shell layout, viewer, provider, credential, budget, ledger, egress or Penpot file is authorized.

Readiness must replace this list with an exact allowed file set after inspecting current code.

## 10. Acceptance criteria

1. One workspace-scoped candidate aggregate endpoint exists and is side-effect free.
2. Existing candidate list/detail, archive, promote, create, artifact-content and CAD-link behavior remains unchanged.
3. Candidate and attempts come from the canonical BLUECAD ledger.
4. Artifact metadata is workspace-bound, deduplicated, stably ordered and contains no `stored_path`.
5. Artifact content URLs remain existing backend URLs and cross-workspace artifact references are not exposed.
6. Evidence and run associations require explicit accepted provenance/reference relationships; no heuristic association is used.
7. Freshness uses existing 050/051 authority and follows the four-state summary contract.
8. Missing, malformed and inaccessible optional references produce deterministic diagnostics while preserving valid sections.
9. Candidate-not-found and cross-workspace access return indistinguishable 404 responses.
10. Aggregate assembly uses a coherent read snapshot and avoids per-item connection/query loops.
11. The endpoint performs zero writes, provider calls, tool calls and external network calls.
12. The frontend adds only typed client support; no UI consumes the endpoint.
13. No schema, dependency, package, workflow, shell, viewer or visual-identity change is introduced.
14. Full backend tests, Ruff, frontend production build and all spec-specific tests/checkers pass on one exact head.

## 11. Required tests

### 11.1 Backend tests

Tests must cover at least:

- candidate aggregate happy path with multiple attempts and overlapping artifact IDs;
- deterministic artifact ordering and deduplication;
- no `stored_path` or data-root disclosure in serialized JSON;
- same-workspace artifact metadata and content URL construction;
- cross-workspace artifact reference rejection/diagnostic without metadata disclosure;
- missing artifact reference diagnostic;
- malformed attempt error JSON remains observable and non-crashing;
- explicit evidence/run link inclusion;
- unrelated same-workspace evidence/run exclusion;
- fresh, stale, mixed and unknown summaries;
- missing/unsupported freshness reference diagnostics;
- candidate 404 and cross-workspace 404 equivalence;
- stable response for unchanged data;
- zero mutation by comparing relevant rows before/after;
- bounded query count or an equivalent regression assertion proving no N+1 behavior;
- existing candidate route tests remain green.

### 11.2 Frontend/build tests

The production TypeScript build must prove:

- strict response typing;
- client path correctness;
- no current component imports or invokes the new client function;
- no DEV-only string or provider binding is introduced by this slice.

### 11.3 Required commands

```bash
python scripts/check_spec_status.py --self-test
cd backend
python -m ruff check app tests
python -m pytest -q
cd ../frontend
npm ci
npm run build
```

Readiness may add one dependency-free source checker if it catches a material boundary not reliably covered by runtime tests. It must not add a browser framework because 084 has no UI behavior.

## 12. Non-goals

084 does not implement:

- BLUECAD workbench migration or new visible UI;
- candidate creation, archive, retry, promotion or validation changes;
- GLB rendering, picking, component identity or scene binding;
- artifact upload, transformation or report parsing;
- editable engineering records;
- new evidence generation;
- dependency recomputation or stale propagation;
- run execution, cancellation or log streaming;
- analytics, comparison or charts;
- search, pagination or generic query language;
- a materialized view, cache, event projection or new table;
- deep links or URL-owned selection;
- provider, model, budget, credential or egress behavior;
- visual identity or Penpot implementation.

## 13. Readiness requirements

A separate readiness PR must:

1. rebase the specification against exact current master;
2. inspect accepted 044/050/051 owner services and identify the exact evidence/run/freshness resolver path;
3. prove every dependency is `merged` and no active front overlaps the runtime boundary;
4. freeze the exact response model, reference kinds and stable ordering;
5. freeze an exact allowed file set;
6. identify the exact test fixtures and existing regression tests reused;
7. decide whether a dependency-free checker is minimum necessary;
8. confirm no schema migration, package dependency, workflow or browser framework is needed;
9. promote row 084 to `ready` only when the implementation can be completed without unresolved authority ambiguity.

Until that readiness decision merges, registry row 084 remains `planned`, implementation PR remains `—`, and no runtime work is authorized.

# 131 — ERROR-CONTRACT-UNIFICATION-1

Status: corrected planning/readiness packet; live implementation authority remains `docs/specs/STATUS.md`.

## Purpose

Remove one concrete backend wire-contract drift without starting a broad exception-taxonomy refactor. The first slice standardizes how an existing workspace ID that cannot be resolved is translated into HTTP across the bounded Workspaces, Modeling, and Project Knowledge route boundary.

## Exact-master inventory

Originally derived after 130 post-merge reconciliation and corrected against exact master `5384720f01bf37cb74d5adf386d8b50223901a05` after planning PR #479 merged.

Fresh code evidence shows the same missing-workspace condition currently has three representations:

- `backend/app/modules/workspaces/routes.py::get_workspace_endpoint` is the only public Workspaces route that translates a missing workspace and currently raises `HTTPException(status_code=404, detail="Workspace not found.")`; there are no Workspaces PATCH/DELETE HTTP endpoints on this exact master;
- `backend/app/modules/modeling/service.py::_require_workspace` raises `ValueError("Workspace not found.")`; `backend/app/modules/modeling/routes.py::_domain_error` currently translates every caught `ValueError` generically to HTTP 404 with `detail=str(exc)`, so workspace absence reaches the wire as the plain string `"Workspace not found."`;
- `backend/app/modules/project_knowledge/routes.py::_workspace_not_found` already returns 404 with structured detail `{"code": "workspace_not_found", "message": "Workspace not found."}`.

`backend/app/modules/workspaces/service.py` owns lookup persistence semantics and exposes create/list/get/get-by-slug/seed/default behavior only; it has no update/delete CRUD functions on this exact master. It does not own HTTP translation and must remain unchanged. Modeling's existing service-level workspace guard remains the existence decision point; 131 must not turn the HTTP layer into a second database lookup owner.

`backend/app/core/errors.py` currently contains only the small domain `AppError` dataclass. There is no established repository-wide HTTP translator that should be broadened opportunistically.

## Failure mode

A client or test that handles the same canonical missing-workspace condition must currently branch by endpoint/module and may accidentally depend on punctuation or string-vs-object shape. Modeling also has a broader `ValueError -> 404 string` translator, so a careless implementation that rewrites every `ValueError` would silently alter unrelated domain failures. A broad global exception middleware rewrite would be a larger and riskier solution than the defect requires.

The earlier #479 packet incorrectly described three Workspaces GET/PATCH/DELETE route translations. Exact-master runtime inspection proves only GET exists. Readiness must therefore bind to the real route surface rather than require nonexistent endpoints or silently invent new CRUD authority.

## Accepted implementation boundary

The implementation MUST be a bounded workspace-not-found translation change only. It may:

1. add one small shared backend helper at an existing common/core boundary to construct the canonical missing-workspace `HTTPException`;
2. make that helper return HTTP 404 with exact FastAPI detail payload `{"code": "workspace_not_found", "message": "Workspace not found."}`;
3. migrate `workspaces.routes.get_workspace_endpoint` to that helper;
4. add a narrow Modeling translation branch that recognizes the existing exact workspace-not-found service error before the pre-existing generic `ValueError` fallback, without changing translation of any other `ValueError`;
5. replace Project Knowledge's local `_workspace_not_found` only if doing so is behavior-identical and removes duplication; otherwise it may remain the reference implementation for this slice;
6. add deterministic route/helper tests proving exact status and JSON response shape for the real representative endpoints.

The shared helper is a translation seam, not a new domain/store/service authority. Workspace existence continues to be decided by the existing workspace service/modeling service DB owners. 131 MUST NOT add Workspaces PATCH/DELETE routes merely to satisfy the superseded #479 wording.

## Acceptance criteria

All are required on one exact implementation head:

1. Selected missing-workspace routes return HTTP 404 with exact response JSON `{"detail":{"code":"workspace_not_found","message":"Workspace not found."}}`.
2. Workspaces GET-by-ID and at least one Modeling workspace-scoped route use the same canonical workspace-not-found HTTP translation rather than local string variants.
3. Modeling's unrelated `ValueError` translations remain observably unchanged; any non-workspace-absence `ValueError` must not be reclassified as `workspace_not_found`.
4. If Project Knowledge switches to the shared helper, its externally observable missing-workspace status/payload is JSON-value-equivalent to its pre-131 contract.
5. Existing success-path behavior and both workspace service/modeling service existence semantics are unchanged.
6. Existing Project Knowledge Basis/lifecycle error codes and status mappings are unchanged.
7. No Workspaces PATCH/DELETE endpoint, broad `ValueError`/`Exception` catch, global middleware taxonomy, database/schema/store/frontend/provider/egress change, or unrelated domain-error migration is introduced.
8. Focused backend tests plus all repository-required exact-head gates are terminal green.

## Deterministic test plan

At minimum:

- test the shared helper's 404 status and structured detail value;
- exercise a nonexistent workspace through Workspaces GET-by-ID and assert exact response JSON;
- exercise one Modeling workspace-scoped endpoint whose service raises `ValueError("Workspace not found.")` and assert the same exact response JSON;
- assert a representative non-workspace Modeling `ValueError` retains its existing plain-detail 404 contract, proving the new branch is narrow;
- preserve/extend an existing Project Knowledge missing-workspace assertion to prove no regression if its local helper is deduplicated;
- run affected backend pytest/ruff gates and repository-required frozen-head CI.

Tests must assert the actual HTTP response contract, not merely that an exception was raised.

## Non-goals

- no new Workspaces update/delete CRUD or endpoints;
- no bulk migration of every backend `HTTPException`;
- no replacement of Modeling's generic `ValueError` fallback beyond the exact workspace-not-found branch;
- no unified taxonomy for all lifecycle/model/run/evidence errors;
- no global FastAPI exception middleware or handler framework;
- no change to workspace/modeling service CRUD or persistence semantics;
- no frontend error-UX rewrite;
- no schema, migration, store, provider, credential, egress, runner, or external-service change;
- no 132+ implementation.

## Readiness decision

**READY, conditional only on this correction and the subsequent live registry transition to `131=ready` merging.**

The actual defect is reproduced by exact-head code inspection, the corrected scope is local/reversible, no security/credential/provider/store/ownership authority is introduced, the canonical payload already exists in Project Knowledge, and acceptance/non-goals are now bound to the real runtime surface. The slice therefore remains eligible for post-112 low-risk planning compression.

Until this correction is merged and exact `master` records `131=ready`, this packet grants no implementation authority.

### Test del minimo necessario

Criterio di accettazione: one stable missing-workspace HTTP contract across the bounded first backend slice.

Questo lavoro serve a soddisfarlo? sì.

Il criterio è raggiungibile senza di esso? no — leaving the route-local translators in place preserves observably different contracts; adding nonexistent CRUD or a larger taxonomy/middleware layer is unnecessary.

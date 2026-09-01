# 131 — ERROR-CONTRACT-UNIFICATION-1

Status: planning/readiness packet; live implementation authority remains `docs/specs/STATUS.md`.

## Purpose

Remove one concrete backend wire-contract drift without starting a broad exception-taxonomy refactor. The first slice standardizes how an existing workspace ID that cannot be resolved is translated into HTTP across the bounded Workspaces, Modeling, and Project Knowledge route boundary.

## Exact-master inventory

Derived from exact master `a10bf6881c42df67b38fcae90b4893dbe62fb1db` after 130 post-merge reconciliation.

Fresh code evidence shows the same missing-workspace condition currently has three representations:

- `backend/app/modules/workspaces/routes.py` repeats `HTTPException(status_code=404, detail="Workspace not found")` in GET/PATCH/DELETE;
- `backend/app/modules/modeling/routes.py::_require_workspace` raises 404 with `detail="Workspace not found."`;
- `backend/app/modules/project_knowledge/routes.py::_workspace_not_found` already returns 404 with structured detail `{"code": "workspace_not_found", "message": "Workspace not found."}`.

`backend/app/modules/workspaces/service.py` owns lookup persistence semantics and returns `None`/`False` for missing rows; it does not own HTTP translation and must remain unchanged.

`backend/app/core/errors.py` currently contains only the small domain `AppError` dataclass. There is no established repository-wide HTTP translator that should be broadened opportunistically.

## Failure mode

A client or test that handles the same canonical missing-workspace condition must currently branch by endpoint/module and may accidentally depend on punctuation or string-vs-object shape. Adding more routes by copy/paste makes that drift worse. A broad global exception middleware rewrite would be a larger and riskier solution than the defect requires.

## Accepted implementation boundary

The implementation MUST be a bounded HTTP-translation change only. It may:

1. add one small shared backend helper at an existing common/core boundary to construct the canonical missing-workspace `HTTPException`;
2. make that helper return HTTP 404 with exact FastAPI detail payload `{"code": "workspace_not_found", "message": "Workspace not found."}`;
3. migrate the three duplicated Workspaces route translations and Modeling `_require_workspace` to that helper;
4. replace Project Knowledge's local `_workspace_not_found` only if doing so is behavior-identical and removes duplication; otherwise it may remain the reference implementation for this slice;
5. add deterministic route/helper tests proving exact status and JSON response shape for representative endpoints.

The shared helper is a translation seam, not a new domain/store/service authority. Workspace existence continues to be decided by the existing workspace service/DB owner.

## Acceptance criteria

All are required on one exact implementation head:

1. Selected missing-workspace routes return HTTP 404 with exact response JSON `{"detail":{"code":"workspace_not_found","message":"Workspace not found."}}`.
2. Workspaces GET/PATCH/DELETE and at least one Modeling route use the same shared translation seam rather than local punctuation/string variants.
3. If Project Knowledge switches to the shared helper, its externally observable missing-workspace status/payload is byte-equivalent at the JSON-value level to its pre-131 contract.
4. Existing success-path behavior and workspace service return semantics are unchanged.
5. Existing Project Knowledge Basis/lifecycle error codes and status mappings are unchanged.
6. No broad `ValueError`/`Exception` catch, global middleware taxonomy, database/schema/store/frontend/provider/egress change, or unrelated domain-error migration is introduced.
7. Focused backend tests plus all repository-required exact-head gates are terminal green.

## Deterministic test plan

At minimum:

- test the shared helper's 404 status and structured detail value;
- exercise a nonexistent workspace through representative Workspaces GET/PATCH/DELETE endpoints and assert exact response JSON;
- exercise one Modeling endpoint guarded by `_require_workspace` and assert the same exact response JSON;
- preserve/extend an existing Project Knowledge missing-workspace assertion to prove no regression if its local helper is deduplicated;
- run affected backend pytest/ruff gates and repository-required frozen-head CI.

Tests must assert the actual HTTP response contract, not merely that an exception was raised.

## Non-goals

- no bulk migration of every backend `HTTPException`;
- no unified taxonomy for all lifecycle/model/run/evidence errors;
- no global FastAPI exception middleware or handler framework;
- no change to workspace service CRUD semantics or persistence;
- no frontend error-UX rewrite;
- no schema, migration, store, provider, credential, egress, runner, or external-service change;
- no 132+ implementation.

## Readiness decision

**READY, conditional only on the live registry transition to `131=ready` merging.**

The defect is reproduced by exact-head code inspection, the scope is local/reversible, no security/credential/provider/store/ownership authority is introduced, the canonical payload already exists in Project Knowledge, and acceptance/non-goals are explicit. The slice therefore qualifies for post-112 low-risk planning compression.

Until exact `master` records `131=ready`, this packet grants no implementation authority.

### Test del minimo necessario

Criterio di accettazione: one stable missing-workspace HTTP contract across the bounded first backend slice.

Questo lavoro serve a soddisfarlo? sì.

Il criterio è raggiungibile senza di esso? no — leaving the route-local translators in place preserves three observably different contracts; a larger taxonomy/middleware layer is unnecessary.
# Spec 083 amendment — production SPA route fallback

**Status:** normative amendment to `docs/specs/083-app-shell-1.md` sections 3, 4, 16, 18, 19, and 21.

**Exact finding baseline:** `89ce0539dcad7be4502bba1d779930ad5f9f380a`

## 1. Verified blocker

The single-process desktop launch serves `frontend/dist` from `backend/app/main.py` through:

```py
app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
```

`StaticFiles(..., html=True)` serves `index.html` for directory/index cases but does not provide a general single-page-application fallback for arbitrary static paths. A direct request or refresh for canonical frontend routes such as:

```text
/home
/design/model
/legacy/domain-foundation
```

can therefore return a server-side 404 even though client-side navigation and Vite preview work.

The existing exact file set excludes backend static-serving changes, making the route-continuity acceptance criteria impossible in the shipped single-process runtime.

## 2. Selected minimum solution

The 083 implementation must add one bounded static-serving adapter for the built frontend.

It must:

1. preserve all FastAPI/API routes and their precedence;
2. serve existing frontend files and directories with normal `StaticFiles` behavior;
3. after an ordinary static 404, serve `frontend/dist/index.html` only when all fallback conditions are met;
4. support only `GET` and `HEAD` fallback requests;
5. require a navigation-compatible request accepting `text/html`;
6. reject fallback for a path whose final segment has a file suffix;
7. reject fallback for any reserved backend/API top-level path root;
8. leave missing assets, API misses, non-navigation requests, and non-GET/HEAD methods as real 404/405 responses;
9. remain inactive when `frontend/dist` is absent;
10. add no API, backend state, schema, migration, provider, credential, budget, ledger, egress, audit, or MemoryStore behavior.

## 3. Reserved API roots

The implementation must not maintain an unrelated hand-written copy of every API endpoint.

Before mounting the frontend, `create_app()` must derive the reserved top-level path roots from the already registered non-frontend application routes. The set must include the first literal segment of every registered HTTP route whose path begins with `/`, including FastAPI documentation and schema routes where enabled.

Examples include roots equivalent to:

```text
health
system
api
workspaces
memory
flowsheets
openapi.json
docs
redoc
```

The actual set is derived from the application route table and is not limited to these examples.

Rules:

- an exact registered API route continues to win before the frontend mount;
- an unregistered path beneath a reserved root remains an API/static 404 and never returns `index.html`;
- dynamic placeholders are not treated as literal roots;
- the frontend mount itself is excluded from derivation;
- an empty or malformed route path contributes no root.

## 4. Fallback request contract

A fallback is eligible only when:

```text
method is GET or HEAD
AND Accept includes text/html
AND first path segment is not reserved
AND final path segment has no suffix
AND frontend index.html exists
AND normal static resolution returned 404
```

Additional rules:

- query strings do not affect route eligibility;
- URL fragments never reach the server and carry no authority;
- path traversal remains governed and rejected by `StaticFiles`;
- the adapter must not catch arbitrary exceptions or convert 500 responses into index HTML;
- a HEAD fallback returns index metadata/body semantics appropriate for HEAD;
- response media type for the fallback is HTML;
- cache behavior must not make `index.html` immutable or asset-like.

## 5. Authorized implementation files

The single 083 implementation PR is additionally authorized to modify:

```text
backend/app/main.py
```

and add:

```text
backend/app/core/spa_static.py
backend/tests/test_spa_static.py
```

No other backend file is authorized by this amendment.

`backend/app/main.py` may change only to:

- import the bounded adapter/helper;
- derive reserved roots after API routers are registered;
- mount the adapter instead of raw `StaticFiles` when `frontend/dist` exists.

It must not reorder or alter API router registration, middleware, lifespan, settings, or backend authority.

## 6. Required deterministic tests

`backend/tests/test_spa_static.py` must prove at minimum:

1. an existing built asset is served unchanged;
2. an existing `index.html` is served at `/`;
3. `/home`, `/design/model`, and one required `/legacy/...` route serve the index for `GET` with `Accept: text/html`;
4. the same route supports `HEAD` without an unexpected body;
5. an unknown non-reserved extensionless client route serves the index, allowing the client not-found surface to render;
6. a missing asset such as `/assets/missing.js` remains 404;
7. an extensionless request without `Accept: text/html` remains 404;
8. an unregistered path under every representative reserved API root remains 404 and never contains the frontend index marker;
9. registered API routes retain their original responses and content types in an integration test;
10. POST/PUT/DELETE to a frontend-looking path do not receive index HTML;
11. absence of the frontend build leaves `create_app()` usable without a frontend mount;
12. traversal and malformed-path behavior is not weakened;
13. reserved-root derivation ignores the frontend mount and handles static/literal route paths deterministically.

Tests use temporary directories/fixtures and make no live provider call, secret request, or real data-root mutation.

## 7. Browser evidence amendment

Route direct-load and refresh evidence must be collected through the shipped FastAPI single-process serving path, not only through Vite preview.

At minimum verify through the backend-served production build:

```text
/home
/design/model
/design/flowsheet
/legacy/domain-foundation
one unknown client route
```

Also verify:

- a missing asset remains a server 404;
- one unknown reserved API-root path remains a server/API 404 and does not render the shell;
- registered API health behavior remains unchanged.

Vite preview may provide supplemental evidence but cannot satisfy this production-serving gate by itself.

## 8. Security and authority boundary

The fallback adapter is delivery infrastructure for already built public frontend files. It must not:

- expose repository files or the data root;
- broaden static directory roots;
- return index HTML for API failures;
- swallow authorization, validation, provider, budget, ledger, or secret errors;
- log request bodies, secrets, tokens, or private engineering content;
- introduce templating, server-side rendering, dynamic code execution, or runtime route registration;
- add a dependency.

## 9. Rollback and removability

The adapter is independently removable with 083 by restoring the prior raw static mount. It creates no durable state, migration, route record, or browser storage.

Removing it while retaining path-based 083 routes would break direct-load/refresh behavior; therefore it is part of the structural shell delivery boundary, not part of the Penpot visual-identity lane.

## 10. Acceptance amendment

Spec 083 cannot be promoted to ready or merged as implemented unless:

- the bounded production fallback is implemented within the authorized files;
- all backend adapter tests pass;
- direct-load/refresh is proved through FastAPI-served `frontend/dist`;
- API and missing-asset 404 semantics remain intact;
- no P0/P1 or beta-blocking P2 remains.

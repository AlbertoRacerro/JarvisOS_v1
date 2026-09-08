# Spec 083 amendment — exact client routes beneath reserved API roots

**Status:** normative corrective amendment to `docs/specs/083-app-shell-1.md` and `docs/specs/083-spa-fallback-amendment-2026-08-05.md`.

**Exact finding baseline:** `c0256125d8e8883c9515c0ab0f66f9bc712f7d63`

## 1. Verified production blocker

The trusted 142 exact-head browser proof for 113/#548 reached real Chromium on exact candidate head `8434d864cebe9049e90a5a6c5545a5a426ddf2e7` through the shipped FastAPI single-process serving path. `frontend/dist` was built successfully and FastAPI was healthy, but a direct browser navigation to `/memory/models` returned HTTP 404.

This is not a missing-build or proof-runner defect. `backend/app/main.py` already mounts the built frontend through `SpaStaticFiles`. The 404 follows the current 083 rule that rejects SPA fallback for every path whose first segment is a derived reserved backend/API root. Because `memory` is a real backend route root, the accepted 113 client route `/memory/models` is therefore unreachable on direct load/refresh in the production single-process path.

The same collision class applies to the current beta-critical client routes used by 142 under backend-owned top-level namespaces, including Coding routes. A separate proof-only UI server would hide this production defect and is forbidden as substitute evidence.

## 2. Selected minimum correction

Preserve the fail-closed reserved-root model, but permit SPA fallback for a **small exact allowlist of canonical client routes** that intentionally coexist beneath a reserved API root.

Initial authorized exact exceptions are only:

```text
/memory/models
/settings/ai
/coding/repository
/coding/runtime
```

An exception is eligible only when every existing 083 fallback condition remains true: GET or HEAD, navigation request accepting `text/html`, extensionless safe path, existing frontend `index.html`, and ordinary static resolution returning 404.

The exception matches the complete normalized request path only. It must not imply prefix, child, wildcard, parameterized, or sibling authorization. For example, authorizing `/memory/models` must **not** make `/memory/unknown`, `/memory/models/unknown`, or any registered/missing Memory API route receive SPA HTML.

Registered FastAPI routes continue to win before the frontend mount and retain their existing semantics regardless of the exception set.

## 3. Authority and ownership

The correction belongs to the 083 production-delivery adapter because the failure is direct-load/refresh routing of an already accepted client route through the single-process production server. It does not transfer any Memory, Coding, Settings, API, schema, persistence, provider, credential, budget, egress, ledger, or product-state authority to 083.

`SpaStaticFiles` remains a generic static-serving adapter. It may accept an explicit collection of exact client-route exceptions from application composition; it must not discover frontend routes by executing frontend code, parse arbitrary client bundles, or maintain a broad copy of backend endpoints.

The bounded application composition may declare the four exact routes above as delivery exceptions. Future additions require fresh accepted evidence that a canonical client route intentionally collides with a reserved API root; no prefix-level escape hatch is authorized.

## 4. Authorized implementation files

One corrective implementation PR is authorized to modify only:

```text
backend/app/main.py
backend/app/core/spa_static.py
backend/tests/test_spa_static.py
```

`backend/app/main.py` may only pass the bounded exact client-route exception set into the existing SPA adapter. Router registration order, middleware, lifespan, settings, and backend authorities must not change.

`backend/app/core/spa_static.py` may only extend fallback eligibility to an exact normalized path present in the supplied exception set while preserving all existing safety, Accept, method, suffix, traversal, asset, and reserved-root behavior for every other path.

## 5. Required deterministic acceptance

Tests must prove at minimum:

1. `/memory/models` returns the production `index.html` for GET with `Accept: text/html` when the build exists;
2. the same exact route supports HEAD with correct no-body semantics;
3. representative exact exceptions `/settings/ai`, `/coding/repository`, and `/coding/runtime` are eligible under the same contract;
4. `/memory/unknown`, `/memory/models/unknown`, `/coding/unknown`, and another reserved-root sibling remain 404 and never contain the frontend index marker;
5. registered Memory/Coding/API routes retain their original status/content type and are never shadowed by the frontend mount;
6. missing assets remain 404;
7. non-HTML Accept, POST/PUT/DELETE, malformed/traversal paths, and suffixed paths remain ineligible;
8. an exception path is exact and normalization cannot broaden it through query strings, encoded traversal, duplicate separators, or child paths;
9. existing 083 SPA fallback tests remain green.

No live provider, secret, network egress, or real user data is permitted.

## 6. Browser acceptance

After deterministic acceptance and exact-head review, rerun 142 through the shipped FastAPI single-process path. For 113, `/memory/models` must return the SPA and satisfy the accepted dossier assertions on the same exact PR head. Do not substitute Vite preview, a standalone static server, or a proof-only route rewrite.

Later 124/140 proof may rely on this correction only after their own deterministic/semantic gates are ready; a path returning SPA HTML alone is never sufficient proof of those specs.

## 7. Security invariants

This amendment does **not** authorize:

- fallback for a whole reserved root;
- wildcard or prefix exceptions;
- conversion of unknown API misses into HTML 200;
- any change to registered API route precedence;
- serving repository/data-root files;
- a second frontend server in production or in lieu of 142 single-process evidence;
- credential/provider/budget/ledger/egress changes;
- new dependencies.

## 8. Acceptance decision

The corrective implementation is mergeable only when deterministic tests prove exact-route behavior and reserved-root siblings remain fail-closed, CI is green, review finds no P0/P1 or beta-blocking P2, and a subsequent 142 run demonstrates that the real production route collision is resolved rather than bypassed.

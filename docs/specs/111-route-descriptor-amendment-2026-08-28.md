# 111 route-descriptor amendment — 2026-08-28

This amendment is binding on `111 JARVIS-CONTEXT-ACTION-FOUNDATION-1` and must be consumed by its fresh readiness decision. It resolves the route-identity ambiguity found during exact-head review of PR #419. It does not authorize runtime implementation by itself; registry row `111` remains `planned` until readiness is merged and reconciled.

## Exact source authority

Derived against exact master `689e3e4cc3a7039dffc30b514ad66163184d0aed` and the current canonical router in `frontend/src/app/routes.ts`.

The common Jarvis route descriptor MUST use the canonical router identity rather than accepting an arbitrary route string.

## Frozen route descriptor contract

The typed descriptor is the pair:

- `route_id`: the exact `RouteId` emitted by the canonical `resolveRoute()` result;
- `canonical_path`: the exact `canonicalPath` emitted by that same resolved route.

The pair is authoritative only when both values correspond to the same entry in the readiness-frozen non-legacy allow-list derived from `PRODUCTION_ROUTES`. The backend/common contract MUST reject mismatched pairs rather than normalizing one field to the other.

Readiness MUST freeze the exact allow-list from fresh master and MUST exclude:

- every route whose current definition has `legacy: true`;
- `legacy-dev-local-chat`;
- `not-found`;
- redirect source paths such as `/`, `/home`, `/design/model`, `/design/results`, `/design/lineage`, `/design/flowsheet`, and `/settings`.

A redirect is presentation/navigation behavior only. The Jarvis contract receives the canonical resolved pair after routing; it never keys capabilities by a redirect source string.

Optional mode/tab identity is allowed only as a separately typed bounded field when readiness proves one current canonical surface needs it. It MUST NOT replace `route_id` or `canonical_path`, and arbitrary path/tab strings are not capability keys.

## Capability-key rule

Common capability registration and lookup MUST key route-scoped availability by the canonical `route_id` defined above. `canonical_path` is carried as inspectable routing evidence and must match the registered route. Later domain adapters MUST NOT independently choose pathname, redirect source, free-form tab id, or another route vocabulary as their capability key.

This preserves one vocabulary across 111 and later 121–123 adapters while keeping 112–120 unable to activate Jarvis-domain behavior early.

## Readiness obligations

The separate 111 readiness decision MUST:

1. re-read `frontend/src/app/routes.ts` from its exact source master;
2. enumerate the exact accepted non-legacy `route_id` / `canonical_path` pairs;
3. freeze the backend field shape and validation boundary implementing that pair;
4. map deterministic tests proving accepted pair, mismatched pair rejection, redirect-source rejection, legacy/dev/not-found rejection, and stable capability lookup by `route_id`;
5. preserve the full-spec rule that route/selection changes never implicitly mutate the added-context basket.

No frontend route redesign, new navigation owner, compatibility alias, domain adapter, provider path, or durable store is authorized by this amendment.

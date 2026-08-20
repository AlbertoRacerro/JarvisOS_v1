# 058c — fresh readiness correction: explicit semantic-companion registration surface

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-2026-08-20-fresh.md` and `docs/specs/058c-readiness-provenance-correction-2026-08-20.md`  
Reason: exact-head review of PR #317 proved that server-side companion registration authority alone does not make the semantic companion reachable through the current operator workflow on a fresh workspace, and that the globally mounted Properties controller does not currently refresh its implementation list after that explicit registration when the workspace identity is unchanged.

This correction is part of the 058c readiness decision. Where it conflicts with the fresh readiness record, this file governs. It changes no runtime code and does not promote `058c` from `planned`.

## 1. Failure modes closed

The fresh readiness correctly authorizes one idempotent server-owned semantic-companion registration path and requires a fresh workspace to be able to register that companion. However, its frontend allow-list does not include the only current explicit bundled-model registration surface, `frontend/src/pages/DomainFoundation.tsx`.

Current runtime exposes `onRegisterBundledModels()` there as the deliberate operator action that registers missing bundled BlueRev models. Merely adding a new API client function does not make the companion reachable. Conversely, automatically registering the companion from `EngineeringProperties` on selection/load would turn semantic inspection into a durable side effect and would violate the operator-first no-hidden-mutation boundary.

A second exact-runtime gap remains after explicit registration: `DomainFoundation` refreshes only its own local `implementations` state, while the globally mounted `useEngineeringProperties` controller loads implementations only when `workspaceId` changes. Ordinary route navigation preserves the workspace identity, so registration followed by navigation to Design can leave Properties on a stale model list until a page reload. A successful explicit registration must therefore invalidate or refresh the existing Properties model list without introducing another store or making selection itself persistent.

Therefore 058c V0 must extend the existing explicit registration action and add one bounded in-memory refresh/invalidation seam into the existing Properties controller rather than introducing selection-triggered registration, an implicit background registration path, or parallel semantic state.

## 2. Correct V0 registration and refresh contract

On a fresh workspace, the existing explicit **Register missing bundled models** action in `DomainFoundation` is the minimum normal product surface for semantic-companion creation.

Implementation must:

1. keep the existing registration action explicitly operator-triggered;
2. include the new reviewed-047 semantic companion in that same missing-bundled-model registration sequence;
3. preserve idempotency: if the companion already exists with the exact server-known identity, the action creates no duplicate;
4. preserve the existing legacy 047/048/049 registrations and their current labels/contracts/identity;
5. refresh `DomainFoundation`'s workspace records after registration exactly as the current action already does;
6. after successful explicit registration, deterministically refresh/invalidate the already-mounted `useEngineeringProperties` implementation list for the same workspace so the companion is available without a page reload;
7. keep that refresh as an in-memory read-side synchronization only: it may refetch current model implementations/Parameters but creates no model, changes no working binding, selects no semantic model by inference, and persists nothing;
8. surface registration failure through the existing operator message/error path and do not signal the Properties refresh as successful when registration failed;
9. never register a model merely because a BLUECAD object was selected, Properties opened, semantic metadata was read, preflight ran, or a route changed.

The companion remains server-owned and exact-tuple guarded. The frontend registration surface supplies only explicit operator intent; it does not decide script/contract identity, applicability, provenance, freshness, or execution admission. The Properties refresh only makes newly authoritative server state visible to its existing controller.

## 3. Minimum allow-list amendment

The fresh readiness Section 11 frontend allow-list is amended to add exactly:

- `frontend/src/pages/DomainFoundation.tsx` — only to extend the existing explicit bundled-model registration action and its current registered/missing state handling for the semantic 047 companion, and to invoke the successful-registration refresh callback;
- `frontend/src/App.tsx` — only for a bounded callback/refresh-generation bridge from the explicit registration surface to the already-mounted Properties controller; no new durable/global semantic store;
- `frontend/src/components/engineering/EngineeringProperties.tsx` — already in the base allow-list; may expose/reuse one deterministic read-side refresh/invalidation operation for current implementations/Parameters while preserving this controller as the sole working-state/preflight owner;
- focused frontend tests covering explicit registration/idempotent missing-state behavior and registration → navigation/Properties visibility without page reload if current test structure requires them.

No other page, navigation redesign, new registration wizard, automatic initialization hook, background persistence effect, local persistence, provider path, event bus/framework, or semantic state store is authorized. Prefer the smallest existing React callback/controller seam; do not add a general invalidation framework for this one synchronization need.

`frontend/src/api/client.ts` remains authorized for the narrow companion registration call/type needed by this explicit action.

## 4. Acceptance added

Implementation acceptance gains these merge-blocking cases:

1. fresh workspace + explicit bundled-model registration action → semantic 047 companion is created through the normal server-owned endpoint;
2. repeating the same explicit action → no duplicate semantic companion;
3. legacy bundled models continue to register exactly as before;
4. selecting `illuminated_tube_proxy` before companion registration → no automatic registration side effect; Properties remains truthful/limited until the model exists;
5. opening/reopening Properties, switching candidates, preflight, and ordinary route changes → zero registration requests;
6. companion registration error → visible operator error, no fake registered state and no false successful refresh signal;
7. successful explicit registration → the already-mounted Properties controller refreshes authoritative model data for the same workspace, and normal navigation to Design exposes the companion without a full page reload;
8. the refresh itself performs read-side synchronization only and does not mutate working bindings, auto-select by semantic inference, create a run, or persist/register anything;
9. direct client manipulation cannot bypass the server-owned exact companion identity/guarded execution contract.

## 5. Review consequence

The Codex P1 delivered on PR #317 head `4ff02489ca8ae35a748316cdcc9bec267ed0e1ad` is valid: the previous allow-list could leave the production semantic companion unreachable on a fresh workspace or tempt an invalid selection-triggered persistence path.

The later Codex P2 delivered on head `d661240cb78702a3c47a998e54326ee1e8925748` is also valid: refreshing only `DomainFoundation` local state does not refresh the globally mounted Properties controller when `workspaceId` is unchanged. This correction closes that reachability gap with a bounded read-side synchronization seam and explicitly forbids a new store/framework or registration side effect.

After this correction is published, all deterministic/review evidence on older heads is stale for merge authority. The new exact head must pass fresh deterministic gates and receive an independent exact-head peer/GLM verdict confirming that registration is explicit, idempotent, reachable, side-effect free with respect to selection/Properties loading, and visible to the existing Properties controller without a page reload.

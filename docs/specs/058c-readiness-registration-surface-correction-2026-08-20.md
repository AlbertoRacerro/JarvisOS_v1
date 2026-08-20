# 058c — fresh readiness correction: explicit semantic-companion registration surface

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-2026-08-20-fresh.md` and `docs/specs/058c-readiness-provenance-correction-2026-08-20.md`  
Reason: exact-head review of PR #317 proved that server-side companion registration authority alone does not make the semantic companion reachable through the current operator workflow on a fresh workspace.

This correction is part of the 058c readiness decision. Where it conflicts with the fresh readiness record, this file governs. It changes no runtime code and does not promote `058c` from `planned`.

## 1. Failure mode closed

The fresh readiness correctly authorizes one idempotent server-owned semantic-companion registration path and requires a fresh workspace to be able to register that companion. However, its frontend allow-list does not include the only current explicit bundled-model registration surface, `frontend/src/pages/DomainFoundation.tsx`.

Current runtime exposes `onRegisterBundledModels()` there as the deliberate operator action that registers missing bundled BlueRev models. Merely adding a new API client function does not make the companion reachable. Conversely, automatically registering the companion from `EngineeringProperties` on selection/load would turn semantic inspection into a durable side effect and would violate the operator-first no-hidden-mutation boundary.

Therefore 058c V0 must extend the existing explicit registration action rather than introducing selection-triggered registration or an implicit background registration path.

## 2. Correct V0 registration contract

On a fresh workspace, the existing explicit **Register missing bundled models** action in `DomainFoundation` is the minimum normal product surface for semantic-companion creation.

Implementation must:

1. keep the existing registration action explicitly operator-triggered;
2. include the new reviewed-047 semantic companion in that same missing-bundled-model registration sequence;
3. preserve idempotency: if the companion already exists with the exact server-known identity, the action creates no duplicate;
4. preserve the existing legacy 047/048/049 registrations and their current labels/contracts/identity;
5. refresh the workspace model list after registration exactly as the current action already does;
6. surface registration failure through the existing operator message/error path;
7. never register a model merely because a BLUECAD object was selected, Properties opened, semantic metadata was read, or preflight ran.

The companion remains server-owned and exact-tuple guarded. The frontend registration surface supplies only explicit operator intent; it does not decide script/contract identity, applicability, provenance, or execution admission.

## 3. Minimum allow-list amendment

The fresh readiness Section 11 frontend allow-list is amended to add exactly:

- `frontend/src/pages/DomainFoundation.tsx` — only to extend the existing explicit bundled-model registration action and its current registered/missing state handling for the semantic 047 companion;
- focused frontend tests covering explicit registration/idempotent missing-state behavior if current test structure requires them.

No other page, navigation redesign, new registration wizard, automatic initialization hook, background effect, local persistence, provider path, or semantic state store is authorized.

`frontend/src/api/client.ts` remains authorized for the narrow companion registration call/type needed by this explicit action.

## 4. Acceptance added

Implementation acceptance gains these merge-blocking cases:

1. fresh workspace + explicit bundled-model registration action → semantic 047 companion is created through the normal server-owned endpoint;
2. repeating the same explicit action → no duplicate semantic companion;
3. legacy bundled models continue to register exactly as before;
4. selecting `illuminated_tube_proxy` before companion registration → no automatic registration side effect; Properties remains truthful/limited until the model exists;
5. opening/reopening Properties or switching candidates → zero registration requests;
6. companion registration error → visible operator error, no fake registered state;
7. after successful explicit registration and normal model refresh, the companion becomes available to the 058c eligibility/provenance gate;
8. direct client manipulation cannot bypass the server-owned exact companion identity/guarded execution contract.

## 5. Review consequence

The Codex P1 delivered on PR #317 head `4ff02489ca8ae35a748316cdcc9bec267ed0e1ad` is valid: the previous allow-list could leave the production semantic companion unreachable on a fresh workspace or tempt an invalid selection-triggered persistence path.

After this correction is published, all deterministic/review evidence on older heads is stale for merge authority. The new exact head must pass fresh deterministic gates and receive an independent exact-head verdict confirming that registration is explicit, idempotent, reachable, and side-effect free with respect to selection/Properties loading.

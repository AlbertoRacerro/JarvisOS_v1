# 092 — SCENE-BINDING-0 (operator-first re-derivation)

Status: **definition only**  
Date: 2026-08-19  
Depends on: 005, 006, 071b, 083, 084, 085, 095, 096

## 1. Purpose

Define the minimum scene-selection binding contract that lets a BLUECAD viewport selection resolve a stable real engineering object context for the operator-first Properties surface introduced by 071b.

This definition replaces the old interpretation of 092. A renderer mesh, primitive index, exporter order, material slot, scene-node name, or transient GLTF detail is not engineering identity. The scene is a presentation and hit-testing surface; engineering identity remains server/domain-owned.

This PR is definition only. It authorizes no runtime mutation. A separate exact-master readiness record must inspect current BLUECAD artifact/scene metadata, frontend viewer code, 071b Properties contracts, and backend engineering/CAD authority before 092 can become `ready`.

## 2. Operator contract

When the operator selects visible geometry, the normal result is a semantic selection context suitable for Properties and Jarvis context, not a machine-debug dump.

A resolved selection exposes, when authoritative data exists:

- human engineering tag/name as primary identity;
- engineering object kind/type;
- stable semantic object identifier used for subsequent reads/actions;
- relationship to the selected BLUECAD candidate/workspace;
- geometry source/reference sufficient to explain why the hit maps to that object;
- links to authoritative related objects such as stream/equipment/part only when those relationships already exist;
- a truthful unresolved/ambiguous state when deterministic resolution is impossible.

Opaque UUIDs, mesh indices, node paths and exporter metadata belong to Inspect/Audit and must not dominate the Properties header.

## 3. Authority and state ownership

092 must reuse existing authority. It must not create a second engineering-object store, duplicate Parameters/Assumptions/Decisions, or persist frontend-only identities as canonical records.

Ownership is separated as follows:

1. backend engineering/model/CAD records own semantic engineering identity and relationships;
2. generated BLUECAD artifacts may carry deterministic binding metadata sufficient to map rendered geometry back to those records;
3. the frontend viewer owns only ephemeral hit/selection state and requests/resolves semantic context;
4. 071b owns editable working configuration and deterministic preflight; 092 does not become a second working-state owner;
5. Properties renders the resolved engineering context through existing/authorized contracts; Jarvis may receive a compact human-readable context reference but does not own selection identity.

If current artifacts cannot carry a stable deterministic mapping without a bounded additive seam, readiness must identify the smallest server/exporter-owned seam and prove why existing metadata is insufficient before authorizing it.

## 4. Deterministic binding

Binding must be deterministic for a fixed candidate/artifact and semantic engineering state. Resolution may use existing authoritative metadata such as part IDs, stable CAD entity metadata, artifact manifests or server-owned mapping tables only after readiness verifies their actual runtime shape.

Forbidden identity shortcuts include:

- `mesh[17]` or primitive order as engineering identity;
- material/color as identity;
- display label alone when labels are not unique;
- array position/export traversal order;
- heuristics based only on bounding box, nearest name, or visual similarity;
- model-generated guesses.

If multiple semantic objects legitimately correspond to one visible hit, the contract must return explicit ambiguity or a bounded choice derived from authoritative relationships. It must not silently pick one by order.

## 5. Selection lifecycle and stale safety

Selection is ephemeral UI state but must be revision-aware enough to avoid showing Properties for stale geometry.

The runtime implementation must fail closed or clear/re-resolve selection when any of these changes invalidate the binding:

- candidate/artifact changes;
- workspace changes;
- viewport reload replaces the scene;
- selected semantic object is deleted/unavailable;
- mapping metadata revision no longer matches the rendered artifact;
- an async resolution response returns after a newer selection/candidate became current.

Late responses may not overwrite a newer selection. Selection clear/unmount must not trigger unrelated Jarvis provider calls or mutate working configuration.

## 6. Properties integration

A successfully resolved semantic selection drives the object header and available property context in the existing bounded Properties pane.

092 does not invent model/property semantics. It supplies the semantic target and existing authoritative relationships. 071b/058c determine what editable/derived fields exist.

Required UI states:

- **No selection** — neutral Properties state; no fabricated object.
- **Resolving** — bounded progress state without stale prior-object mutation.
- **Resolved** — human engineering identity primary; machine identity secondary.
- **Unresolved** — selected geometry has no authoritative semantic binding; explain this truthfully and expose technical hit data only under Inspect/Audit if useful.
- **Ambiguous** — more than one authoritative target; require deterministic/operator resolution rather than guessing.
- **Stale/removed** — clear or mark unavailable; never keep editing a target that is no longer current.

A scene hit alone never grants mutation authority. Editing still flows through 071b working-configuration validation.

## 7. Linked engineering context

092 may expose authoritative links from the selected object to related engineering objects so Properties can show contextual linked values without duplicating their authority.

Examples include a part linked to an equipment item or a process stream, but only where current backend records prove the relationship. A linked value remains authoritative at its source. Selection does not copy that value into a new scene-owned record.

Navigation to a linked source should preserve human engineering identity and provide a deterministic way back to the selected object when practical. Exact behavior is frozen in readiness from current routing/components.

## 8. Jarvis integration boundary

Selection may update the compact Jarvis context chip with human-readable engineering identity. It must not inject raw geometry dumps, UUID lists, full property tables or raw GLTF metadata into normal chat presentation.

092 does not authorize Jarvis to mutate engineering state. Structured Jarvis mutations remain 097 and must target the semantic identity/working revision exposed by the later action contract.

Selection changes alone do not automatically call an AI provider. Any later AI context use remains subject to existing routing, sensitivity, egress and budget authority.

## 9. Failure modes that readiness must prove

Readiness must inspect exact runtime and freeze acceptance for at least:

1. two visually similar parts do not alias because of mesh/export order;
2. a candidate reload/re-export with reordered primitives still resolves the same engineering object when semantic authority is unchanged;
3. a stale async selection response cannot replace a newer selection;
4. switching candidate/workspace clears or re-resolves prior selection before Properties can edit it;
5. missing binding metadata yields truthful unresolved state, not guessed identity;
6. duplicate/non-unique display labels do not create ambiguous hidden identity;
7. malformed/hostile metadata is rendered inertly and cannot create page overflow or script execution;
8. deleted/unavailable semantic target fails closed;
9. linked values remain source-owned and are not duplicated into scene state;
10. selection does not mutate canonical project data, working configuration, run history or provider state;
11. keyboard-accessible selection/clear and focus behavior remains usable;
12. effective 200%/compact sidecar degradation preserves the same semantic selection when panes tab between Jarvis and Properties;
13. scene load/error/unmount does not leave an editable stale Properties target.

## 10. Responsive, accessibility and containment

The implementation must preserve merged 096 sidecar containment and existing viewport keyboard/focus behavior. Selection indication cannot rely on color alone. Long human labels and machine identifiers must wrap/truncate without page-level horizontal overflow. Inspect/Audit technical metadata remains bounded/collapsed.

No new global visual identity is authorized. Styling must use the existing UI foundation and current workstation language.

## 11. Migration and rollback

The implementation must be additive over current candidate viewing. Existing candidates/artifacts without new binding metadata must remain viewable; they may resolve to an explicit `Unresolved engineering binding` state rather than being rejected solely for lacking future metadata.

If readiness authorizes an additive artifact/server binding field, absence must be backward compatible and migration must not rewrite historical artifacts merely to satisfy the UI.

Rollback is removal of the bounded semantic-binding seam/UI integration while preserving existing viewer/candidate behavior and all canonical engineering records.

## 12. Non-goals

092 does **not** implement:

- 058c model selectors, inactive-model value retention or formula/`fx` semantics;
- 097 Jarvis engineering mutations;
- 098 engineering-record lifecycle mutations;
- 006b variants or loading prior runs as working configurations;
- 058b comparison;
- a general editable flowsheet or Aspen-like process topology editor;
- geometry authoring, CAD constraint solving or mesh editing;
- a second engineering object/parameter database;
- AI-based object recognition as identity authority;
- Notes, 062 grading UI, dense spreadsheet editing or global visual identity.

## 13. Readiness requirements

Before runtime authorization, a separate 092 readiness record from fresh master must:

1. inspect the exact current BLUECAD viewer/GLTF loader and selection seams;
2. inspect current CAD artifact manifests/export metadata and identify what stable semantic keys actually exist;
3. inspect backend engineering/CAD relationships and 071b Properties integration;
4. choose the minimum deterministic mapping strategy and explicitly reject weaker alternatives;
5. freeze exact frontend/backend/exporter file allow-list;
6. freeze request/response or artifact metadata shape if an additive seam is necessary;
7. prove stale/candidate-switch behavior and no duplicate engineering authority;
8. freeze deterministic tests plus a browser matrix covering the failure modes above;
9. document backward compatibility for historical candidates without the mapping;
10. preserve 058c/097/098/006b/058b boundaries.

If no stable deterministic mapping can be obtained from existing authority plus one bounded additive seam, readiness must stop rather than inventing identity heuristics.

## 14. Acceptance criteria for the eventual implementation

092 is complete only when exact-head evidence proves:

- a visible scene hit can resolve to a stable authoritative engineering object context where mapping exists;
- exporter/mesh ordering is not identity;
- unresolved/ambiguous/stale cases fail closed and remain inspectable;
- Properties receives the semantic target without becoming a second state owner;
- linked values remain source-owned;
- selection cannot mutate working/canonical/run/provider state by itself;
- stale async responses cannot overwrite newer selection;
- 096 containment, accessibility, compact/effective-200% behavior and theme invariants remain intact;
- no downstream 058c/097/098/006b/058b behavior is smuggled into this slice.

## 15. Downstream seam

After 092 is implemented, merged and reconciled, 058c may define engineering scene/object semantics over the stable selected target: property groups, mutually exclusive model choices, inactive-value retention, derived/formula Inspect content and dependency semantics.

092 deliberately stops at **identity and binding**. It answers `what engineering object did the operator select?`; it does not answer every question about how that object's engineering model behaves.
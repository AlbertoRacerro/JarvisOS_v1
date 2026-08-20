# 058c — fresh readiness correction: selected-object provenance

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-2026-08-20-fresh.md`  
Reason: exact-head review of PR #317 proved that `partKind == "tube_run"` alone is not sufficient authority for the reviewed-047 selected-object semantics, and that row status alone is not sufficient authority for linked-Parameter freshness.

This correction is part of the 058c readiness decision. Where it conflicts with the fresh readiness record, this file governs. It changes no runtime code and does not promote 058c from `planned`.

## 1. Failure modes closed

The fresh readiness correctly proves that the reviewed 047 CAD link creates one `tube_run` proxy from exactly `tube_length`, `tube_inner_diameter`, and `tube_outer_diameter`. However, current runtime also creates unrelated `tube_run` parts, including common and branch tubing in the 072 topology path. Ordinary BLUECAD candidates may also contain `tube_run` parts.

Therefore this rule is invalid and is superseded:

> selected part kind matches implementation/variable `applicable_part_kinds` ⇒ the reviewed-047 companion is an object-semantic candidate.

`partKind` is necessary applicability metadata but is **not sufficient provenance**. Using it alone could present a topology segment or unrelated tube as governed by the global reviewed-047 geometry/hydraulics model and could let an operator execute that model from the wrong selected-object context.

The fresh readiness also treated linked-Parameter `status == "superseded"` as the relevant stale-source guard. Current 051 runtime proves that this is insufficient: downstream nodes can remain `proposed`/`accepted` while canonical `freshness_marks` records them stale after an upstream replacement. Therefore row status is not canonical freshness authority and cannot by itself admit a linked Parameter to preview or execution.

## 2. Exact current authority

Fresh runtime inspection establishes these distinct facts:

- `backend/app/modules/bluecad/cad_link.py` creates the reviewed-047 M0 proxy with transformation version `bluerev_047_m0_tube_proxy_v0_1` and records a canonical `bluecad_cad_links` row binding the source simulation run to the exact `child_candidate_id`;
- that same path emits the single canonical part `part_id="illuminated_tube_proxy"`, `kind="tube_run"`;
- `backend/app/modules/bluecad/cad_link_topology_contract.py` creates multiple unrelated `tube_run` parts for the 072 topology, so part kind cannot discriminate provenance;
- `BluecadCandidateRead.origin == "process_linked"` is also insufficient by itself because it is a broad candidate-origin category, not the exact 047 transformation/model relationship;
- the current read aggregate does not expose the canonical `bluecad_cad_links` transformation/source identity as structured selected-object provenance;
- `backend/app/modules/flowsheet/freshness.py` and its canonical `freshness_marks` lookup own node freshness; a linked Parameter's own row status is not a substitute for that lookup.

The canonical link table, not candidate notes, labels, scene names, `origin`, mesh identity, part order, or part kind by itself, is the authoritative source for this V0 eligibility decision. Canonical flowsheet freshness, not a Parameter row-status shortcut, is the authoritative source for whether a linked Parameter may participate in preview/execution.

## 3. Correct V0 applicability gate

The reviewed-047 semantic companion is eligible as the selected-object semantic model only when **all** of the following are true for the current 092 target:

1. workspace, candidate, artifact and viewer-session identity are current under merged 092 stale-safety;
2. canonical selected `partId` is exactly `illuminated_tube_proxy`;
3. canonical selected `partKind` is exactly `tube_run`;
4. the current candidate is the `child_candidate_id` of a same-workspace canonical `bluecad_cad_links` row;
5. that link has exact transformation version `bluerev_047_m0_tube_proxy_v0_1`;
6. the link's source run/model identity satisfies the existing reviewed-047 CAD-link identity contract rather than a label-only or frontend-inferred approximation.

If any condition is missing, stale, ambiguous, malformed or false, the selected object remains truthfully identified by 092 but **does not receive reviewed-047 object-semantic groups**. Generic 071b model configuration remains available where otherwise valid.

No fallback is permitted from candidate origin, brief text, notes, part naming similarity, category, unit, geometry, mesh/node metadata, or a nearby associated run.

## 4. Minimum read projection authorized by readiness

Because the frontend currently has candidate ID but does not receive structured exact-047 link provenance, implementation may make one bounded additive read-only extension to the existing BLUECAD candidate aggregate rather than creating a new service/store.

The preferred minimum seam is `backend/app/modules/bluecad/read_model.py` plus its existing `/candidates/{candidate_id}/aggregate` response model/route only as needed to expose an inert semantic-source discriminator derived from the canonical `bluecad_cad_links` row.

The projection must be bounded to facts needed for eligibility, for example:

- source kind such as `cad_link_047_m0` only after exact canonical-link verification;
- exact transformation version;
- source simulation-run/model identity or a server-owned verified boolean/typed discriminator sufficient to prove the reviewed-047 relationship.

It must **not** duplicate engineering values, create a new durable semantic record, expose arbitrary SQL rows, infer provenance from notes, or make the frontend responsible for verifying raw model hashes. The server owns provenance verification; the frontend only consumes the bounded result.

If implementation inspection proves the existing aggregate can establish the same exact relationship without extending its response, no new field is required. If it cannot, `read_model.py` and focused aggregate/API tests are added to the Section 11 implementation allow-list as the minimum necessary exception. No new route is authorized by default.

## 5. Correction to schema-v3 applicability semantics

The schema-v3 `semantic_context.applicable_part_kinds` and variable-level `applicable_part_kinds` remain valid but become only one layer of eligibility.

For this reviewed-047 V0:

`exact source provenance AND exact selected part identity AND schema-v3 applicability`

are all required before object-specific fields render.

Schema metadata alone never elevates an unrelated candidate into the 047 semantic family. Conversely, canonical 047 provenance does not make the six generic reviewed-047 inputs intrinsic selected-tube properties; only the three CAD-link-proven geometry inputs remain object-specific.

## 6. Linked-Parameter freshness correction

Every linked Parameter used by 058c must pass the existing canonical node-freshness authority in addition to any row-status and unit/type checks. Preview and the final pre-persistence execution guard must query the canonical freshness path used by the flowsheet runtime; they must not infer freshness from `status != "superseded"`.

Required behavior:

- explicitly superseded linked Parameter → fail closed;
- linked Parameter marked stale in canonical `freshness_marks`, even if its row remains `proposed`, `accepted`, or another otherwise admissible status → fail closed;
- downstream Parameter made stale by upstream replacement → fail closed until canonical freshness is restored by the owning runtime path;
- missing/ambiguous freshness authority where freshness is required → fail closed rather than assume fresh;
- the same freshness decision must be revalidated immediately before run persistence/execution so a preview cannot authorize a source that became stale afterward.

058c must reuse the existing flowsheet freshness authority and must not create a parallel freshness store, frontend freshness heuristic, or new lifecycle status.

## 7. Frontend behavior correction

For a resolved 092 `bluecad-part`, `EngineeringProperties` may show the reviewed-047 object-semantic `Geometry` group only after the current candidate aggregate proves the exact source gate above.

Required negative behavior:

- 072 topology `tube_run` → no reviewed-047 selected-object semantic group;
- ordinary/AI/parametric `tube_run` → no reviewed-047 selected-object semantic group;
- process-linked candidate without the exact 047 canonical link → no reviewed-047 selected-object semantic group;
- exact 047 child candidate but wrong part ID/kind → no reviewed-047 selected-object semantic group;
- stale/missing/ambiguous link provenance → limited/unresolved semantic state, never guessed applicability.

The generic model configuration surface remains usable and must not be conflated with selected-object ownership.

## 8. Stale safety

The provenance projection is part of the current selected-object context and is stale whenever candidate/workspace selection is stale. A late aggregate/provenance response for candidate A cannot authorize semantic rendering or editing after selection has moved to candidate B.

The frontend must bind eligibility to the same current workspace/candidate/artifact/viewer-session/selection generation already required by 092/071b. No provider call, Jarvis mutation, run creation, canonical promotion or implicit model switch occurs merely because provenance resolves.

Linked-Parameter freshness is a separate server-owned execution precondition and must be rechecked at preview and immediately before persistence/execution; frontend selection freshness cannot substitute for canonical node freshness.

## 9. Deterministic and browser acceptance added

The implementation acceptance matrix gains these merge-blocking cases:

1. exact 047 CAD-link child + selected `illuminated_tube_proxy` → reviewed-047 Geometry semantics available;
2. 072 topology candidate + any `tube_run` segment → reviewed-047 selected-object semantics absent;
3. ordinary BLUECAD `tube_run` candidate → reviewed-047 selected-object semantics absent;
4. `process_linked` candidate without exact `bluecad_cad_links` 047 transformation → absent;
5. forged/malformed candidate notes or origin cannot manufacture eligibility;
6. wrong/missing/stale link row fails closed;
7. candidate switch while provenance read is in flight cannot leak old semantic eligibility into the new selection;
8. generic 071b configuration remains reachable for non-eligible objects without presenting it as object ownership;
9. direct guarded execution of the semantic companion remains exact server-known and is not authorized merely by client-selected candidate metadata;
10. a linked Parameter that is canonically stale through downstream propagation but is not itself `superseded` is rejected by preview;
11. the same downstream-stale/non-superseded Parameter becoming stale after preview is rejected by the final pre-persistence execution check.

Tests must include at least one actual 072 `tube_run` negative fixture because that is the concrete collision that exposed the provenance failure mode, and at least one actual downstream-stale/non-superseded Parameter fixture exercising the canonical freshness lookup.

## 10. Allow-list amendment

The fresh readiness Section 11 allow-list is amended only as follows:

- `backend/app/modules/bluecad/read_model.py` and focused read-model/API tests may be touched if required to project exact canonical 047 CAD-link provenance through the existing aggregate;
- `backend/app/modules/bluecad/routes.py` may change only if the existing aggregate response model requires the additive projection; no new route is authorized by default;
- the existing flowsheet freshness query/service path and focused preview/execution tests may be touched only as necessary to reuse canonical node freshness for linked-Parameter admission; no new freshness store/status/route is authorized;
- corresponding additive type consumption in `frontend/src/api/client.ts` is already within the existing frontend allow-list.

No other BLUECAD persistence, CAD-link execution, scene-binding, topology, provider, schema-migration or state-owner change is authorized by this correction.

## 11. Review consequence

The Codex P1 on original PR #317 head `50da32efb25382882fd90ca978965cb6b83fb5a1` and the canonical-freshness P1 on head `6fc4d9688f570896e70f9e793e257184811c3541` are materially valid and block those heads from merge. CI PASS on either head does not override the semantic findings.

After this correction is published, all prior exact-head review/gate evidence is stale for merge authority. The new exact head must pass deterministic gates and receive a fresh independent read-only verdict confirming both that 047 selected-object semantics are provenance-bound with 072/ordinary `tube_run` candidates failing closed, and that stale linked Parameters are rejected through canonical freshness even when their own row status is not superseded.

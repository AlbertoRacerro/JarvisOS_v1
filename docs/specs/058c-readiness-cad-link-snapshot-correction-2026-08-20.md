# 058c — fresh readiness correction: CAD-link snapshot working baseline

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-2026-08-20-fresh.md` and all prior PR #317 readiness corrections  
Reason: exact-head review proved that exact 047 CAD-link provenance can identify the selected object while the existing 071b working bindings still initialize empty, allowing Properties and a later run to diverge from the canonical geometry snapshot that generated that object.

This correction is part of the 058c readiness decision. Where it conflicts with the earlier prohibition on projecting engineering values from the CAD-link record, this file governs. It changes no runtime code and does not promote 058c from `planned`.

## 1. Failure mode closed

For the exact reviewed-047 CAD-link child, `bluecad_cad_links.source_snapshot_json` is not an arbitrary duplicate or frontend inference. It is the canonical immutable source snapshot captured by `backend/app/modules/bluecad/cad_link.py` from the succeeded reviewed-047 run and used to resolve the geometry that produced the child candidate.

Merged 071b, however, initializes ordinary working bindings independently. If 058c only projects provenance and semantic labels, selection of canonical `part_id="illuminated_tube_proxy"` can truthfully identify the 047 child while showing empty/manual values for `tube_length`, `tube_inner_diameter`, and `tube_outer_diameter`. A subsequent run could then use values unrelated to the geometry being inspected.

That state is invalid for selected-object semantics: the initial effective Geometry values and their source must correspond to the exact source snapshot that generated the selected candidate.

## 2. Minimum source-owned read projection

For an object that passes the full selected-object applicability gate in the provenance correction, implementation is authorized to extend the same bounded existing BLUECAD candidate aggregate projection with the three CAD-link geometry snapshot bindings required by V0:

- `tube_length`;
- `tube_inner_diameter`;
- `tube_outer_diameter`.

The server reads these values from the exact same-workspace canonical `bluecad_cad_links.source_snapshot_json` row already used to prove eligibility and validates that the snapshot is well formed and consistent with the exact reviewed-047 CAD-link relationship. The frontend must not parse candidate notes, infer dimensions from GLB geometry, reconstruct values from scene bounds, or query raw SQL-shaped data.

The projection should remain typed and bounded to the three proven geometry inputs and the minimum source metadata needed by the existing 071b binding model, including canonical source Parameter identity/unit where already present in the snapshot. It must not expose the whole CAD-link row or turn the aggregate into a general engineering-value store.

This is a read projection of an existing immutable source snapshot, not a new durable semantic store and not a second working-state owner.

## 3. Adoption into the existing 071b working state

When the current 092 selection first resolves to an eligible exact 047 CAD-link child, the existing `EngineeringProperties` owner must adopt the three projected CAD-link snapshot bindings as the selected object's **source-owned working baseline** before presenting editable effective Geometry values.

Required semantics:

1. initial effective values for the three Geometry fields equal the canonical CAD-link source snapshot that generated the selected candidate;
2. source/provenance is shown semantically as the CAD-linked source (for example `Linked stream`/`CAD-linked source` according to the existing operator-facing vocabulary), never as `User` or an invented validation claim;
3. adoption initializes/rebases only the three eligible object-semantic fields in the existing 071b owner; it does not create another store, mutate canonical Parameters, alter the immutable CAD-link snapshot, create a run, register a model, or invoke Jarvis/provider paths;
4. subsequent operator edits are ordinary 071b working overrides with dirty/Undo/Revert behavior; Revert for these fields returns to the adopted CAD-link baseline;
5. generic reviewed-047 inputs remain governed by the ordinary 071b configuration state and are not populated from object geometry;
6. a non-eligible object receives no snapshot adoption;
7. selection/candidate/workspace changes are stale-safe: a late aggregate response from an old selection cannot rebase the current working state;
8. repeated reads of the same unchanged eligible source are idempotent and must not erase legitimate current working edits merely because Properties re-rendered or the aggregate was refetched.

The exact implementation may use a minimal source-baseline adoption helper inside the existing 071b controller. It may not add a global store, event framework, hidden persistence, automatic canonical promotion, or general prior-run loading machinery from 006b.

## 4. Freshness and identity boundary

Snapshot adoption is authorized only after the full provenance gate succeeds for the exact current workspace/candidate/artifact/viewer session and exact `illuminated_tube_proxy` / `tube_run` identity.

The snapshot is historical source truth for the geometry that generated the candidate; it does not by itself prove that a linked Parameter is currently fresh for a new execution. Therefore the canonical 051 linked-Parameter freshness rules from the prior correction still apply independently at preview and immediately before persistence/execution.

If a projected source Parameter is canonically stale or otherwise inadmissible for execution, Properties may still truthfully inspect the historical candidate/source relationship, but deterministic preflight/run admission must fail closed until the operator supplies an admissible working binding. The UI must not relabel historical snapshot evidence as current validation.

## 5. Acceptance additions

The implementation acceptance matrix gains these merge-blocking cases:

1. exact eligible 047 child selection initializes `tube_length`, `tube_inner_diameter`, and `tube_outer_diameter` to the exact values/units in the canonical CAD-link source snapshot;
2. the three initial rows expose truthful linked/CAD source provenance rather than `User`;
3. editing one adopted field creates ordinary dirty working state; Undo/Revert returns to the CAD-link snapshot baseline without mutating canonical Parameters or the CAD-link record;
4. refetch/re-render of the same unchanged selection does not overwrite an existing dirty working edit;
5. switching from eligible candidate A to candidate B while A's aggregate is in flight cannot adopt A's snapshot into B;
6. 072/ordinary/non-047 `tube_run` selections never receive 047 snapshot values;
7. a canonically stale linked Parameter remains execution-blocking even when its historical value is present in the CAD-link snapshot;
8. no selection, aggregate read, or snapshot adoption creates a model registration, simulation run, canonical Parameter mutation, Jarvis action, or provider call.

Tests must compare against the persisted canonical source snapshot, not hard-coded UI-only fixture values.

## 6. Allow-list amendment

The existing PR #317 implementation allow-list is amended only as needed for this source-baseline seam:

- `backend/app/modules/bluecad/read_model.py` and the existing candidate aggregate response/types/tests may project the bounded three-field canonical CAD-link snapshot alongside the already-authorized exact provenance discriminator;
- `backend/app/modules/bluecad/routes.py` may change only if required by the existing aggregate response model; no new route is authorized by default;
- `frontend/src/api/client.ts` may consume the additive typed projection;
- `frontend/src/components/engineering/EngineeringProperties.tsx` and its focused tests may adopt the snapshot into the existing 071b baseline/working owner with the stale/idempotency rules above.

No new durable state, schema migration, CAD-link write behavior, scene-binding authority, generic snapshot service, 006b prior-run loader, 097 Jarvis action, 098 lifecycle behavior, provider path, or hidden persistence is authorized.

## 7. Review consequence

The Codex P1 on PR #317 head `1bafe51cd466f7bc659afea897dfaf8a121bd8a5` is materially valid and blocks that head from merge. This correction closes the specification gap by making the exact canonical CAD-link snapshot the initial source-owned baseline for the three proven selected-object Geometry fields while preserving 071b as the sole mutable working-state owner.

After this correction is published, all prior exact-head CI/review evidence is stale for merge authority. The new exact head must pass deterministic gates and receive a fresh independent peer/GLM verdict confirming the snapshot-baseline, stale-selection, dirty-edit preservation, canonical-freshness, provenance, registration-reachability and runner pre-persistence boundaries.
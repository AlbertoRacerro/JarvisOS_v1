# 058c — fresh readiness correction: exact semantic read/schema contract

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-2026-08-20-fresh.md` and all prior PR #317 readiness corrections  
Reason: exact-head review proved readiness ambiguities in the candidate-aggregate provenance projection and schema-v3 semantic string contract. A later exact-head review also proved that candidate provenance and current selected-part validation must be split across their actual authority surfaces.

This correction is part of the 058c readiness decision. Where it conflicts with earlier illustrative/alternative wording, this file governs. It changes no runtime code and does not promote 058c from `planned`.

## 1. Exact candidate-aggregate semantic-source projection

If the existing aggregate cannot prove the exact reviewed-047 relationship without an additive field, implementation uses exactly one optional aggregate field named `semantic_source` with this response shape:

```json
{
  "semantic_source": {
    "schema_version": 1,
    "kind": "cad_link_047_m0",
    "transformation_version": "bluerev_047_m0_tube_proxy_v0_1",
    "source_simulation_run_id": "<canonical simulation_runs.id>",
    "source_model_version_id": "<verified model_versions.id>",
    "geometry_bindings": {
      "tube_length": {"value": 12.0, "unit": "m", "source_parameter_id": "<canonical parameters.id>"},
      "tube_inner_diameter": {"value": 80.0, "unit": "mm", "source_parameter_id": "<canonical parameters.id>"},
      "tube_outer_diameter": {"value": 90.0, "unit": "mm", "source_parameter_id": "<canonical parameters.id>"}
    }
  }
}
```

`semantic_source` is either the complete object above or `null`. There is no alternative boolean/raw-row/hash-only representation and no union of multiple semantic-source shapes in V0.

### 1.1 Server construction and validation — candidate provenance only

The existing candidate aggregate is a **candidate-scoped** read surface. It receives workspace/candidate identity and does not receive, reconstruct, or own the current 092 selected-part identity, artifact, viewer session, or selection generation. It therefore MUST NOT claim to validate those frontend-owned current-selection facts.

The server may emit `kind="cad_link_047_m0"` only after all candidate/link provenance conditions below succeed against one same-workspace canonical `bluecad_cad_links` row:

- `child_candidate_id` equals the requested candidate;
- `transformation_version` equals exactly `bluerev_047_m0_tube_proxy_v0_1`;
- stored `source_model_identity_json` and its digest are well formed and resolve to the exact verified reviewed-047 model identity already required by CAD-LINK-0;
- `source_simulation_run_id` and `model_version_id` are canonical existing same-workspace identities consistent with that link;
- `source_snapshot_json` and its digest are well formed;
- the snapshot contains exactly usable entries for `tube_length`, `tube_inner_diameter`, and `tube_outer_diameter` with the expected units and canonical Parameter references.

The typed discriminator therefore means only: **the requested candidate has server-verified same-workspace reviewed-047 CAD-link provenance and a valid immutable geometry source snapshot**. It does not mean that any arbitrary currently selected part in that candidate is eligible.

The frontend does not verify raw model hashes or infer candidate provenance from response fields. Candidate provenance is server-owned; current selected-object identity and stale-context validation are frontend-owned as frozen below.

### 1.2 Frontend adoption gate — current 092 selected object and stale context

Before `semantic_source` may seed the existing 071b working baseline or expose the reviewed-047 selected-object semantic groups, the already-mounted frontend composition must independently verify all of the following against the **current** 092 resolved selection:

- the response still belongs to the current workspace and candidate;
- the current 092 target is resolved, not ambiguous/unresolved;
- current canonical `partId` is exactly `illuminated_tube_proxy`;
- current canonical `partKind` is exactly `tube_run`;
- current artifact identity/digest, viewer session/generation and selection generation still match the request/adoption context according to the merged 092 stale-safety contract;
- the response contains the exact known `semantic_source.schema_version=1` and `kind="cad_link_047_m0"` shape defined here.

If any condition fails, the frontend treats the semantic source as ineligible/limited and performs **no baseline adoption**. It must not ask the candidate aggregate to validate part identity, add selected-part query parameters, create a new route, or infer eligibility from candidate origin, notes, mesh/name/order/material/bounds, associated-run heuristics, or part-kind alone.

This split is binding: server verifies candidate/link provenance; merged 092 verifies current selected-object identity and stale context at frontend adoption. Neither side duplicates the other's authority.

### 1.3 Exact geometry binding field semantics

Each `geometry_bindings` entry has exactly:

- `value`: finite JSON number obtained from the corresponding persisted CAD-link source snapshot `executed_value`; bool, NaN, infinities and values not safely convertible by the server are invalid and fail closed;
- `unit`: exact literal `m` for `tube_length`, exact literal `mm` for both diameter fields;
- `source_parameter_id`: non-empty canonical Parameter ID from the persisted snapshot's `parameter_ref`, after same-workspace Parameter existence is verified.

No fourth geometry key is allowed in this V0 projection. Missing, duplicated, wrong-unit, malformed or non-finite source data makes the entire `semantic_source` projection unavailable; the server must not emit a partial semantic-source object.

The projected numeric values are a typed read view of the immutable source snapshot. Tests compare them to the persisted snapshot after the same decimal-to-finite-number conversion performed by the server; hard-coded UI fixture values are not authority.

### 1.4 Null and error behavior

- Candidate with no matching canonical reviewed-047 link: `semantic_source: null`; this is a normal limited-semantic state and does not by itself add a diagnostic.
- A matching/claimed link whose row, model identity, snapshot, Parameter reference, digest or same-workspace relationship is malformed/inaccessible/conflicting: `semantic_source: null` and append a bounded existing aggregate diagnostic with `source="bluecad.semantic_source"` and the closest existing diagnostic code (`malformed_reference`, `missing_reference`, or `inaccessible_reference`).
- More than one canonical row attempting to claim the same candidate for this exact semantic relationship is ambiguous: fail closed to `null` plus `malformed_reference`; never pick by row/order/time.
- The frontend treats `null`, unknown `schema_version`, unknown `kind`, missing required field, extra incompatible shape, wrong unit or malformed geometry binding as ineligible/limited semantics and never falls back to `origin`, notes, part-kind-only, mesh/name/order/bounds or associated-run heuristics.
- A late aggregate response remains subject to the frontend adoption gate in §1.2 before it may adopt the source baseline.

No new route or request parameter is authorized. The existing candidate aggregate remains the candidate-provenance read surface.

## 2. Exact schema-v3 semantic string bounds

The schema-v3 semantic fields use these deterministic validation rules. Implementations must reject, not truncate or silently normalize, values outside them.

### 2.1 Machine identifiers

The following fields are ASCII machine identifiers:

- `semantic_context.applicable_part_kinds[*]`;
- `semantic_context.model_family_key`;
- `variables[*].applicable_part_kinds[*]`.

Each identifier:

- length: 1–64 ASCII characters;
- pattern: `^[A-Za-z][A-Za-z0-9_]{0,63}$`;
- no leading/trailing whitespace;
- exact case-sensitive matching;
- no hyphen, dot, slash, colon, wildcard, control character or Unicode confusable;
- duplicate values in an applicability list are invalid rather than deduplicated.

Implementation-level applicability remains 1–16 unique identifiers. Variable-level applicability remains 0–16 unique identifiers. Every non-empty variable-level identifier must occur exactly in the implementation-level list.

### 2.2 Human semantic labels

The following fields are human labels:

- `semantic_context.model_family_label`;
- `semantic_context.model_option_label`;
- `variables[*].property_group`.

Each human label:

- length: 1–120 Unicode code points;
- must already be Unicode NFC; non-NFC input is rejected rather than rewritten;
- must equal `value.strip()` (no leading/trailing whitespace);
- must be single-line: no `\r`, `\n`, or `\t`;
- may contain normal engineering punctuation and Unicode symbols but no Unicode control characters in categories `Cc` or `Cf`;
- is presentation text only and has no identifier, Markdown/HTML, script, route or execution authority.

These fields remain separate from the existing v1/v2 `name`, `label`, `unit`, `description`, `physical_dimension`, and `semantic_basis` constraints, which are unchanged.

### 2.3 Canonicalization consequence

Schema-v3 canonicalization validates the exact rules above before canonical JSON/digest generation. It does not trim, case-fold, Unicode-normalize, reorder lists to repair input, or otherwise rewrite invalid semantic metadata. Existing schema-v1/v2 canonical bytes remain byte-for-byte unchanged.

The checked-in reviewed-047 V0 companion therefore uses the exact valid values already frozen by readiness:

- part kind `tube_run`;
- family key `geometry_hydraulics`;
- family label `Geometry and hydraulics model`;
- option label `Reviewed 047 tubular-loop V0`;
- property groups `Geometry` and `Operating` where applicable.

## 3. Acceptance additions

The eventual implementation gains these merge-blocking deterministic cases in addition to all earlier PR #317 corrections:

1. candidate aggregate returns the exact complete `semantic_source` shape for one valid same-workspace reviewed-047 CAD-link child **without requiring or pretending to validate a selected part**;
2. ordinary/072/non-047 candidates return `semantic_source: null` and never receive reviewed-047 selected-object groups;
3. malformed source-model identity, bad digest, wrong transformation, wrong workspace, missing Parameter, malformed/partial snapshot and duplicate/ambiguous link all fail closed without partial projection;
4. unknown semantic-source schema/kind or malformed response is inert in the frontend; no heuristic fallback occurs;
5. the three projected values/units/source Parameter IDs match the persisted canonical source snapshot through the server's defined conversion;
6. for a valid reviewed-047 candidate, selecting exact `illuminated_tube_proxy`/`tube_run` permits baseline adoption, while selecting any other resolved part identity/kind does not, even if the candidate-level `semantic_source` is non-null;
7. a workspace/candidate/artifact/viewer-session/selection-generation change before response adoption rejects the late semantic source and does not rebase dirty/current Properties state;
8. machine identifiers accept boundary lengths 1 and 64, reject length 65 and reject punctuation/Unicode/control characters outside the exact grammar;
9. human labels accept valid NFC engineering punctuation through 120 code points, reject 121 code points, edge whitespace, non-NFC, multiline/tab and control/format characters;
10. duplicate applicability values and variable applicability not contained in implementation applicability are rejected;
11. schema-v1/v2 canonical payload/digest fixtures remain unchanged.

## 4. Allow-list consequence

No new implementation area is introduced beyond the existing corrected readiness allow-list. The exact candidate provenance projection is implemented only through the already-authorized existing candidate aggregate/read-model surface and client consumption. Current selected-part/stale-context eligibility is implemented only through the already-authorized merged-092 selection/composition consumption seam; it does not modify 092 identity authority. The exact schema-v3 bounds are implemented only in the already-authorized runner input-contract parser/schema-v3 tests and the checked-in companion contract.

No new database/store, route, provider, scene identity, lifecycle status, model option, formula infrastructure, event framework, hidden persistence, 097/098/006b/058b behavior, Notes, 062 grading or global visual-identity work is authorized.

## 5. Review consequence

The exact-head P1 findings on older PR #317 heads concerning provenance applicability, canonical freshness, registration reachability/refresh, CAD-link snapshot adoption, an unfrozen provenance response shape, unfrozen schema-v3 string bounds, and candidate-vs-selection authority were materially valid and block those older heads from merge.

This correction closes the candidate-vs-selection authority ambiguity by freezing the actual split instead of forcing the candidate-only server aggregate to validate frontend-only selection state. All gate/review evidence from older heads is stale for merge authority. No further Codex review is authorized for PR #317; the final immutable head must pass fresh deterministic gates and receive an independent non-mutating peer/GLM review covering this exact contract plus all previously corrected provenance, freshness, registration, refresh, runner pre-persistence, CAD-link baseline, dirty-edit and stale-selection failure classes.

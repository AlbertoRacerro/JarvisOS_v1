# 133 — FRONTEND-CONTRACT-CODEGEN-1

Status: compressed definition/full-spec/readiness packet; live implementation authority remains `docs/specs/STATUS.md`.

## Purpose

Replace one real drift-prone hand-maintained frontend API contract with a deterministic generated type derived from the existing backend contract, and make backend↔frontend drift fail visibly in CI. This is a narrow proof of the codegen boundary, not a whole-client/OpenAPI rewrite.

## Exact-master inventory

Derived from exact master `68bf5fa6408a058c65a96e7c6aea8a0d13658ee9` after 132 post-merge reconciliation.

Fresh repository evidence identifies `ParameterRead` as the first surface:

- backend authority is `backend/app/modules/modeling/models.py::ParameterRead`, inheriting `ParameterCreate` and adding `id`, `workspace_id`, `created_at`, `updated_at`, and `lifecycle_state`;
- the backend contract includes fields absent from the current frontend `Parameter` type: `value_min`, `value_max`, `source_ref`, `confidence`, `notes`, `supersedes_parameter_id`, `created_at`, and `updated_at`;
- backend `unit` is required, while `frontend/src/api/client.ts::Parameter` currently declares `unit?: string | null`;
- backend `value_status` and `lifecycle_state` are bounded literals, while the frontend currently widens them to `string | null`;
- `frontend/src/api/client.ts` manually owns this response type and uses it for `/workspaces/{workspace_id}/parameters` and related Parameter flows;
- no generated frontend contract file or exact drift checker currently owns this boundary.

This is a demonstrated contract drift, not hypothetical cleanup. Generating `ParameterRead` first is smaller and more valuable than attempting all models simultaneously.

## Failure modes to prevent

1. **Silent field omission:** backend adds or changes a Parameter response field while frontend type remains stale.
2. **Required/optional inversion:** frontend accepts `undefined` for a backend-required response field or requires a backend-optional one.
3. **Literal widening:** finite backend enums/literals degrade to unconstrained `string`, hiding incompatible values from TypeScript.
4. **Nullable drift:** `null` semantics differ between backend and generated frontend output.
5. **Generator nondeterminism:** equivalent backend contracts produce unstable ordering/formatting and noisy diffs.
6. **Generated-file hand edits:** a developer patches the generated type directly and CI fails to notice divergence.
7. **Source ambiguity:** generation uses OpenAPI/runtime routes or another derivative while the accepted Pydantic model is the actual selected authority.
8. **Over-generalization:** implementation turns into a full OpenAPI client generator, rewrites fetch/runtime behavior, or migrates every frontend type at once.
9. **Import-cycle/client regression:** moving the type breaks `client.ts` exports or consumers even though runtime JSON is unchanged.
10. **Environment-dependent output:** working directory, hash seed, platform path separators, locale, or timestamps alter generated content.

## Accepted implementation boundary

The first implementation must remain limited to the Parameter read contract:

1. add one small deterministic generator/checker, expected at `scripts/generate_frontend_contracts.py`, that imports the accepted backend `ParameterRead` model and emits a canonical TypeScript representation for that model only;
2. emit one generated frontend module, expected at `frontend/src/api/generated/modeling.ts`, containing the generated Parameter read type and an explicit generated-file header naming the source model/path; no timestamps, machine paths, random IDs, or mutable build metadata;
3. update `frontend/src/api/client.ts` to consume/re-export the generated Parameter type while preserving existing public imports for current frontend callers where practical;
4. add an exact drift check mode (`--check` or equivalent) that regenerates in memory and fails non-zero when the checked-in generated file differs byte-for-byte;
5. wire that check into existing CI for changes affecting either the selected backend model/generator/generated file/frontend client boundary, or run it unconditionally in the existing frontend/backend static path if simpler and cheap;
6. add focused deterministic generator self-tests covering field order, required/optional, nullable, literal, scalar mapping, inherited fields, unsupported-schema failure, and stale generated-file detection.

The implementation may use Pydantic's model metadata/JSON schema as an introspection mechanism, but `ParameterRead` remains the selected source authority. It must not generate from a running server, network OpenAPI endpoint, database contents, or frontend declarations.

## Canonical TypeScript mapping for V0

The generator supports only schema forms required by `ParameterRead` and fails closed on unsupported constructs rather than guessing:

- Python/Pydantic `str` -> TypeScript `string`;
- `int`/`float` -> `number`;
- `bool` -> `boolean`;
- `Literal[...]` -> sorted/preserved deterministic union of literal values;
- nullable `T | None` -> `T | null`;
- backend fields with defaults remain present in the **response** type unless the emitted JSON contract actually permits omission; defaultability in input construction must not automatically become optional response syntax;
- inherited fields are flattened into the generated read type in deterministic model-field order or an equivalently documented stable order.

If Pydantic schema semantics cannot distinguish response-requiredness safely for a field, implementation must derive it from `ParameterRead.model_fields`/equivalent exact metadata or fail closed. Do not paper over ambiguity with `?`.

## Generated contract target

The generated type must faithfully represent the current `ParameterRead` response surface, including at least:

- `name`, `symbol`, `value`, required `unit`;
- bounded `value_status`;
- `value_min`, `value_max`, `source_ref`, `confidence`, `status`, `notes`, `supersedes_parameter_id`;
- `id`, `workspace_id`, `created_at`, `updated_at`;
- bounded `lifecycle_state`.

The exact exported name may be `ParameterRead` with `client.ts` exporting a compatibility alias `Parameter`, or an equivalently narrow naming arrangement that preserves existing callers without a broad frontend migration.

## Acceptance criteria

All are required on one exact implementation head:

1. Generated Parameter response type is derived deterministically from backend `ParameterRead`; no manually duplicated field list remains authoritative for that response in `client.ts`.
2. Generated output includes all current backend response fields and matches required/nullable/literal semantics, specifically correcting the current frontend omissions and `unit`/literal widening drift.
3. Existing frontend imports/callers compile without requiring a broad unrelated migration.
4. Generator output is byte-stable across repeated runs and contains no timestamp, host path, locale, or random metadata.
5. `--check` on unchanged generated output exits zero and performs no file mutation.
6. Altering the selected backend contract without regenerating causes the drift check to fail.
7. Altering the generated file manually causes the drift check to fail.
8. Unsupported Pydantic/schema constructs fail closed with an actionable error instead of emitting `any`/`unknown` silently.
9. Focused generator tests cover inherited fields, required-vs-nullable, literals, scalar mapping and stale-file detection.
10. Frontend typecheck/build remains green; no runtime fetch URL, payload, request method, response parsing, store, schema, provider, or product behavior changes.
11. Existing backend tests and architecture/typecheck gates remain green.
12. Repository-required exact-head CI and PR Attention Evidence are terminal green before merge.

## Deterministic test plan

At minimum prove:

- two generations from identical source produce identical bytes;
- expected `ParameterRead` field set is complete;
- `unit` emits as required `string`, not optional/nullable;
- `symbol`, `value`, bounds/source/confidence/notes/replacement fields emit the exact nullable semantics;
- `value_status` and `lifecycle_state` emit finite unions rather than wide strings;
- inherited fields appear exactly once;
- a fixture/temporary source-contract delta makes check mode fail until regeneration;
- direct generated-file tampering makes check mode fail;
- unsupported schema shape produces deterministic non-zero failure;
- frontend build/typecheck passes with existing callers using the compatibility export.

## Non-goals

- no whole-client generation;
- no OpenAPI SDK generator, network schema fetch, new package manager, or external codegen dependency unless exact implementation evidence proves the tiny built-in approach impossible;
- no generation of request payloads, Workspace, Requirement, ModelSpec, Assumption, SimulationRun, Decision, AI, BLUECAD, Process, or other contracts in this slice;
- no backend Pydantic contract redesign merely to simplify generation;
- no runtime validation library introduction, runtime JSON transformation, API behavior change, store/schema/migration change, provider/credential/egress change, or UI redesign;
- no mass rename of frontend `Parameter` consumers;
- no 134 implementation.

## Files likely touched

Implementation is expected to remain bounded to:

- `scripts/generate_frontend_contracts.py` — deterministic ParameterRead generator/checker and self-test where appropriate;
- `frontend/src/api/generated/modeling.ts` — generated output;
- `frontend/src/api/client.ts` — generated type import/re-export and removal of the duplicate manual Parameter response declaration;
- `.github/workflows/ci.yml` — exact drift gate if no existing static hook is reusable;
- focused tests only where generator self-test is insufficient;
- `docs/specs/STATUS.md` for implementation lifecycle handshake.

## Readiness decision

**READY, conditional on this compressed planning/full-spec/readiness packet being accepted and the live registry subsequently recording `133=ready`.**

Rationale: 133 is additive/reversible repository/frontend tooling with no new security, credential, provider, egress, durable-store, migration, destructive, or cross-domain runtime authority. Fresh exact-master inventory proves a real mismatch between backend `ParameterRead` and the hand-maintained frontend `Parameter` response type, and the selected V0 closes only that boundary. It therefore qualifies for post-112 low-risk planning compression.

Because this planning PR intentionally does not rewrite the full live registry file, implementation remains forbidden until a subsequent exact mechanical `133: planned -> ready` registry transition merges. That transition must contain no implementation PR association or unrelated queue change.

### Test del minimo necessario

Criterio di accettazione della spec: make one demonstrated backend↔frontend response contract drift mechanically impossible to merge unnoticed, using deterministic generated code and an exact drift gate.

Questo lavoro serve a soddisfarlo? sì.

Il criterio è raggiungibile senza di esso? no — `ParameterRead` and the manually maintained frontend `Parameter` are already semantically different, and current CI has no generator/drift gate for that boundary.

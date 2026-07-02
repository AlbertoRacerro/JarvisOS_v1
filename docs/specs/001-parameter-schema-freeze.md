# 001 — Parameter/Assumption schema freeze + Requirement record

Status: implemented (pending review)
Depends on: none

## Goal

Engineering records become credible before real project data entry begins:
parameters carry units, value status, uncertainty, and provenance; assumptions carry
status and confidence; a minimal Requirement record exists so traceability can start
at requirements instead of assumptions.

## Why

Real pilot-project data entry starts immediately after this slice. Retrofitting
units/status onto populated engineering records is one of the most expensive
migrations that exists, so these fields must be frozen first. A parameter without a
unit is not reviewable engineering data. (Strategy reference:
`docs/strategy/JARVISOS_COMPUTATIONAL_ENGINEERING_WORKSPACE.md`.)

## Scope

In scope:
- Extend the `parameters` record with the new fields listed below (backend schema,
  models, service, API routes, and API payload validation).
- Extend the `assumptions` record with `status` and `confidence` if not already
  present (inspect first; align with existing patterns).
- Add a new minimal `requirements` record with CRUD API.
- Additive SQLite schema changes with safe defaults, following the existing pattern
  in `backend/app/core/schema.py`; bump the relevant schema version field.
- Tests.

Out of scope (binding non-goals):
- No frontend changes (UI ergonomics is a later slice).
- No `pint` or any unit-validation dependency — `unit` is a required free-text field
  for now; dimensional validation is a future slice.
- No changes to model specs, simulation runs, runner, AI modules, or routing.
- No data migration of existing rows beyond safe column defaults.
- No Alembic.

## New fields

`parameters` (add; keep all existing fields unchanged):

| Field | Type | Constraint |
| --- | --- | --- |
| `unit` | text | required on create; `"dimensionless"` is an allowed value |
| `value_status` | text enum | one of `candidate`, `literature`, `measured`, `validated`, `accepted`; default `candidate` |
| `value_min` | real, nullable | optional uncertainty lower bound |
| `value_max` | real, nullable | optional uncertainty upper bound |
| `source_ref` | text, nullable | free-text provenance (citation, artifact id, "user estimate") |

`assumptions` (add only if missing after inspection):

| Field | Type | Constraint |
| --- | --- | --- |
| `status` | text enum | `proposed`, `accepted`, `rejected`, `superseded`; default `proposed` |
| `confidence` | text enum, nullable | `low`, `medium`, `high` |

`requirements` (new table + CRUD, mirroring the simplest existing domain record
pattern, e.g. assumptions):

| Field | Type |
| --- | --- |
| `id`, `workspace_id`, timestamps, `schema_version` | per existing record conventions |
| `statement` | text, required |
| `rationale` | text, nullable |
| `status` | text enum: `draft`, `active`, `retired`; default `draft` |
| `notes` | text, nullable |

## Files likely touched

- `backend/app/core/schema.py` (table definitions / schema version)
- `backend/app/modules/modeling/models.py`, `service.py`, `routes.py` (parameters,
  assumptions — verify where these records actually live; some domain records may be
  under `engineering/` or `workspaces/`)
- New or existing module for `requirements` — place it next to whichever module owns
  assumptions; do not create a new top-level pattern
- `backend/tests/` (new/extended tests)

## Design constraints

- Enum validation happens at the API/service boundary (Pydantic/service checks),
  stored as text — follow whatever pattern existing enum-like fields use.
- Existing API consumers must not break: new fields optional in responses where
  needed, `unit` required only on *create* of new parameters; existing rows get a
  sentinel default (`"unspecified"`) via column default.
- `value_min`/`value_max`, when both present, must satisfy `value_min <= value_max`
  (validate at boundary).
- No renames of existing fields or endpoints.

## Acceptance criteria

1. Creating a parameter without `unit` fails with a clear validation error; with
   `unit` it succeeds and the row stores all new fields.
2. `value_status` rejects values outside the enum; defaults to `candidate`.
3. Existing parameter rows (pre-migration) still load and list correctly.
4. Requirements CRUD works end-to-end via API (create, get, list by workspace,
   update status).
5. Assumption `status`/`confidence` behave per the table above (or the spec's
   implementation notes explain that they already existed).
6. Schema version bumped; database initializes cleanly from scratch AND upgrades an
   existing database without data loss (covered by tests if an upgrade-test pattern
   exists; otherwise document manual verification in implementation notes).

## Required tests

- Parameter create/validation tests: missing unit, bad `value_status`,
  `value_min > value_max`, happy path with all fields.
- Requirement CRUD test following the existing domain-record test style
  (`backend/tests/test_domain_foundation.py` is the likely reference).
- A test that existing/minimal rows without new fields still list correctly.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status updated,
summary written.

## Implementation notes

- Implemented parameter schema-freeze fields in SQLite, Pydantic API models, service inserts, and list responses. Legacy/minimal parameter rows are covered with safe defaults (`unit="unspecified"`, `value_status="candidate"`).
- Updated assumptions to use the spec-defined text enums for `status` and `confidence`; the previous implementation had `status="draft"` and numeric confidence.
- Added minimal requirements CRUD endpoints next to the existing modeling domain records: create, get, list by workspace, and patch for status/field updates.
- Bumped the current schema migration marker to `0004_engineering_record_schema_freeze`; fresh initialization and upgrade-style additive statements both create the new shape without destructive migration.

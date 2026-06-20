# Storage And Artifact Strategy

## Purpose

JarvisOS should keep structured truth queryable while letting files grow safely. The system is local-first and Windows-first today, but future storage should not be trapped by absolute paths or SQLite blobs.

## Core Principle

```text
SQLite stores metadata, relationships, provenance, and small structured payloads.
The data-root filesystem stores bytes.
Runtime code resolves logical artifact keys into concrete paths.
```

## Proposer, Critic, Synthesizer

### Proposal v1

Store all artifact files under `C:\JarvisOS`, keep their metadata in SQLite, and use the existing `artifacts.stored_path` field as the file pointer.

### Critique v1

This works now but makes `stored_path` a fragile identity. If the data root moves, backups are restored elsewhere, or object storage is added, absolute paths become broken truth. It also does not distinguish generated plots from source PDFs, notebooks, logs, or CAD placeholders.

### Improved Proposal v2

Make artifact identity logical:

- `storage_backend`: `local_data_root` now, future `object_store` or `external_reference`.
- `storage_key`: data-root-relative key, for example `workspaces/bluerev/runs/<run_id>/timeseries.csv`.
- `filename`: display name only.
- `sha256`: content identity for managed immutable files.
- `size_bytes`: quick safety and UI metadata.
- `artifact_type`: controlled taxonomy.
- `mime_type`: content hint.
- `schema_version`: metadata version.
- `source_ref`: human-readable provenance link until normalized source tables exist.

### Critique v2

This creates a migration problem for current absolute paths and may be premature if there are only runner CSV artifacts.

### Final Synthesis

Do not migrate immediately during this documentation milestone. Before artifact viewer or file ingestion, add a migration-compatible metadata layer:

1. Keep reading current `stored_path`.
2. Add or derive relative `storage_key` for new records.
3. Preserve hash and file size for managed files.
4. Resolve absolute path only at access time through `build_paths()`.
5. Never use absolute path as durable identity again.

Residual risk: existing absolute-path records remain local-machine-specific until migrated.

## What Belongs In SQLite

Store these in SQLite:

- artifact id, workspace id, source object id;
- artifact type and role;
- storage backend and storage key;
- filename and extension;
- MIME type;
- size in bytes;
- SHA-256 for immutable managed files;
- schema version;
- status;
- creation timestamp;
- provenance fields;
- retention/deletion status;
- parser/extraction status;
- safe short notes;
- relationships to SimulationRun, ModelSpec, Decision, source document, or AIReview.

SQLite may store small structured JSON payloads when the payload is part of domain truth:

- normalized run input;
- normalized run output;
- source extraction summary;
- AI review output metadata;
- artifact manifest;
- thumbnail metadata.

## What Belongs In Filesystem Data Root

Store these as files under the JarvisOS data root:

- CSV data;
- plot images;
- PDFs;
- Markdown;
- LaTeX source;
- DOCX;
- notebook exports;
- simulation logs beyond bounded DB excerpts;
- model snapshots;
- AI review output documents;
- source documents;
- literature PDFs;
- STEP/STL placeholders;
- PFD diagrams;
- large JSON exports;
- generated report bundles.

## What Must Never Be Stored

Do not store:

- raw API keys;
- provider authorization headers;
- private keys;
- `.env` file contents;
- unrestricted raw AI prompts containing secrets;
- unreviewed AI-generated executable code as runnable implementation;
- external provider raw response bodies when they may include prompt fragments or account metadata;
- credentials inside runner environment metadata;
- absolute path as the only artifact identity.

## Artifact Type Taxonomy

Initial taxonomy:

| Type | Examples | Managed Bytes | Parser Allowed By Default |
| --- | --- | --- | --- |
| `json_result` | result JSON, structured output | yes | safe JSON only |
| `csv_timeseries` | runner time series | yes | yes |
| `plot_image` | PNG, SVG export, JPEG | yes | image metadata only |
| `pdf_document` | report or source PDF | yes | no, design gate first |
| `markdown_document` | notes, AI review outputs | yes | yes with redaction caution |
| `latex_source` | equations/report source | yes | no compile by default |
| `docx_document` | Word report | yes | no parser by default |
| `source_document` | original literature or vendor source | yes | no extraction without provenance |
| `cad_placeholder` | STEP/STL future placeholder | yes | no parser by default |
| `pfd_diagram` | process flow diagram | yes | no converter by default |
| `notebook_export` | HTML/ipynb export | yes | no execution |
| `simulation_log` | stdout/stderr full file | yes or bounded DB | text only |
| `model_snapshot` | model implementation bundle | yes | manifest only |
| `ai_review_output` | structured AI review | yes | JSON/Markdown only |
| `source_extraction_output` | extracted table/citation graph | yes | JSON only |

## Metadata Shape

Future artifact metadata should look like:

```json
{
  "id": "uuid",
  "workspace_id": "bluerev",
  "artifact_type": "csv_timeseries",
  "role": "runner_output",
  "filename": "timeseries.csv",
  "storage_backend": "local_data_root",
  "storage_key": "workspaces/bluerev/runs/<simulation_run_id>/timeseries.csv",
  "mime_type": "text/csv",
  "size_bytes": 12345,
  "sha256": "...",
  "schema_version": 1,
  "source_ref": "simulation_run:<id>",
  "status": "registered",
  "created_at": "iso-8601"
}
```

## Content Addressing And Hashes

Use SHA-256 for every managed immutable file. Hashes provide:

- duplicate detection;
- tamper detection;
- export validation;
- future object storage key support;
- runner reproducibility evidence.

Do not make content addressing the only path scheme yet. Human-friendly logical keys under workspace/run folders are more debuggable for local development.

## Relative Path Policy

Rules:

- New managed artifacts should store data-root-relative `storage_key`.
- Absolute paths may be returned as runtime convenience only when needed for local debugging.
- API responses should eventually prefer logical keys and download/open endpoints over raw absolute paths.
- External references should use `storage_backend = external_reference`, not pretend to be local managed files.

## Versioning Policy

Use two separate version dimensions:

- artifact metadata schema version;
- content version or source generation version.

For immutable generated artifacts, create a new artifact row per generation. Do not mutate file bytes behind an existing hash.

For editable documents, create new versions or snapshots before destructive edits.

## Deletion And Retention Policy

V0 recommendation:

- soft-delete metadata first with `status = deleted`;
- keep bytes until a cleanup command exists;
- never delete source documents automatically;
- allow generated runner artifacts to be purged by retention policy later;
- preserve artifacts linked to accepted Decisions unless explicitly archived.

## Export And Backup Strategy

A complete local backup should include:

- SQLite database;
- workspace artifact folders;
- manifest of schema migration id;
- manifest of artifact hashes and storage keys;
- app version;
- data-root relative paths.

Export should not include runtime-memory API keys.

## Future Object Storage Compatibility

The same metadata should support:

- local data root;
- NAS-like shared folder;
- S3-compatible object storage;
- read-only external source references.

Do not implement object storage now. The design requirement is to avoid blocking it later.

## Why Not Store Large Binary Files In SQLite Now

Do not store large binaries in SQLite because:

- local backups become harder to inspect;
- DB vacuum/locking behavior gets worse;
- large artifacts are inefficient to stream through DB queries;
- future object storage migration becomes harder;
- filesystem tools are useful for local engineering workflows.

SQLite remains excellent for metadata, relationships, small JSON payloads, and audit trails.

## Migration Plan

Before artifact viewer:

1. Add `storage_backend`, `storage_key`, `size_bytes`, and `schema_version` fields.
2. Keep `stored_path` for compatibility.
3. Write new records with both `stored_path` and `storage_key` if needed.
4. Add tests for data-root relocation resolution.
5. Add API that returns artifact metadata without requiring raw absolute paths.

Before source ingestion:

1. Add source/provenance records.
2. Add parser status fields.
3. Add extraction output artifact types.
4. Define copyright and citation policy.

Before CAD/PFD:

1. Store files as opaque artifacts.
2. Add preview/conversion design gate.
3. Do not parse or execute external converters by default.


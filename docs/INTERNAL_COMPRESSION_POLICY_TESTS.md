# Internal Compression Policy Tests

Milestone: 1D-D - Internal compression policy tests

## Executive Summary

JarvisOS may later compress internal memory summaries or compact display
snippets, but compression must never replace raw/original evidence.

Core principle:

```text
compression is never allowed to replace raw/original evidence, and compression must preserve technical truth before any compressed text can be used
```

This milestone designs the compression policy and future test matrix only. It
does not create executable tests, compression code, compression runtime,
database schema, memory runtime, retrieval runtime, provider calls, hooks, MCP,
workers, viewers, routes, frontend UI, or BlueRev modeling.

## Design Goals

- Define what JarvisOS may consider compressible later.
- Define what must never be compressed.
- Define protected technical tokens that compression must preserve.
- Define future test families before any runtime compression exists.
- Preserve raw/original evidence through MemoryStore before compression.
- Prevent compressed text from becoming canonical source or promotion authority.
- Keep compression local-first and non-authoritative.
- Adapt Caveman/Cavemem safety lessons without copying runtime code.

## Non-Goals And Hard Boundaries

This milestone does not add:

- backend code;
- frontend code;
- executable tests;
- compression implementation;
- compression runtime;
- runtime memory;
- retrieval runtime;
- database schema or migration;
- model or provider calls;
- external compression providers;
- hooks;
- MCP;
- worker processes;
- viewers;
- routes or APIs;
- tool execution;
- BlueRev modeling;
- external reference audits;
- vendored code.

This document is a design artifact. Example test cases are documentation tables,
not executable tests.

## Caveman/Cavemem-Inspired Lessons

Caveman's relevant lesson is safety discipline, not its external compression
runtime. Cavemem's relevant lesson is preserving raw observations and keeping
compact context separate from full evidence.

JarvisOS should adapt these lessons:

- token preservation;
- validation after compression;
- raw/original retention;
- sensitive input refusal;
- safe-field-only transformation;
- no external compression runtime for JarvisOS memory.

JarvisOS should not copy:

- Caveman external Claude/Anthropic compression runtime;
- Caveman CLI behavior;
- Cavemem TypeScript compression code;
- Cavemem storage/runtime code;
- hooks, MCP, worker, viewer, or embedding behavior.

## Compression Eligibility Policy

Compression eligibility is conservative.

Compressible later:

- natural-language summaries derived from accepted or proposed records;
- short display snippets;
- non-authoritative compact candidate text;
- reviewed explanatory prose with source references preserved.

Non-compressible:

- raw evidence;
- original user input;
- source files;
- code;
- config files;
- secrets;
- credentials;
- `.env` content;
- private keys;
- raw tool output;
- legal, safety, or audit-critical text;
- canonical docs;
- ADR source text;
- database rows treated as authoritative state.

Review-required:

- technical or engineering records;
- numerical assumptions;
- formulas;
- BlueRev material, geometry, process, or parameter notes;
- literature/source summaries;
- test reports;
- provenance-heavy records;
- records that may affect accepted or canonical state.

Compression must fail closed when eligibility is unknown.

## Protected Token Classes

Future compression validators must preserve:

- code fences;
- inline code;
- file paths;
- URLs;
- DOIs;
- commit hashes;
- version numbers;
- commands;
- formulas;
- numbers;
- units;
- enum values;
- source IDs;
- artifact IDs;
- table values;
- chemical identifiers;
- engineering identifiers;
- BlueRev material terms;
- BlueRev geometry terms;
- BlueRev process terms.

Protected tokens include exact spelling, punctuation, casing, ordering, and
relationships when those details affect meaning.

## Required Future Test Families

Future implementation must include tests for:

- token preservation;
- numeric/unit preservation;
- formula preservation;
- path/URL/DOI preservation;
- code/config no-compress;
- secret/path refusal;
- raw/original retention;
- no-op/empty-output rejection;
- compression cannot promote memory;
- compressed text cannot become canonical source;
- safe-field-only mutation;
- rollback/restore on validation failure.

These tests must exist before any compressed text is used by memory, retrieval,
micro-context, showcase generation, Context Pack Broker, or local model flows.

## Example Test Cases

### Token Preservation

| Case | Input risk | Required behavior |
| --- | --- | --- |
| Code fence with Python snippet | Syntax or indentation changes break meaning. | Compression preserves fence and code exactly or refuses. |
| Inline command `python -m pytest -q` | Command mutation changes action. | Command remains exact. |
| File path `backend/app/modules/local_ai/contracts.py` | Path mutation misroutes source request. | Path remains exact. |
| URL and DOI in source note | Source link corruption breaks evidence trail. | URL/DOI remain exact. |
| Commit hash `0a5cb5f84ff5a63ae0180d2af6e97408d6815ac8` | Hash truncation changes identity. | Hash remains exact unless display-only truncation is explicitly marked. |

### Numeric, Unit, And Formula Preservation

| Case | Input risk | Required behavior |
| --- | --- | --- |
| `12.5 L/min` | Number or unit mutation changes engineering meaning. | Number and unit remain exact. |
| `kLa = OUR / C*` | Formula mutation corrupts model logic. | Formula remains exact. |
| Table row with parameter values | Table value shifts or reorders. | Values preserve row association. |
| Version `v1.2.0` | Version mutation breaks traceability. | Version remains exact. |

### No-Compress And Refusal

| Case | Input risk | Required behavior |
| --- | --- | --- |
| `.env` content | Secret leakage. | Refuse compression and record policy reason later. |
| Private key block | Secret leakage. | Refuse compression. |
| Source code file | Semantic corruption. | Refuse compression by default. |
| Raw evidence body | Loss of original evidence. | Refuse replacement; raw/original reference remains. |

### Authority And Rollback

| Case | Input risk | Required behavior |
| --- | --- | --- |
| Empty compression output | Data loss. | Reject and keep original. |
| Output changes source ID | Evidence link corruption. | Reject and keep original. |
| Compression succeeds on proposed memory | Authority confusion. | Mark compressed body non-authoritative. |
| Validator failure after partial work | Corrupt staged record. | Roll back or leave original record unchanged. |

## Future Acceptance Criteria Before Implementation

Before runtime compression is allowed:

- raw/original reference is preserved;
- validator catches protected token mutation;
- sensitive paths are refused;
- secret-like inputs are refused or gated;
- compression output is bounded;
- audit event is required;
- compressed body is marked non-authoritative;
- no compressed text can promote memory;
- no compressed text can become canonical source;
- rollback/restore behavior is tested;
- compression cannot bypass MemoryStore;
- external compression providers remain unapproved for memory.

## Relationship To MemoryStore

MemoryStore must retain raw/original evidence before compression.

Compression policy may later run inside or behind MemoryStore. It must never
bypass MemoryStore. MemoryStore remains responsible for source links,
provenance, staged transitions, raw/original retention references, hard policy
overrides, and audit records.

Compression cannot:

- create durable memory directly;
- promote memory;
- change final sensitivity;
- overwrite raw evidence;
- write canonical state;
- bypass review requirements;
- bypass source/provenance checks.

## Relationship To Retrieval

Compressed snippets may support compact candidate display later.

Full evidence retrieval by ID remains required for decisions. Compressed text
may help orientation, ranking, display, or compact context, but it must not
replace full source evidence when deciding memory promotion, safety, BlueRev
assumptions, provider use, or tool execution.

Retrieval runtime remains deferred.

Future SQLite/FTS schema concepts are documented in
`docs/SQLITE_FTS_MEMORY_SCHEMA_DESIGN.md`; FTS must index compact snippets only,
not raw/original evidence.

## Failure Modes

Mutated numbers or units:

- Compression changes quantitative meaning.
- Required response: validator rejects output.

Changed formulas:

- Compression rewrites equations or symbolic relationships.
- Required response: validator rejects output.

Lost source IDs:

- Compression removes evidence traceability.
- Required response: output is rejected and original evidence remains.

Compressed text treated as truth:

- Compact prose is mistaken for canonical state.
- Required response: compressed body is marked non-authoritative.

Sensitive input sent to external provider:

- Memory content leaks outside local-first boundaries.
- Required response: external compression providers are not approved.

Raw evidence deleted:

- Original evidence is lost after compaction.
- Required response: compression cannot proceed without raw/original retention.

Over-compression of engineering assumptions:

- A tentative assumption appears accepted or simplified past review value.
- Required response: review-required technical records are refused or gated.

## Milestone Boundary Confirmation

1D-D is a docs-only design milestone.

It does not add:

- backend code;
- frontend code;
- executable tests;
- compression implementation;
- compression runtime;
- runtime memory;
- retrieval runtime;
- database schema or migration;
- local or external model calls;
- hooks;
- MCP;
- worker processes;
- viewers;
- provider routing;
- tool execution;
- BlueRev modeling;
- external reference audits;
- vendored code.

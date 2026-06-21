# Cavemem/Caveman Reference Audit

Milestone: 1C-Z-T - Cavemem/Caveman reference clone and implementation-pattern audit

Inspection date: 2026-06-21

## Executive Summary

This milestone inspected Cavemem and Caveman as external reference
implementations for future JarvisOS memory, compression, retrieval, hook, MCP,
and worker design. The repositories were cloned outside the JarvisOS repository
and were not vendored.

The strongest reusable Cavemem idea is the architectural split between raw
storage and a single `MemoryStore` facade that owns the write boundary. Hooks,
worker processes, MCP tools, viewer routes, compression, embeddings, and FTS all
attach around that boundary rather than letting model output write directly to
durable memory. Cavemem also demonstrates a useful progressive disclosure
shape: compact search/timeline results first, then full observation retrieval by
ID.

The JarvisOS-specific future facade contract is documented in
`docs/MEMORYSTORE_FACADE_DESIGN.md`.

The strongest reusable Caveman idea is the compression safety pattern:
technical-token preservation, validation after compression, out-of-tree original
retention, sensitive path refusal, and "safe fields only" transformation. The
current Caveman compression path uses external Claude/Anthropic execution, so
JarvisOS should not copy that runtime. It should adapt the safety philosophy
with Python-native internal tests later.

JarvisOS internal compression policy test design is documented in
`docs/INTERNAL_COMPRESSION_POLICY_TESTS.md`.

This audit adds no JarvisOS runtime memory, SQLite runtime, retrieval runtime,
MCP server, frontend UI, routes, hooks, worker, viewer, local model authority,
provider integration, or compression implementation. It records patterns to
adapt before the 1D design sequence.

## Reference Repositories Inspected

| Repo | URL | Branch | Commit hash | License | Local path outside JarvisOS | Inspection date |
| --- | --- | --- | --- | --- | --- | --- |
| Cavemem | `https://github.com/JuliusBrussee/cavemem.git` | `main` | `1fe41e9c9f28380d3da9640f02812f8e5565839a` | MIT, copyright 2026 Julius Brussee | `C:\Users\thera\Documents\JarvisOS_external_refs\cavemem` | 2026-06-21 |
| Caveman | `https://github.com/JuliusBrussee/caveman.git` | `main` | `25d22f864ad68cc447a4cb93aefde918aa4aec9f` | MIT, copyright 2026 Julius Brussee | `C:\Users\thera\Documents\JarvisOS_external_refs\caveman` | 2026-06-21 |

License note: both repositories reported MIT license at the inspected commits.
No source code from either repository was copied into JarvisOS during this
milestone. Any future source copying would require preserving license and
copyright notices and should be approved explicitly.

## Cavemem File Tree Overview

Relevant top-level Cavemem structure:

```text
cavemem/
  README.md
  CLAUDE.md
  LICENSE
  package.json
  pnpm-workspace.yaml
  docs/
    architecture.md
    compression.md
    development.md
    mcp.md
  examples/
    settings.example.json
  hooks-scripts/
  packages/
    compress/
    config/
    core/
    embedding/
    hooks/
    installers/
    storage/
  apps/
    cli/
    mcp-server/
    worker/
  evals/
```

Most relevant Cavemem directories for JarvisOS are:

- `packages/core`: facade and ranking logic.
- `packages/storage`: SQLite, FTS, embedding persistence, timeline queries.
- `packages/compress`: compact-at-rest text handling and private tag stripping.
- `packages/config`: settings schema, defaults, loader, docs.
- `packages/hooks`: session and prompt/tool hooks that write through the facade.
- `apps/mcp-server`: compact retrieval tools and full retrieval by ID.
- `apps/worker`: loopback worker/viewer and embedding loop.
- `packages/embedding`: local, Ollama, OpenAI embedding provider abstractions.

## Caveman File Tree Overview

Relevant top-level Caveman structure:

```text
caveman/
  README.md
  CLAUDE.md
  AGENTS.md
  GEMINI.md
  LICENSE
  INSTALL.md
  install.ps1
  install.sh
  package.json
  bin/
  commands/
  agents/
  plugins/
  skills/
    caveman/
    caveman-compress/
  src/
    hooks/
    mcp-servers/
    plugins/
    rules/
    tools/
  tests/
```

Most relevant Caveman directories for JarvisOS are:

- `skills/caveman-compress`: Python compression flow, validators, security
  notes, backup policy, and command-line wrapper.
- `src/mcp-servers/caveman-shrink`: safe-field MCP metadata compression proxy.
- `src/hooks`: activation/mode hooks with symlink-safe flag handling.
- `bin`: installer and provider/hook configuration behavior.
- `tests`: compression, validation, MCP shrink, symlink, config, and installer
  safety tests.

## Cavemem Relevant Module Map

| Area | Reference paths | Role | JarvisOS relevance |
| --- | --- | --- | --- |
| Config | `packages/config/src/schema.ts`, `defaults.ts`, `loader.ts` | Typed settings for data dir, compression, embeddings, search, privacy, IDES. | Future memory policy config, but not runtime yet. |
| Compression | `packages/compress/src/compress.ts`, `expand.ts`, `tokenize.ts`, `privacy.ts` | Compact text while preserving protected segments and stripping private tags. | Future internal compression policy tests and token preservation rules. |
| Raw storage | `packages/storage/src/schema.ts`, `storage.ts`, `types.ts` | SQLite schema, observations, summaries, FTS, embeddings. | Future SQLite/FTS design input. No JarvisOS storage added now. |
| Facade | `packages/core/src/memory-store.ts` | Central write/read facade that applies redaction and compression before storage. | Strong candidate pattern for future `MemoryStore` write boundary. |
| Ranking | `packages/core/src/ranker.ts` | Hybrid FTS/vector ranking and cosine similarity. | Future compact memory retrieval candidate ranking. |
| Hooks | `packages/hooks/src/runner.ts`, `handlers/*` | Captures session starts, user prompts, tool uses, and session ends. | Future event/write-boundary capture inspiration, not copied now. |
| MCP server | `apps/mcp-server/src/server.ts` | Search, timeline, get observations by ID, list sessions. | Future Context Pack Broker/retrieval interface shape, not runtime now. |
| Worker/viewer | `apps/worker/src/server.ts`, `viewer.ts`, `embed-loop.ts` | Loopback viewer, API, worker state, embedding loop. | Future lazy enrichment/indexing worker idea, deferred. |
| Embeddings | `packages/embedding/src/*` | Local, Ollama, OpenAI, none providers. | Do not copy provider abstractions yet. JarvisOS provider boundaries differ. |
| Tests | `packages/*/test/*`, `apps/*/test/*` | Progressive retrieval, token preservation, redaction, hook perf, FTS scope. | Port concepts later as Python tests. |

## Caveman Relevant Module Map

| Area | Reference paths | Role | JarvisOS relevance |
| --- | --- | --- | --- |
| Compression skill | `skills/caveman-compress/SKILL.md`, `README.md`, `SECURITY.md` | Defines external-model compression workflow and safety requirements. | Copy safety philosophy only, not external compression runtime. |
| Python compressor | `skills/caveman-compress/scripts/compress.py` | Detects sensitive files, calls Claude/Anthropic, validates, retries, backs up originals. | Rewrite later in Python for local/internal policy, without external calls. |
| Type detection | `skills/caveman-compress/scripts/detect.py` | Natural language vs code/config/file type heuristics. | Useful for deciding what should never be compressed. |
| Validation | `skills/caveman-compress/scripts/validate.py` | Verifies headings, code blocks, URLs, paths, bullets, inline code. | Port conceptual validators; extend for numbers, formulas, units, source IDs. |
| CLI wrapper | `skills/caveman-compress/scripts/cli.py` | User-facing command, exit codes, UTF-8 handling. | Later admin/manual tool shape only, not runtime now. |
| MCP shrink proxy | `src/mcp-servers/caveman-shrink/index.js`, `compress.js` | Compresses MCP description fields only; preserves request/response bodies. | Good "safe fields only" principle; defer MCP runtime. |
| Hooks/config | `src/hooks/caveman-config.js`, `caveman-activate.js`, `caveman-mode-tracker.js` | Symlink-safe flag files, mode activation, natural language toggles. | Security ideas for future hooks; reject direct hook behavior now. |
| Installer | `bin/install.js`, `install.ps1`, `install.sh` | Cross-provider install and pinned refs. | Defer. JarvisOS should keep explicit reviewed setup paths. |
| Tests | `tests/test_compress_safety.py`, `test_validate_inline.py`, `test_mcp_shrink.js`, `test_symlink_flag.js`, `test_repo_local_config.js`, `test_hooks.py` | Regression tests for no-op safety, backups, token preservation, symlink safety. | Port concepts into JarvisOS tests later. |

## Detailed File, Function, And Class Audit

| Reference repo | Reference path | Symbol / file section | What it does | Why it matters for JarvisOS | JarvisOS equivalent / future target | Adaptation decision | Dependencies introduced if copied | Security/privacy concerns | Tests to port conceptually | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cavemem | `packages/core/src/memory-store.ts` | `MemoryStore` | Provides the main facade over settings, storage, compression, redaction, sessions, timeline, and search. | Establishes a single application-level memory boundary instead of letting callers write raw records directly. | Future Python `MemoryStore` facade. | Rewrite in Python. | TypeScript runtime, `better-sqlite3`, package graph if copied. | Facade must enforce secret rules, source links, policy, and audit. | Add-observation path, add-summary path, search fallback, get-by-ID expansion. | Best architectural pattern from Cavemem. |
| Cavemem | `packages/core/src/memory-store.ts` | `addObservation` | Redacts private segments, ensures session, compresses body, writes storage record. | Shows write-time boundary ordering. | Future raw/proposed memory intake write path. | Copy idea. | Same as above if copied. | JarvisOS needs stronger deterministic secret/IP scans than private tags. | Redaction before write, compressed body persisted, raw retention policy. | Do not let model output call this directly. |
| Cavemem | `packages/core/src/memory-store.ts` | `addSummary` | Writes compressed session summaries through the same facade. | Summaries should share retention and redaction rules. | Future enrichment summary records. | Copy idea. | Same as above if copied. | Summaries can leak original sensitive content if not validated. | Summary write tests with redaction and provenance. | Useful after MemoryStore exists. |
| Cavemem | `packages/core/src/memory-store.ts` | `getObservations` | Retrieves observations by ID and optionally expands compressed body. | Supports compact-first retrieval followed by full-body fetch. | Future full memory body retrieval by ID. | Rewrite in Python. | None if rewritten. | ID access must be permission checked and audited. | Full retrieval by ID, expanded vs compressed behavior. | Maps directly to Context Pack future. |
| Cavemem | `packages/core/src/memory-store.ts` | `timeline` | Returns compact ordered observation metadata. | Prevents flooding context with full memory bodies. | Future compact memory timeline/candidates. | Copy idea. | None if rewritten. | Timeline scope should respect workspace/project boundaries. | Compact shape tests. | Good progressive disclosure primitive. |
| Cavemem | `packages/core/src/memory-store.ts` | `search` | Runs FTS and optional embedding ranking, falling back when no embedder exists. | Demonstrates graceful retrieval degradation. | Future compact memory candidate retrieval. | Rewrite later. | Embedding providers if copied. | Embedding external provider must not be implicit. | FTS fallback, provider none fallback, stale embedding handling. | Defer vector search until policy exists. |
| Cavemem | `packages/core/src/ranker.ts` | `hybridRank`, `cosine` | Combines FTS and vector similarity. | Useful ranking shape for later retrieval. | Future retrieval scoring module. | Defer. | None if rewritten. | Ranking can overexpose sensitive records without policy filters. | Deterministic ranking tests. | Implement after schema/security design. |
| Cavemem | `packages/storage/src/schema.ts` | `SCHEMA_SQL` | Defines sessions, observations, summaries, FTS, embeddings, triggers, schema version. | Good concrete schema input for SQLite/FTS design. | Future memory DB migration. | Copy idea. | `better-sqlite3` if copied directly. | Needs migrations, workspace scoping, retention, encryption decision. | Schema creation, FTS triggers, foreign keys. | Do not copy SQL wholesale without JarvisOS schema review. |
| Cavemem | `packages/storage/src/storage.ts` | `Storage` | Opens SQLite, applies pragmas, creates schema, exposes storage operations. | Shows a thin storage layer beneath the facade. | Future repository/DAO under `MemoryStore`. | Rewrite in Python. | `better-sqlite3` if copied. | Low-level methods should not be public write authority. | Storage CRUD, scoping, missing IDs. | JarvisOS uses Python backend, not Node. |
| Cavemem | `packages/storage/src/storage.ts` | `insertObservation` | Inserts a compressed observation row. | Shows low-level write that facade should protect. | Future private storage method. | Rewrite in Python. | None if rewritten. | If exposed, bypasses redaction/compression policy. | Direct storage unit tests plus facade tests. | Keep below service boundary. |
| Cavemem | `packages/storage/src/storage.ts` | `searchFts` | Sanitizes FTS query, supports optional `cwd` scope, returns negative `bm25` score. | Shows compact scoped keyword search. | Future memory FTS retrieval. | Copy idea. | SQLite FTS5. | Query sanitization and workspace scope required. | FTS, query sanitation, scope filter tests. | JarvisOS should scope by workspace/project/source. |
| Cavemem | `packages/storage/src/storage.ts` | embedding methods | Stores vectors, reads missing embeddings, drops stale model embeddings. | Shows lazy indexing and model-version invalidation. | Future enrichment/indexing worker storage. | Defer. | Vector provider/runtime. | Embeddings can leak sensitive content to external providers. | Missing/stale embedding tests. | Keep external embeddings disabled by default if ever added. |
| Cavemem | `packages/compress/src/compress.ts` | `compress` | Tokenizes text and compresses prose while preserving protected technical segments. | Supports compact-at-rest memory without destroying technical tokens. | Future internal compression policy. | Rewrite in Python. | TypeScript package if copied. | Lossy compression can corrupt engineering truth. | Code fence, URL, path, version, date preservation. | Compression must be optional and reversible to raw/original body. |
| Cavemem | `packages/compress/src/expand.ts` | `expand` | Expands abbreviations in compact text; does not restore omitted filler. | Clarifies that expansion is convenience, not exact restore. | Future display/context expansion policy. | Copy idea. | None if rewritten. | Expanded text may appear more authoritative than compressed source. | Expanded vs compressed shape tests. | JarvisOS must preserve raw/original separately. |
| Cavemem | `packages/compress/src/tokenize.ts` | `tokenize` | Classifies fences, inline code, URLs, paths, commands, versions, dates, numbers, identifiers, headings, prose, newline. | Provides a strong technical-token preservation inventory. | Future Python tokenizer tests. | Rewrite in Python. | None if rewritten. | Tokenizer bugs can mutate critical values. | Token class preservation tests. | Good exact test matrix source. |
| Cavemem | `packages/compress/src/privacy.ts` | `redactPrivate` | Removes balanced `<private>...</private>` and unclosed private content to EOF. | Shows simple explicit private segment redaction. | Future redaction policy input. | Modify/reject as sufficient policy. | None. | Private tags alone are insufficient for secrets/IP. | Private segment tests plus deterministic secret tests. | Useful as one rule, not the whole policy. |
| Cavemem | `packages/config/src/schema.ts` | `SettingsSchema` | Zod settings for data dir, compression, embedding providers, search, privacy, IDEs. | Shows policy knobs and defaults. | Future memory/retrieval/compression config. | Rewrite in Python. | Zod/Node if copied. | Config can accidentally enable external embeddings/providers. | Default-none provider tests, settings validation. | JarvisOS should keep external providers explicitly gated. |
| Cavemem | `packages/hooks/src/runner.ts` | `runHook` | Loads settings, creates MemoryStore, dispatches hook handlers, returns safe hook result. | Demonstrates hook path writing only through facade. | Future event/write-boundary capture. | Defer. | Node hook runtime. | Hooks can capture sensitive tool/user data. | Hook error handling, hot path timing. | No hooks in this milestone. |
| Cavemem | `packages/hooks/src/handlers/session-start.ts` | session start handler | Starts/resumes session and returns same-cwd summaries only for startup context. | Shows scoped context injection and avoiding noisy context. | Future micro-context starter. | Copy idea. | Node hook runtime. | CWD alone is not enough for JarvisOS workspace authority. | Same-scope summary tests. | Defer until context policy exists. |
| Cavemem | `packages/hooks/src/handlers/user-prompt-submit.ts` | user prompt handler | Stores prompt observation and returns no retrieval context. | Separates capture from retrieval. | Future raw intake event capture. | Copy idea. | Node hook runtime. | Raw prompt capture has retention and consent implications. | Prompt write, no context injection. | Needs explicit JarvisOS policy. |
| Cavemem | `packages/hooks/src/handlers/post-tool-use.ts` | post tool handler | Stores truncated tool output with metadata. | Shows tool result as memory evidence. | Future event capture after tool boundaries. | Modify heavily. | Node hook runtime. | Tool output may contain secrets or file contents. | Truncation, metadata, redaction tests. | Must require allowlists and secret scanning. |
| Cavemem | `packages/hooks/src/auto-spawn.ts` | worker auto-spawn | Fire-and-forget worker startup with hot path limits. | Shows lazy worker model. | Future lazy enrichment/indexing worker. | Defer. | Detached Node process. | Background services need lifecycle/security review. | Hot-path perf and disabled-mode tests. | No worker now. |
| Cavemem | `apps/mcp-server/src/server.ts` | `buildServer` | Exposes MCP tools: search, timeline, get observations, list sessions. | Demonstrates compact retrieval tool surface. | Future retrieval/Context Pack interface. | Defer. | MCP server runtime. | MCP can expose memory if scope/auth is weak. | Tool list, compact search, full retrieval, invalid input. | No MCP server now. |
| Cavemem | `apps/mcp-server/src/server.ts` | `get_observations` | Retrieves full bodies by IDs, max 50, expanded by default. | Useful full-context second step after compact search. | Future full memory body retrieval by ID. | Copy idea. | MCP runtime if copied. | ID enumeration and over-fetch risks. | ID count limit, missing ID, expand flag. | Good for progressive disclosure design. |
| Cavemem | `apps/worker/src/server.ts` | `buildApp` | Loopback Hono API for state, sessions, observations, search, HTML pages. | Shows viewer/API separation around memory store. | Future local admin viewer, not product UI. | Defer. | Hono/Node server. | Viewer can leak sensitive memory locally. | Viewer escaping, loopback binding, state routes. | No viewer now. |
| Cavemem | `apps/worker/src/embed-loop.ts` | `startEmbedLoop` | Lazily indexes observations, expands content before embedding, writes state snapshots, idles out. | Good lazy enrichment/indexing shape. | Future enrichment/indexing worker. | Defer. | Embedding runtime/provider packages. | Embedding expansion may leak compressed sensitive text. | Stale model, missing embedding, idle shutdown. | External providers remain gated. |
| Cavemem | `packages/embedding/src/index.ts` | `createEmbedder` | Selects local, Ollama, OpenAI, or none embedding provider. | Shows adapter split but also provider creep risk. | Future retrieval provider interface only after policy. | Reject for now. | Local transformers, Ollama/OpenAI fetch. | External embedding providers violate local-first assumptions unless gated. | Provider none and wrong-dim tests. | Do not introduce provider routing here. |
| Caveman | `skills/caveman-compress/scripts/compress.py` | `compress_file` | Resolves path, refuses sensitive files, size-caps, detects type, calls model, validates, backs up, retries, restores on failure. | Good compression safety transaction model. | Future internal compression policy tests. | Rewrite in Python later. | Anthropic SDK or Claude CLI if copied. | External model call can leak document contents. | No-op safety, backup verification, restore on failure. | Do not copy runtime call path. |
| Caveman | `skills/caveman-compress/scripts/compress.py` | sensitive path checks | Denies secret-like basenames and path components. | Shows deterministic preflight before compression. | Future JarvisOS compression/read policy. | Copy idea. | None. | Needs broader JarvisOS secret/IP rules and allowed roots. | Sensitive path refusal tests. | Useful immediate policy concept. |
| Caveman | `skills/caveman-compress/scripts/compress.py` | `backup_dir_for` | Stores originals under OS app data, outside source folders. | Avoids adjacent `.original` files being reingested. | Future raw/original memory body retention policy. | Copy idea. | None. | Backup location needs encryption/retention/cleanup decisions. | Out-of-tree backup and verified backup tests. | JarvisOS likely stores raw body in DB/object store, not sidecar files. |
| Caveman | `skills/caveman-compress/scripts/compress.py` | `call_claude` | Uses Anthropic SDK or `claude --print` subprocess. | Shows current runtime is external model based. | No JarvisOS equivalent. | Reject runtime. | Anthropic SDK, Claude CLI, subprocess. | External provider leakage and subprocess risk. | Mock model call tests only if concept used. | Do not use for JarvisOS internal memory. |
| Caveman | `skills/caveman-compress/scripts/detect.py` | `detect_file_type`, `should_compress` | Classifies file type and whether it is natural language enough to compress. | Useful guard against compressing code/config/secrets. | Future compression eligibility policy. | Rewrite in Python. | None. | Misclassification could corrupt source artifacts. | Code/config rejection tests. | Extend with JarvisOS artifact types. |
| Caveman | `skills/caveman-compress/scripts/validate.py` | `validate` and validators | Checks headings, code blocks, URLs, paths, bullets, inline code. | Demonstrates post-compression preservation tests. | Future compression validation module. | Rewrite and extend. | None. | Current validator does not fully prove semantic fidelity. | Heading/code/URL/path/inline preservation tests. | Add numbers, formulas, units, source IDs, enums. |
| Caveman | `skills/caveman-compress/scripts/cli.py` | CLI wrapper | Handles command-line execution, stdout/stderr encoding, and exit codes. | Useful for future admin-only manual tooling. | Optional future admin command. | Defer. | None if rewritten. | Manual tools can mutate files unexpectedly. | Exit code and dry-run tests. | No CLI now. |
| Caveman | `skills/caveman-compress/SECURITY.md` | Security notes | Documents subprocess/file I/O risks, fixed argv, size limit, external model paths. | Helpful risk framing. | Future compression threat model. | Copy idea. | None. | Must be adapted to local-first JarvisOS threat model. | Threat-model checklist tests. | Useful audit source. |
| Caveman | `src/mcp-servers/caveman-shrink/compress.js` | protected segment compression | Protects fences, inline code, URLs, paths, constants, functions, versions. | Strong token-preservation inventory. | Future Python tokenizer tests. | Rewrite in Python. | Node if copied. | Pattern gaps can mutate technical content. | Protected segment preservation tests. | Combine with Cavemem tokenizer ideas. |
| Caveman | `src/mcp-servers/caveman-shrink/index.js` | `transformResponse` | Compresses tool/prompt/resource description fields only; passes request bodies and tool-call results through. | Excellent safe-field mutation principle. | Future metadata-only compression rules. | Copy idea. | MCP proxy runtime if copied. | Even metadata transformation can confuse model/tool contracts. | Description-only mutation tests. | Defer MCP entirely. |
| Caveman | `src/hooks/caveman-config.js` | `safeWriteFlag`, `readFlag`, config lookup | Uses safer file handling and symlink checks for mode flags/config. | Useful for future local config/hook security. | Future hook/config safety utilities. | Copy idea only. | Node if copied. | Symlink and config injection risks. | Symlink refusal, malformed config fallback. | No hooks now. |
| Caveman | `src/hooks/caveman-mode-tracker.js` | UserPromptSubmit mode tracker | Natural-language activation/deactivation and reinforcement. | Shows how hooks can influence local behavior. | No current JarvisOS target. | Reject for JarvisOS now. | Hook runtime. | User prompt hooks can become hidden behavior. | Hook activation tests if ever implemented. | Not appropriate before explicit JarvisOS UX. |
| Caveman | `bin/install.js` | installer/provider matrix | Installs skills/hooks/plugins across providers with pinned refs. | Shows cross-host installation complexity. | No current target. | Defer. | Node installer, host-specific hooks. | Installer can mutate user config. | Upgrade/uninstall/provider tests. | JarvisOS should keep reviewed setup scripts. |
| Caveman | `tests/test_compress_safety.py` | compression safety tests | Verifies empty/no-op output does not touch disk, backups are verified, backups are out-of-tree. | Critical concepts for any future compression implementation. | Future Python compression tests. | Port conceptually. | None. | Protects against data loss. | Port directly as behavior, not code. | High-value test set. |
| Caveman | `tests/test_validate_inline.py` | inline code validation tests | Confirms inline code preservation checks. | Technical-token integrity matters for engineering memory. | Future compression validator tests. | Port conceptually. | None. | Inline code/path mutation can break commands. | Inline code preservation. | Combine with Cavemem compression tests. |
| Caveman | `tests/test_mcp_shrink.js` | MCP shrink tests | Confirms description compression and protected token behavior. | Useful safe-field-only regression concept. | Future metadata compression tests. | Port conceptually later. | Node/MCP if copied. | MCP descriptions can affect tool use. | Safe fields only, pass-through request/result. | Defer until MCP design. |
| Caveman | `tests/test_symlink_flag.js` | symlink-safe flags | Verifies symlink refusal and permissions. | Good local filesystem security baseline. | Future hook/config file tests. | Port conceptually. | None. | Prevents config/flag injection. | Symlink and mode tests. | Useful for Windows/local-first safety too. |

## JarvisOS Adaptation Blueprint Mapping

| Reference pattern | JarvisOS adaptation target | Decision |
| --- | --- | --- |
| Cavemem observation | JarvisOS raw/proposed memory record with source ID, timestamp, provenance, raw/original body reference, broad intake signals, and enrichment status. | Rewrite in Python later. |
| Cavemem compressed body | JarvisOS internal compressed memory body generated only after raw/original text is retained and validation passes. | Defer until compression policy tests. |
| Cavemem `MemoryStore` | JarvisOS future `MemoryStore` facade enforcing write boundary, redaction, compression policy, source links, audit, and promotion rules. | Copy architecture idea, rewrite in Python. |
| Cavemem search/timeline | JarvisOS compact memory candidate retrieval with scoped metadata only. | Design later in 1D-F / 2E path. |
| Cavemem `get_observations(ids)` | JarvisOS full memory body retrieval by ID after compact candidate selection and permission checks. | Copy progressive disclosure idea. |
| Cavemem hooks | JarvisOS future event/write-boundary capture after explicit hook/security design. | Defer. |
| Cavemem worker | JarvisOS future lazy enrichment/indexing worker for FTS, summaries, compression, and embeddings only after policy gates. | Defer. |
| Cavemem settings | JarvisOS memory/retrieval/compression policy config with safe defaults and no implicit external providers. | Rewrite in Python later. |
| Caveman compressor | JarvisOS internal memory compression policy that preserves technical tokens and validates output. | Rewrite in Python later; reject external model runtime. |
| Caveman original backup | JarvisOS raw-body/original-text retention policy, likely DB/object-store based rather than sidecar files. | Copy idea, adapt storage. |

## Copy, Adapt, Defer, Reject List

### Copy As Philosophy

- Single facade owns memory write boundary.
- Compact-first retrieval, full-body-by-ID second.
- Raw/original text must survive compression.
- Compression must preserve code fences, inline code, URLs, paths, commands,
  versions, dates, numbers, identifiers, headings, and source IDs.
- Compression output must be validated before replacing or using compact text.
- Background indexing/enrichment should be lazy and non-authoritative.
- Hooks should capture events only through policy-controlled boundaries.
- Safe-field-only mutation is preferable to arbitrary payload mutation.
- Reports and retrieval should avoid raw sensitive text unless explicitly needed.

### Rewrite In Python Later

- `MemoryStore` facade and repository/storage layer.
- SQLite/FTS schema and migrations for staged memory records.
- Token-preserving compression tokenizer and validator.
- Redaction/private segment handling plus JarvisOS deterministic secret/IP rules.
- Scoped compact search and timeline APIs.
- Full memory body retrieval by ID.
- Compression eligibility/type-detection rules.
- Lazy enrichment/indexing worker.
- Settings schema for memory, retrieval, compression, retention, and review gates.
- Tests for progressive disclosure, token preservation, secret refusal, and raw
  body retention.

### Defer

- Runtime memory service.
- SQLite/FTS memory runtime.
- Retrieval runtime.
- Context Pack Broker runtime.
- MCP server.
- Worker process.
- Local viewer.
- Hooks.
- Embeddings.
- External embedding providers.
- Compression implementation.
- Any model-driven memory promotion.

### Reject Or Modify

- Reject copying Caveman external Claude/Anthropic compression runtime into
  JarvisOS memory.
- Reject direct vendoring of Cavemem TypeScript runtime into the Python backend.
- Reject private-tag redaction as sufficient privacy policy.
- Reject CWD-only scoping as sufficient JarvisOS memory authority.
- Reject automatic tool-output capture without allowlists, truncation, secret
  scanning, and explicit policy.
- Reject external embedding providers as default memory infrastructure.
- Modify Cavemem storage concepts to include JarvisOS migrations, workspace
  scoping, audit, retention, raw body references, and policy gates.
- Modify Caveman validation to cover numbers, units, formulas, identifiers,
  source IDs, enum values, and domain-specific engineering fields.

## Security Gap Analysis

| Area | Observed reference behavior | JarvisOS risk | Required JarvisOS control before implementation |
| --- | --- | --- | --- |
| Private content | Cavemem strips explicit `<private>` segments. | Secrets and proprietary IP may not be tagged. | Deterministic secret/IP scanning, sensitivity buckets, path deny/allow rules. |
| Tool output capture | Cavemem stores truncated tool outputs. | Tool output may include secrets or raw files. | Tool allowlists, redaction, source classification, storage limits, review gates. |
| Compression | Caveman can call Claude/Anthropic or Claude CLI. | External model leakage and subprocess risks. | Local-only/internal compression or explicit external-provider gate, plus tests. |
| Raw/original retention | Caveman stores out-of-tree backups; Cavemem stores compressed observations. | Losing original text corrupts later enrichment and audit. | Raw/original body retention policy, retention limits, encryption decision. |
| SQLite schema | Cavemem creates schema directly with schema version row. | JarvisOS needs migration and compatibility story. | Migration design, versioned schemas, rollback/backup strategy. |
| Retrieval | Cavemem exposes compact and full retrieval via MCP. | Unauthorized over-fetch or ID enumeration. | Workspace/project scope, permission checks, query limits, audit. |
| Embeddings | Cavemem supports local/Ollama/OpenAI. | External embedding calls can leak memory content. | Provider disabled by default, explicit policy, redaction, audit, local-first default. |
| Hooks | Both repos use hooks for capture/activation. | Hidden behavior and unintended capture. | Explicit hook design, user-visible policy, opt-in, tests, safe filesystem handling. |
| Viewer | Cavemem has loopback viewer/API. | Local viewer can expose memory contents. | Auth or local trust model, loopback binding, escaping, retention filters. |
| Config files | Caveman tests symlink-safe flags/config. | Config injection or symlink attacks. | Symlink refusal, size caps, permission checks, Windows-specific tests. |
| Model authority | Reference tools can transform/capture content. | Model output may be mistaken for authority. | JarvisOS policy remains final; models propose only. |

## Recommended Next JarvisOS Implementation Sequence

1. `1D-A Local-model-facing showcase files design`
2. `1D-B Micro-context design`
3. `1D-C MemoryStore facade design`
4. `1D-D Internal compression policy tests`
5. `1D-E SQLite/FTS schema design`
6. `1D-F Progressive retrieval contract design`
7. `1D-G Holdout intake generalization set`

This sequence keeps JarvisOS design-first. It does not add runtime memory,
retrieval, compression, MCP, hooks, or viewer behavior until the boundaries are
specified and tested.

## Detailed Findings Summary

### Write Boundary

Cavemem's most important implementation pattern is that capture paths do not
write arbitrary memory records directly. They pass through `MemoryStore`, which
applies redaction, session handling, compression, and storage. JarvisOS should
adapt this as a Python facade that owns all future memory writes and prevents
model output, routes, worker jobs, hooks, or provider adapters from bypassing
policy.

### Compression

Cavemem compresses prose around protected technical segments. Caveman uses a
model-assisted compression transaction with detection, validation, retries, and
original backup. JarvisOS should combine these philosophies later: local
token-preserving compression, validation-first acceptance, and raw/original
retention. This milestone does not implement compression.

### Token Preservation

Both references treat technical tokens as high-risk content. Paths, URLs,
versions, code fences, inline code, commands, identifiers, headings, and numbers
must not be casually rewritten. JarvisOS should create Python tests around these
token classes before compressing memory text.

### Storage

Cavemem's SQLite/FTS schema is useful but should not be copied as-is. JarvisOS
needs workspace/project scoping, migration design, audit fields, raw body
retention, source IDs, staged memory status, and policy fields aligned with
`FastIntakeSignalForm` and future memory cards.

JarvisOS future SQLite/FTS schema design is documented in
`docs/SQLITE_FTS_MEMORY_SCHEMA_DESIGN.md`.

### Retrieval

Cavemem's retrieval surface is a good progressive disclosure pattern:
`search`/`timeline` return compact metadata and snippets, while
`get_observations(ids)` returns full bodies only for selected IDs. JarvisOS
should adapt that shape for future compact memory candidate retrieval and full
context package assembly.

### Hooks And Worker

Cavemem hooks and worker show useful event capture and lazy indexing patterns,
but JarvisOS should not implement hooks or workers before explicit memory
policy, capture scope, retention, and security tests exist. Caveman's hook
files are useful mainly for filesystem safety and mode/config risk awareness.

### Config

Reference settings show that memory, compression, search, privacy, and
embedding behavior need typed policy config. JarvisOS should keep defaults
conservative: no external providers, no implicit embeddings, no automatic
promotion, no route/UI exposure, and no hidden capture.

### MCP

Cavemem's MCP server and Caveman's MCP shrink proxy are useful future design
references. JarvisOS should not add MCP runtime now. If MCP appears later,
JarvisOS should expose compact, scoped retrieval first and require explicit
full-body-by-ID requests.

### Viewer

Cavemem's loopback viewer is useful for local inspection but has obvious memory
exposure risk. JarvisOS should defer viewer work until scope, redaction,
authentication/trust, and UI decisions exist.

### Tests

The most valuable tests to port conceptually are:

- token preservation across compression;
- no-op/empty compression refusal;
- verified raw/original backup retention;
- compact search/timeline shapes;
- full retrieval by ID;
- same-scope retrieval;
- stale embedding invalidation if embeddings are later added;
- symlink-safe config/flag handling if hooks are later added;
- hook hot-path limits if capture hooks are later added.

### Privacy And Security

Cavemem and Caveman are useful references, not sufficient security designs.
JarvisOS must add deterministic secret scanning, project/workspace scoping,
explicit retention, raw/original body policy, migration safety, audit events,
review gates, and no-external-provider defaults before memory runtime exists.

## License And Attribution Notes

- Cavemem and Caveman are MIT at the inspected commits.
- No Cavemem or Caveman source code was vendored in this milestone.
- No substantial source code blocks are copied into this document.
- Future code copying would require preserving license and copyright notices.
- Preferred future path is Python-native reimplementation of patterns unless a
  specific licensed snippet is explicitly approved later.

## Milestone Boundary Confirmation

1C-Z-T is a reference-clone audit and implementation-pattern extraction
milestone only. It does not approve Gemma, Qwen, Cavemem, Caveman, or any model
for memory, retrieval, compression, tool use, provider routing, Context Pack
Broker behavior, frontend chat, BlueRev modeling, or autonomous actions.

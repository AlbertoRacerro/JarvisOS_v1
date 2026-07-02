# docs/ — How to read this directory

This directory mixes three kinds of documents. Read them with different trust
levels.

## 1. Canonical (describes current state; wins conflicts)

| File | Scope |
| --- | --- |
| `ARCHITECTURE.md` | Current stable architecture |
| `DECISIONS.md` | Durable decisions |
| `RUNBOOKS.md` | Operational commands |
| `UI_START.md` | UI startup |
| `LOCAL_AI_EVALUATION_EVIDENCE.md` | Local model capability boundaries |
| `specs/` | Live work items and roadmap (`specs/README.md`) |
| `strategy/` | Strategic review pack (point-in-time, dated) |

If a canonical doc conflicts with current code, code wins and the doc must be
fixed.

## 2. Design docs (future intent, not runtime)

Files like `MEMORYSTORE_FACADE_DESIGN.md`, `SQLITE_FTS_MEMORY_SCHEMA_DESIGN.md`,
`PROGRESSIVE_RETRIEVAL_CONTRACT_DESIGN.md`, `FORM_PROTOCOL_CATALOG.md`,
`MICRO_CONTEXT_DESIGN.md`, `LOCAL_MODEL_SHOWCASE_FILES.md`, and similar
`*_DESIGN.md` files describe **future** behavior. They do not claim any runtime
exists. Do not implement from them without a spec in `specs/`.

## 3. Historical milestone evidence (do not treat as current)

Everything with milestone-style prefixes/suffixes (`0D_*`, `0E_*`, `1G-*`,
`FAST_SECRETARY_*`, `QWEN_PROFILE_*`, `nightly_upscale_review/`, `context_packs/`,
`reference_audits/`, milestone entries inside older docs) is a point-in-time
record of work that was done. It is kept as evidence and for provenance. Model
names, defaults, route behavior, and roadmap numbering in these files are
frequently superseded — including the `1A–6C` roadmap and `POS-*`/`BRIDGE-*`
milestone names, all replaced by `specs/`.

When in doubt: check the code, then `ARCHITECTURE.md`, then ask.

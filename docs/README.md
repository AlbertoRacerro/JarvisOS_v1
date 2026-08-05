# docs/ — How to read this directory

This directory mixes documents with different authority and freshness. Read them according to the question being answered.

## Authority by question

| Question | Primary authority |
| --- | --- |
| What does the system actually do? | Current code, runtime behavior, deterministic tests, exact-head evidence |
| What may an AI coding/review agent do? | `../AGENTS.md` plus `AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` |
| What work is active, ready, merged, blocked, or next? | `specs/STATUS.md` only |
| What is the active slice required to do? | The selected spec and readiness record |
| What durable architecture decisions were accepted? | `DECISIONS.md` |
| What is the current stable architecture? | `ARCHITECTURE.md`, only where consistent with code, accepted decisions, and current spec state |
| How is the repository started or operated? | `RUNBOOKS.md`, `UI_START.md`, and the root README |

A README is an onboarding/navigation document. It is not an independent roadmap, runtime, or merge authority.

## 1. Canonical operational and current-state documents

| File | Scope |
| --- | --- |
| `../AGENTS.md` | Hard invariants, safety boundaries, test gates, general agent conduct |
| `AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` | Delivery, exact-SHA continuation, model collaboration, finding closure, post-beta deferral, documentation drift |
| `specs/STATUS.md` | Sole live work-state, dependency, queue, and implementation-PR registry |
| `specs/README.md` | Spec execution workflow and status conventions |
| `DECISIONS.md` | Durable architecture decisions |
| `ARCHITECTURE.md` | Current stable architecture, subject to code/decision/current-state freshness checks |
| `RUNBOOKS.md` | Operational commands |
| `UI_START.md` | UI startup |
| `LOCAL_AI_EVALUATION_EVIDENCE.md` | Local model capability boundaries |

If a canonical document conflicts with current code, current behavior wins and the document must be fixed. If documents conflict about work state, `specs/STATUS.md` wins. If they conflict about agent execution, `../AGENTS.md` and `AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` win. If they conflict about durable architecture, accepted decisions and current code win over stale descriptive prose.

## 2. Design documents — future intent, not runtime

Files such as `MEMORYSTORE_FACADE_DESIGN.md`, `SQLITE_FTS_MEMORY_SCHEMA_DESIGN.md`, `PROGRESSIVE_RETRIEVAL_CONTRACT_DESIGN.md`, `FORM_PROTOCOL_CATALOG.md`, `MICRO_CONTEXT_DESIGN.md`, `LOCAL_MODEL_SHOWCASE_FILES.md`, and similar `*_DESIGN.md` files describe future behavior. They do not prove that runtime exists. Do not implement from them without an authorized spec in `specs/`.

## 3. Strategy material — dated advisory context

Files under `strategy/` are point-in-time strategic review material. They may inform definition work but do not override current code, accepted decisions, the active spec, or `specs/STATUS.md`.

## 4. Historical milestone evidence — not current authority

Everything with milestone-style prefixes or suffixes (`0D_*`, `0E_*`, `1G-*`, `FAST_SECRETARY_*`, `QWEN_PROFILE_*`, `nightly_upscale_review/`, `context_packs/`, `reference_audits/`, milestone entries inside older documents) is point-in-time evidence. Model names, defaults, route behavior, and roadmap numbering in these files are frequently superseded, including the old `1A–6C`, `POS-*`, and `BRIDGE-*` schemes.

## Conflict procedure

Do not resolve contradictions by plausibility alone.

1. Identify the exact conflicting claims.
2. Record the source file, date, and SHA.
3. Use current runtime for behavior, `specs/STATUS.md` for work state, the selected spec for scope, and accepted decisions for durable architecture.
4. Correct the stale canonical entry in a bounded documentation change.
5. Preserve superseded history when it provides provenance.

When starting a new coordinating chat, read `../AGENTS.md`, `AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `specs/STATUS.md`, and the active PR/spec at exact SHAs before relying on any narrative handoff.

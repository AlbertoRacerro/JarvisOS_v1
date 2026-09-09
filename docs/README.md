# docs/ — How to read this directory

This directory mixes documents with different authority and freshness. Read them according to the question being answered.

## Authority by question

| Question | Primary authority |
| --- | --- |
| What does the system actually do? | Current code, runtime behavior, deterministic tests, exact-head evidence |
| What may an AI coding/review agent do? | `../AGENTS.md` plus `AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` |
| What work is active, ready, merged, blocked, or dependency-eligible? | `specs/STATUS.md` only |
| What is the active slice required to do? | The selected accepted spec/readiness |
| How are concurrent builders serialized? | `POST_112_PARALLEL_DELIVERY_PROFILE.md` when applicable |
| What durable architecture decisions were accepted? | `DECISIONS.md` |
| What is the current stable architecture? | `ARCHITECTURE.md`, only where consistent with code, accepted decisions, and current spec state |
| How is the repository started or operated? | `RUNBOOKS.md`, `UI_START.md`, and the root README |

A README is an onboarding/navigation document. It is not an independent roadmap, runtime, review, or merge authority. An explicit current maintainer scheduling directive may order already-authorized work, but it does not change `STATUS.md`, readiness, accepted scope, or hard dependencies.

## 1. Canonical operational and current-state documents

| File | Scope |
| --- | --- |
| `../AGENTS.md` | Stable AI engineering constitution: goals, hard invariants, authority boundaries, frontier autonomy, interruption boundary |
| `AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` | Generic Frontier Builder Contract; delivery, convergence, proportional review/evidence, exact-head and merge mechanics |
| `POST_112_PARALLEL_DELIVERY_PROFILE.md` | Post-112 concurrency and shared-writer mutex only; not a roadmap or model-role policy |
| `specs/STATUS.md` | Sole live registry for spec state, hard dependencies, roadmap rows, and implementation-PR association |
| `specs/README.md` | Spec registry/lifecycle conventions; not a competing builder prompt |
| `DECISIONS.md` | Durable architecture decisions |
| `ARCHITECTURE.md` | Current stable architecture, subject to code/decision/current-state freshness checks |
| `GITHUB_CONNECTOR_COMPATIBILITY.md` | Superseded/inactive transport tombstone retained only for provenance; no current authority |
| `RUNBOOKS.md` | Operational commands |
| `UI_START.md` | UI startup |
| `LOCAL_AI_EVALUATION_EVIDENCE.md` | Local model capability evidence/boundaries |

`CLAUDE.md` at repository root is a compatibility bootstrap only. It grants no authority by model identity and redirects Claude-family sessions into the same capability-based governance as any other frontier model.

`JARVISOS_CURRENT_CONTEXT.md` is a **superseded navigation shim** retained only so historical links fail safely. It is not a handoff, roadmap, prompt, review policy, or current-state source.

If a canonical document conflicts with current code, current behavior wins and the stale document must be fixed. If documents conflict about spec state or hard dependencies, `specs/STATUS.md` wins. If they conflict about agent execution, `../AGENTS.md` and `AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` win. If they conflict about concurrency, the post-112 profile governs only concurrency mechanics. If they conflict about durable architecture, accepted decisions and current code win over stale descriptive prose.

## 2. Design documents — future intent, not runtime or implementation authority

Files such as `MEMORYSTORE_FACADE_DESIGN.md`, `SQLITE_FTS_MEMORY_SCHEMA_DESIGN.md`, `PROGRESSIVE_RETRIEVAL_CONTRACT_DESIGN.md`, `FORM_PROTOCOL_CATALOG.md`, `MICRO_CONTEXT_DESIGN.md`, `LOCAL_MODEL_SHOWCASE_FILES.md`, and similar `*_DESIGN.md` files describe future behavior or historical design intent. They do not prove runtime exists and do not authorize implementation without the current accepted spec/readiness.

## 3. Strategy material — dated advisory context

Files under `strategy/` are point-in-time strategic review material. They may inform definition work but do not override current code, accepted decisions, an active accepted spec/readiness, or `specs/STATUS.md`.

## 4. Historical milestone evidence — explicitly non-authoritative

Everything with milestone-style prefixes or suffixes (`0D_*`, `0E_*`, `1G-*`, `FAST_SECRETARY_*`, `QWEN_PROFILE_*`, `nightly_upscale_review/`, `context_packs/`, `reference_audits/`, milestone entries inside older documents) is point-in-time evidence. Model names, defaults, route behavior, agent roles, review recipes, and roadmap numbering in these files are frequently superseded, including the old `1A–6C`, `POS-*`, and `BRIDGE-*` schemes.

Historical PR bodies, closed review comments, old chat handoffs, disabled scheduler prompts, and retired coordination artifacts are provenance only. They must never be promoted back into current builder instructions merely because they contain detailed procedures.

## Conflict procedure

Do not resolve contradictions by plausibility alone.

1. Identify the exact conflicting claims.
2. Determine which question is being answered: runtime behavior, builder authority, spec state/dependencies, active-slice contract, concurrency, or architecture.
3. Use the narrow authoritative surface named above and fresh exact evidence.
4. Correct or explicitly tombstone the stale instruction-bearing entry in one bounded change.
5. Preserve historical provenance when useful, but clearly outside current authority.

When starting a new coordinating chat or scheduler session, read `../AGENTS.md`, `AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `specs/STATUS.md`, the active accepted spec/readiness and active PR exact head. Read `POST_112_PARALLEL_DELIVERY_PROFILE.md` only when concurrency matters. Do not preload historical governance material by default.

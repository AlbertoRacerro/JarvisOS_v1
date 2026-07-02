# JarvisOS Memory and Context Design

## Current Position

JarvisOS memory is not a free-form chat transcript passed to a model. The
intended memory architecture is staged evidence management:

1. Preserve raw input.
2. Attach metadata and provenance.
3. Enrich later.
4. Promote only reviewed or policy-valid records into stronger memory/state.
5. Retrieve bounded context at decision time.

The current runtime has project context assembly, but it does not yet have full
semantic memory/retrieval.

## Current Context Runtime

Current AI task context behavior:

- Manual `context_blocks` can be sent with an AI task.
- Project context is opt-in with `include_project_context`.
- Auto may decide context level: `none`, `light`, `standard`, `deep`.
- Context budget depends on selected local route.
- Workspace context currently comes from deterministic project-context builder
  behavior, not semantic ranking.
- Metadata exposes digest, source counts, context level, budget, and reasons.

Current default workspace in Auto when project context is used is `bluerev`,
unless a request supplies a workspace id.

## Context Level Meaning

| Level | Meaning |
| --- | --- |
| `none` | No workspace context; manual blocks still preserved |
| `light` | Small budget for low/specific workspace context |
| `standard` | Normal project-context budget |
| `deep` | Larger budget for explicit project/history/planning need |

Deep is intentionally rare. It must not be selected by complexity alone.

`context_level` should never be described as "intelligent memory routing." It is
a budget/posture control. Intelligent source selection is a future milestone.

## Current Source Selection Status

The current status is:

| Capability | Status |
| --- | --- |
| Manual context preservation | Implemented |
| Include-project-context permission cap | Implemented |
| Route-aware context budget | Implemented |
| Context digest and source count | Implemented |
| Source manifests | Implemented |
| Semantic retrieval | Not built |
| Vector search | Not built |
| LLM-ranked memory selection | Not built |
| Memory promotion runtime | Not built |
| Conflict-resolution memory layer | Not built |

## Staged Memory Design

The staged design from repository docs uses lifecycle states:

| Stage | Purpose |
| --- | --- |
| `raw_input` | Preserve original input and provenance |
| `fast_intake` | Capture cheap metadata and broad flags |
| `proposed_memory` | Candidate durable memory, not yet authority |
| `enriched_memory` | Later interpretation or extracted structure |
| `accepted_memory` | Reviewed or policy-approved memory |
| `canonical_state` | Strong project state |
| `superseded` | Retained history no longer active |

This design is important because valid JSON from a model is not semantic truth.
JarvisOS should preserve the original evidence and promote only carefully.

## MemoryStore Direction

The future `MemoryStore` facade should be the single durable write boundary for
memory. Intended rule:

> No model, hook, route, worker, tool, provider adapter, or UI component writes
> durable memory directly.

The facade should own:

- Raw/original evidence retention.
- Provenance.
- Source identity.
- Sensitivity tags and policy state.
- Promotion state.
- Conflict handling.
- Retrieval eligibility.
- Audit metadata.

This prevents future agents from turning memory into an uncontrolled side
channel.

## Micro-Context Direction

Micro-context documents are useful as bounded orientation snapshots for local
models, but they are not canonical memory. They should be regenerated from
canonical sources or accepted state.

Useful micro-context content:

- Current project objective.
- Active constraints.
- Relevant accepted assumptions.
- Current files or workspace area.
- Known non-goals.

Dangerous micro-context content:

- Unreviewed model summaries promoted as truth.
- Hidden instructions that override policy.
- Sensitive secrets or private IP.
- Contradictory state without provenance.

## Recommended Next Memory Milestones

| Milestone | Goal |
| --- | --- |
| `SOURCE-SELECTION-0` | Deterministic source chooser for workspace context |
| `MEMORYSTORE-0` | Facade contract and write boundary |
| `MEMORY-INTAKE-0` | Raw input and fast-intake persistence |
| `RETRIEVAL-0` | Structured retrieval over accepted/project records |
| `MEMORY-EVAL-0` | Tests for precision, leakage, and stale-memory behavior |

## Risks for Fable to Review

| Risk | Why it matters |
| --- | --- |
| Context bloat | Local models have limited attention and weaker instruction following |
| Stale memory | Engineering decisions can become wrong but remain plausible |
| Sensitivity leakage | Memory retrieval can surface private/IP material into cloud paths |
| Authority confusion | Model-generated summaries can look like validated project facts |
| Retrieval quality | Bad source selection can be worse than no context |

Core recommendation: keep memory staged, provenance-heavy, and policy-owned.

## Retrieval Strategy Options

Fable should compare three near-term retrieval options:

| Option | Strength | Weakness |
| --- | --- | --- |
| Structured SQL/FTS first | Auditable, deterministic, easy to test | May miss semantic matches |
| Vector search first | Better semantic recall | Harder provenance, drift, sensitivity control |
| Hybrid staged search | Best long-term fit | More implementation complexity |

The likely best path is hybrid, but not as the first runtime slice. A pragmatic
sequence is:

1. Structured source selection over known Domain Foundation records.
2. FTS over accepted/provenance-rich text.
3. Evaluation set for retrieval precision/leakage.
4. Vector search only after sensitivity and promotion rules exist.
5. LLM reranking only after source manifests and budgets are stable.

## Context Contract for Future Agents

Future agents should not receive "all memory." They should receive scoped
context packs:

| Field | Purpose |
| --- | --- |
| Objective | What the agent is asked to do |
| Workspace id | Project boundary |
| Allowed records | Explicit source list or retrieval query id |
| Sensitivity level | Policy context |
| Budget | Max chars/tokens |
| Exclusions | Records or categories withheld |
| Provenance manifest | Source ids and digests |
| Expiration | Prevents stale context reuse |

This keeps agents from building private, untracked memory channels and makes
their conclusions reviewable.

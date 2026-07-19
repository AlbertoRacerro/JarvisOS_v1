# JarvisOS delivery focus

Status: operational policy, 2026-07-19.

Authority: this document applies ADR-060 in `docs/DECISIONS.md` and the canonical
spec registry in `docs/specs/STATUS.md`. It does not replace either source and does
not create a new architecture or implementation spec.

## Decision

JarvisOS is a means to deliver trustworthy BlueRev engineering work. The immediate
program objective is not broader agent infrastructure; it is reducing the number of
days required to demonstrate one useful Mark-1 loop:

`chat -> approved decision -> calc_v0 -> engineering artifact -> BLUECAD geometry -> evidence`

The first complete loop may be visually rough. It must preserve units, assumptions,
provenance, explicit human authority, and deterministic artifacts.

## Architectural authority

ADR-060 remains binding:

- pinned Hermes is the dialogic control plane for conversation, session history,
  context selection, task decomposition, and tool-loop coordination within its
  reviewed profile;
- JarvisOS owns canonical state, MemoryStore, engineering services, sensitivity,
  budget, egress, credentials, ledger, validation, promotion, and every irreversible
  or externally visible action;
- Hermes reaches JarvisOS only through reviewed passthrough and MCP contracts;
- Hermes, models, subagents, benchmarks, critics, and reviewers may propose but do
  not become product authority;
- `bluerev-jarvis-model-bench` is an evidence harness. It may test a JarvisOS-owned
  question, but it may not define JarvisOS architecture, routing policy, memory
  authority, or production promotion.

The useful memory and routing cases merged in benchmark PR #179 remain candidate test
material. They are not an installed JarvisOS orchestration core.

## Model economy and physical capacity

The routing hierarchy remains:

1. external economical models are the normal workhorse for repetitive coding,
   extraction, and bounded analysis after JarvisOS egress approval;
2. frontier models are used for architecture, difficult judgment, and review;
3. local models are used for privacy, offline resilience, controlled fallback, and
   capabilities where measured evidence justifies them.

Logical routes and physical model slots are different concepts. JarvisOS may expose
several capability aliases while initially operating one resident local checkpoint.
A second physical slot is introduced only when separate hardware and measured swap,
latency, and reliability evidence justify it. No design may assume one resident model
per logical lane.

## Work-in-progress limit

Only two delivery lanes are active. All other roadmap items remain maintenance,
blocked, or dependency-driven.

### Lane A — Hermes integration

Objective: make pinned Hermes useful through JarvisOS authority, initially for bounded
memory consolidation.

Ordered work:

1. Preserve the merged PR #134 / spec 061a contract without adding continuation,
   segment, assembly, or orchestration semantics. Canonical flow and attempt evidence
   across no-execution, synthetic, local, external, and confirmation paths remains the
   execution/accounting authority.
2. Re-evaluate the minimum dependencies of 066 after 061a. Automatic continuations in
   061b and human grading in 062 must not block a safe single-attempt passthrough unless
   a concrete contract requires them.
3. Define and implement 066 HERMES-PASSTHROUGH-0 as the smallest disabled,
   transport-abstract OpenAI-compatible subset over `run_ai_task`, preserving 059b and
   061a authority. Hermes-side retries, fallback, direct provider access, and production
   activation remain disabled.
4. Define and implement the first bounded 067 JARVIS-MCP-0 surface as exactly four
   read-only S0/S1 tools:
   - bounded context preview;
   - canonical record search;
   - BLUECAD inspection;
   - evidence query.
   MemoryStore proposal creation, `calc_v0` execution, BLUECAD candidate creation,
   promotion, direct database access, unrestricted filesystem access, and sensitivity
   authority require separately numbered implementation contracts.
5. Freeze 068 HERMES-CONFIG-0 with an exact Hermes version/profile, enforceable
   Windows-first isolation, private authenticated transport, scoped credentials,
   bounded retention and cleanup, and exact model/tool closure. A text-only profile is
   the only allowed activation until tool-capable 066/067 fixtures are merged and
   verified. Browser, computer, cron, proactive behavior, delegation, direct providers,
   retries, fallback, terminal, and mutation tools remain disabled.
6. Run 069 MEMORY-CONSOLIDATE-0 as the first dogfood only after its required proposal
   authority is separately defined and implemented. Hermes may produce proposals with
   provenance and conflict preservation; it may not promote, overwrite, delete, lower
   sensitivity, or change routing.

No local or self-hosted model execution is authorized by this document.

### Lane B — BlueRev Mark-1

Objective: turn the workbook into trustworthy executable engineering artifacts and
then connect those artifacts to BLUECAD.

Ordered work:

1. Implement 047 BLUEREV-PROCESS-0 on the merged `calc_v0` runner:
   - geometry, hydraulics, residence/turnover, and pump nodes;
   - explicit units and provenance;
   - correction of hydraulic-versus-illuminated area;
   - correction of tube residence time versus full-loop turnover;
   - deterministic and literature verification cases.
2. Implement 048 and 049 only after 047 outputs and definitions are stable. Preserve
   the already-recorded productive-volume, recovery-balance, economic-boundary,
   buoyancy, and optical-path corrections.
3. Materialize the provenance DAG through 050 before claiming an automatic process-to-
   geometry dependency graph.
4. Implement 052 CAD-LINK over accepted calculation outputs and existing GeometrySpec
   boundaries. Solver and model outputs remain evidence, not authority.
5. Complete the operator-visible loop through 037/030 and assemble it in 055 as one
   navigable Mark-1 object.

The first Lane B checkpoint is not a broad digital twin. It is one real, reproducible
047 calculation set with artifacts and evidence that can later feed GeometrySpec.

## Merge and experiment rules

1. Every new fail-closed guard names the irreversible risk it prevents. If no such
   risk exists, the check is diagnostic or fail-open.
2. A lane may not open a second consecutive design-only PR unless the prior PR produced
   runtime evidence, a terminal closeout, or an explicit parking decision.
3. Every experiment receives either a fixed number of runs or a two-day timebox. Its
   terminal verdict is exactly one of: continue, pivot, park, or stop.
4. One repair iteration is allowed. A second repair requires an architectural decision,
   not another local hardening layer.
5. Runtime success is asserted only from evidence on the current exact HEAD. PR prose
   links runs and artifacts but does not act as the success authority.
6. `docs/specs/STATUS.md` is updated by the terminal implementation or closeout PR,
   not by every preparatory commit.
7. Raw trajectories, immutable artifacts, deterministic validators, and negative
   assertions remain independent evidence gates.
8. The maintainer's attention is reserved for domain truth, product decisions, and
   irreversible approvals. Routine diff inspection belongs to automated and delegated
   review, with the maintainer receiving a concise decision dashboard.

## Weekly decision dashboard

The strategic review should report only:

- days or blockers remaining to the next Mark-1 loop checkpoint;
- active PR in Lane A and active PR in Lane B;
- current exact-head CI and unresolved review findings;
- runtime evidence produced since the prior review;
- decisions requiring domain or product authority;
- experiments continued, pivoted, parked, or stopped;
- spend and external-egress summary from canonical JarvisOS evidence.

A growing PR count, validator count, or fixture count is not progress unless it reduces
the distance to a useful BlueRev loop or closes a named irreversible risk.

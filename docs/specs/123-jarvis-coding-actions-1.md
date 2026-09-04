# 123 — JARVIS-CODING-ACTIONS-1

## Definition

### Objective

Add one bounded Jarvis Coding action surface that can inspect accepted Coding truth and propose a concrete repository modification as an inspectable plan/diff proposal, without granting Jarvis direct repository mutation, merge, workflow, credential, runtime-update, or terminal authority.

The slice turns the existing read-only Coding foundations into an advisory operator action: Jarvis may explain the current exact repository/runtime/pipeline evidence and may produce a proposed modification packet for human/authorized development execution. It must not become a second GitHub writer, planner, queue, review authority, or merge actor.

### Existing owners to reuse

- `111 JARVIS-CONTEXT-ACTION-FOUNDATION-1` remains the shared exact-context/capability/action contract and the existing AI execution/policy spine.
- `118 CODING-REPOSITORY-TRUTH-1` remains the sole server-side remote repository/ref/SHA/PR/check/review truth owner.
- `119 CODING-RUNTIME-TRUTH-1` remains the sole local executed-path/ref/SHA/dirty/build/runtime observation owner.
- `120 DEVELOPMENT-PIPELINE-STATE-1` remains the sole read-only development-pipeline projection for Proposal → Plan → Implementation → Tests → Independent Review → Reconciliation → Merge.
- `docs/specs/STATUS.md` remains the sole live roadmap/work-state authority.
- Existing GitHub connector/ChatGPT writer, deterministic CI, independent review, mutex, lifecycle, merge and reconciliation mechanisms retain all mutation authority.

### Bounded product boundary

123 may define Coding capabilities that consume explicit exact context refs and return advisory artifacts such as:

- repository/runtime/pipeline explanation grounded in accepted 118/119/120 evidence;
- a bounded modification intent tied to an exact repository/ref/SHA and explicit target paths;
- an inspectable proposed patch/diff or equivalent structured change plan;
- expected deterministic tests/checks and explicit preconditions/blockers;
- provenance sufficient to show what exact evidence the proposal was derived from.

A 123 action is proposal-only. It cannot write repository files, create/update branches or PRs, dispatch workflows, request reviews, merge, change STATUS, restart/update JarvisOS, open a PTY, execute arbitrary shell/Git commands, or silently promote its proposal into any authoritative development state.

### Authority and safety invariants

1. **Proposal only.** 123 has no repository, branch, PR, workflow, review, merge, STATUS, runtime-update, process, PTY, filesystem-write, database, or credential mutation authority.
2. **Exact identity.** Any repository-targeted proposal is bound to an explicit configured repository plus exact ref/SHA evidence from 118. Stale/moved/unknown identity fails closed and cannot be presented as current.
3. **Observed runtime is not write authority.** 119 runtime/dirty/alignment evidence may constrain or explain a proposal but cannot authorize update/restart or local filesystem mutation.
4. **Pipeline evidence is advisory.** 120 stage state may explain blockers/next lawful lifecycle steps but cannot grant readiness, review acceptance, reconciliation, or merge authority.
5. **No second planner/queue.** Proposed modifications are action results/evidence, not durable roadmap state, hidden tasks, background jobs, or a shadow development ledger.
6. **No semantic fabrication.** Jarvis/model output is advisory. Exact repository facts, accepted context refs, canonical lifecycle state and deterministic checks remain externally verifiable evidence rather than model claims.
7. **Conservative stale handling.** A moved target, missing/partial evidence, unconfigured repository, unsupported file/path class, or ambiguous requested mutation degrades to explicit refusal/unknown/proposal-unavailable; never guess a current patch target.
8. **Bounded disclosure.** Reuse existing secret/sensitivity/egress/context policies and 118 bounded projections. Do not expose provider credentials, arbitrary unbounded repository payloads, raw local secrets, hidden prompts, or unrestricted file/log content.
9. **No authority laundering through tools.** The action must not gain mutation indirectly through generic GitHub, shell, filesystem, subprocess, local Git, MCP, external-agent, or provider tooling.
10. **Independently removable.** Removing 123 leaves 111/118/119/120 and all existing development authority unchanged.

### Full-spec questions to freeze before readiness

The full specification must resolve, from then-current master:

- the minimum 111 capability/action identities and request/response schema for inspect/explain versus suggest-modification;
- the exact allowed context refs from 118/119/120 and how mismatched repository/ref/SHA/workspace evidence is rejected;
- the smallest structured modification-proposal contract, including target paths, exact base SHA, proposed diff/plan representation, provenance, assumptions, tests/checks and bounded warnings;
- whether proposal generation is deterministic/template-derived, model-assisted through the existing AI execution spine, or a bounded composition of both, while preserving current sensitivity/egress/budget policy;
- accepted file/path/content bounds and explicit unsupported targets such as binary/oversized/ambiguous changes;
- stale/CAS semantics between evidence collection and proposal return;
- how operator-visible refusal distinguishes missing evidence, unsupported request, stale target, policy denial, provider/model failure and proposal parse/validation failure;
- the exact relationship to existing human/ChatGPT repository writers: 123 may hand off a proposal artifact/context, but no 123 response can execute it;
- deterministic acceptance fixtures proving that no hidden repository/runtime mutation path exists.

### Implementation surface deferred to full spec/readiness

This definition grants no runtime implementation authority. Full spec/readiness must revalidate current 111 action registration/execution owners and current 118/119/120 services before selecting the smallest route/service/schema/test files.

Prefer a thin action adapter over the accepted owners. Do not add a generic coding-agent framework, repository write API, local Git wrapper, PTY, patch-application engine, durable task store, second planner, workflow actuator, merge bot, or frontend redesign merely to deliver 123.

### Acceptance target

123 is complete when an operator can ask Jarvis for an exact-context Coding inspection/explanation or a bounded suggestion for a repository modification, receive an inspectable exact-base proposal/diff/plan with explicit provenance/tests/staleness, and verify that every authoritative mutation remains outside 123 with existing development owners and gates.

### Non-goals

- no direct repository/file/branch/PR/STATUS mutation;
- no workflow/review/merge/reconciliation actuation;
- no auto-merge or hidden development continuation;
- no local runtime update/restart/rollback authority from 125;
- no PTY/shell/session authority from 126;
- no generic autonomous coding agent, second planner/queue, durable coding task store, or background worker;
- no new provider credential or egress path;
- no Hermes runtime/re-derivation or legacy 066–068 reopening;
- no frontend redesign or unrelated Coding/Development feature work.

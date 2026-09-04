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

## Full specification

### Product surface and capability identities

123 adds exactly two route-scoped capabilities on the existing canonical Coding routes:

- `coding.inspect` — action class `READ`, available on `coding-repository` and `coding-runtime`, returning an exact-context explanation assembled from accepted 118/119/120 projections;
- `coding.suggest-modification` — action class `PROPOSE`, available on `coding-repository`, returning one bounded modification proposal tied to an exact repository/ref/base SHA.

No new canonical frontend route is required. The implementation reuses 111 `JarvisCapabilityDescriptor`, exact-ref validation, context preview/digest semantics, and existing Coding route owners. It must not register `COMMIT` or `EXECUTE`.

### Request boundary

A suggest-modification request contains only:

- `workspace_id`;
- configured `repository`;
- exact `base_ref` and 40-character `base_sha`;
- one bounded natural-language `intent` (1–4000 chars);
- 1–16 explicit repository-relative `target_paths`;
- optional exact 111 context refs already accepted by the context preview boundary;
- optional expected deterministic checks, maximum 16 short strings.

Paths must be normalized POSIX-style repository-relative text, unique after normalization, at most 256 chars each, with no absolute path, drive prefix, `..`, NUL, backslash traversal, `.git/`, data-root path, or unsupported binary target. `.github/**`, `AGENTS.md`, `CODEOWNERS`, secret-bearing/config credential surfaces, and any path outside the explicitly requested set are rejected for the first release. The full proposal is unavailable rather than silently widening paths.

### Exact-evidence inputs

The action may consume only bounded projections owned by accepted slices:

- 118 configured repository/ref/file/PR/check/review truth for the exact target repository and SHA;
- 119 runtime observation only when its observed repository identity corresponds to the same configured repository and its reported SHA/ref relation can be tied to the request;
- 120 pipeline-state evidence only when its repository/PR/head/base identity is consistent with the same exact target;
- 111 exact context refs whose workspace matches the request and whose preview is dispatchable/current.

Mismatched repository, workspace, ref, SHA, stale/partial identity, or conflicting evidence fails closed with a typed refusal. 119 dirty/runtime state may create warnings or refusal but never grants mutation authority. 120 lifecycle state may explain a lawful next step but never grants readiness, review acceptance, merge, or reconciliation authority.

### Freshness / CAS protocol

For every proposal:

1. resolve the configured repository target through 118 and freeze exact `base_ref -> base_sha`;
2. build/validate any 111 context preview and digest;
3. read only the explicit bounded source evidence needed for the requested target paths and optional 119/120 evidence;
4. generate and validate the proposal;
5. re-resolve `base_ref` through 118 and revalidate any exact evidence identities used;
6. if ref/SHA/context identity moved or became partial/unknown, return `stale` and no current proposal.

There is no retry loop chasing a moving head. Callers may retry from fresh evidence.

### Proposal generation

The first release is a bounded composition:

- deterministic code owns target identity, path admission, evidence selection, prompt/schema construction, output parsing, diff validation, size limits, staleness, and refusal;
- when a non-template change proposal requires semantic generation, it may call the existing `run_ai_task` execution spine only through current JarvisOS routing/egress/sensitivity/budget/provider policy; no provider is called directly and `route_class="auto"` remains non-external;
- deterministic inspect/explain may return directly from accepted projections without a model call when no semantic synthesis is needed.

Model output is never accepted as repository truth. It is parsed into the closed proposal schema below and rejected on malformed/oversized/out-of-scope content.

### Modification proposal contract

A successful proposal contains:

- `state = "proposed"`;
- exact `repository`, `base_ref`, `base_sha`, `workspace_id`;
- original bounded `intent`;
- ordered `target_paths`;
- `summary` (max 2000 chars);
- `changes`: 1–16 entries, each naming exactly one admitted target path and containing either a bounded unified-diff text fragment or a bounded structured change plan, never both;
- `assumptions` and `warnings`, each at most 16 strings of 256 chars;
- `expected_checks`, at most 16 strings of 128 chars;
- provenance containing the 111 context digest when used plus exact 118/119/120 identities actually consumed;
- `generated_by` identifying deterministic/template or AI-task provenance without exposing hidden prompts/provider credentials.

Total serialized proposal payload is capped at 128 KiB; each diff/plan entry is capped at 32 KiB. Binary patches, renames outside the admitted set, file-mode changes, symlink/submodule changes, Git metadata changes, and any diff header/path not exactly matching an admitted target are rejected.

The response is an ephemeral action result only. 123 adds no database table, task queue, proposal ledger, background worker, branch, PR, artifact persistence, or automatic handoff actuator.

### Refusal taxonomy

Non-success responses use a closed reason family:

- `missing_evidence`;
- `stale_target`;
- `identity_conflict`;
- `unsupported_target`;
- `policy_denied`;
- `provider_unavailable`;
- `proposal_invalid`;
- `proposal_too_large`;
- `unknown`.

Provider exception text, secrets, raw unrestricted file contents, hidden prompts, and sensitive policy internals are never returned.

### Relationship to authorized development writers

A 123 proposal may be copied/consumed by the existing human/ChatGPT development process as advisory input only. The consumer must independently revalidate current repository authority and exact head before applying anything. No response field is an actuator token or permission grant. 123 has no GitHub write client, local Git/subprocess/shell/filesystem-write path, workflow dispatch, review request, branch/PR creation, STATUS mutation, merge, self-update, restart, rollback, PTY, or terminal session capability.

### Implementation surface

Fresh master supports the following minimum bounded implementation:

- `backend/app/modules/ai/jarvis_context_models.py` — add the closed request/response/proposal models and keep action class bounded to existing `READ`/`PROPOSE` vocabulary;
- `backend/app/modules/coding/actions.py` — thin stateless 123 service over injected 118/119/120/context/AI owners, path admission, exact identity, validation, and proposal parsing;
- `backend/app/modules/coding/runtime_routes.py` — add the bounded inspect/suggest endpoints under the existing `/api/coding` router; no new root router;
- `backend/tests/test_jarvis_coding_actions_123.py` — deterministic unit/route/hostile-output acceptance coverage.

A deterministic implementation failure may justify the smallest supporting change to an existing 111/118/119/120 owner, but no new repository provider, credential seam, schema/migration, durable store, workflow, frontend redesign, generic coding-agent framework, or mutation API is authorized.

### Deterministic acceptance matrix

The implementation must prove at least:

1. current configured repository + exact base ref/SHA + admitted targets yields an inspectable proposal tied to that exact base;
2. ref moves before return -> `stale_target`, no current proposal;
3. unconfigured repository -> refusal before provider dispatch;
4. workspace/exact-ref mismatch -> `identity_conflict`;
5. stale/unknown 111 context -> no proposal dispatch;
6. conflicting 118/119/120 repository/ref/SHA evidence -> fail closed;
7. absolute/traversal/backslash-drive/Git-metadata/protected/undeclared path -> `unsupported_target`;
8. duplicate/over-limit target paths are rejected;
9. model output attempting an undeclared second path is rejected;
10. binary/file-mode/symlink/submodule/rename-outside-scope diff is rejected;
11. malformed proposal JSON/schema -> `proposal_invalid`;
12. per-change or total payload limit breach -> `proposal_too_large`;
13. policy/provider denial maps to bounded refusal without leaking raw provider errors;
14. deterministic inspect/explain can complete without a provider call when accepted projections suffice;
15. semantic generation, when used, goes only through the existing AI execution spine and creates its normal AI-job/accounting evidence;
16. no `COMMIT`/`EXECUTE` capability is registered by 123;
17. route/service expose no GitHub write, local Git/subprocess/shell/filesystem write, workflow/review/merge/STATUS/self-update/PTTY authority;
18. existing 111 context preview and 118/119/120 read-only endpoints remain unchanged.

## Readiness decision — 2026-09-04

### Exact-master revalidation

Readiness is derived from exact master `eb7b053b9b94ad5614f566b46bc9a271a420e025` after definition PR #543 merged.

Fresh code confirms:

- 111 already defines `READ` and `PROPOSE` action classes, canonical Coding routes, exact refs, bounded context preview, stale-ref refusal, and a capability registry that rejects `COMMIT`/`EXECUTE`;
- 118/119/120 are merged and expose the exact remote repository truth, local runtime observation, and development-pipeline projection that 123 is defined to consume;
- the existing `/api/coding` router is already mounted, so no second router/provider/config owner is needed;
- current Coding modules contain no repository mutation owner or generic coding-agent framework that 123 must preserve;
- no schema/migration, credential, provider route, durable task store, PTY, self-update, workflow, or frontend redesign is required for the accepted first release.

### Failure-mode disposition

- **Stale ref between evidence and proposal:** closed by final exact-ref revalidation and fail-closed response.
- **Model invents files/paths:** closed by explicit target allowlist plus post-parse diff-path validation.
- **Authority laundering through a proposal:** closed by no write/tool actuator in the service and no COMMIT/EXECUTE capability.
- **Provider/egress bypass:** closed by allowing semantic generation only through the existing AI execution spine.
- **Secret/unbounded repository disclosure:** closed by bounded accepted projections, explicit target paths, size limits and safe refusal mapping.
- **Proposal becomes shadow queue/state:** closed by ephemeral response-only contract and no store/background worker.
- **Dirty/divergent runtime mistaken for write permission:** closed by 119 remaining observation-only and never an authorization input.
- **Need for arbitrary binary/rename/mode changes:** PARK; outside the first-release proposal boundary and not required by the acceptance target.

### Minimum-necessary test

Criterio di accettazione: provide an exact-context Coding inspection and bounded modification suggestion without granting repository/runtime mutation authority.

Questo lavoro serve a soddisfarlo? **sì**.

Il criterio è raggiungibile without a new writer/provider/store/framework? **sì** — reuse 111/118/119/120 and the existing AI execution spine; therefore none is added.

### Readiness verdict

**READY once this planning/readiness PR merges and the live registry row is transitioned to `ready`, either atomically in the same accepted PR or through the smallest mechanical follow-up.**

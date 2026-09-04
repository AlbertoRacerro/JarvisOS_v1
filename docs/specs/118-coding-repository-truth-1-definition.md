# 118 CODING-REPOSITORY-TRUTH-1 — definition

Exact source master: `472881cdf51453fd49dfa9ed6e78fdb9318f65d6`.

Authority: definition only. This document does not authorize runtime implementation and does not change the live `118` registry row from `planned`.

Governing authority:
- `AGENTS.md` and `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` for safety, exact-head evidence, lifecycle, and repository-development authority;
- `docs/specs/STATUS.md` for the live `118` row, dependency, and state;
- `docs/specs/README.md` and `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` for the active Coding-first post-134 lifecycle;
- merged `111 JARVIS-CONTEXT-ACTION-FOUNDATION-1` for explicit READ/CONTEXT/PROPOSE separation and domain-owned mutation authority;
- merged V3.2 repository-development controls through exact master above.

## Problem

The Coding lane needs server-side remote-repository truth that can answer bounded inspection questions without making the browser, a model, a local checkout, branch-name assumptions, or copied repository text authoritative. The current roadmap objective for `118` is deliberately narrower than repository automation: a bounded read-only repository inspector.

Without one owned server-side seam, later Coding work can drift into direct frontend GitHub access, model-supplied repository facts, stale branch-name evidence, duplicated local clones, ad-hoc network calls, or read paths that quietly grow mutation/credential authority.

## Definition boundary

`118` owns only a bounded server-side read-only repository-truth capability for explicitly authorized repositories and refs.

It MUST define, in the later full specification:

1. **Exact repository identity** — repository truth is bound to an explicit configured/authorized repository identity; model text, browser input, arbitrary URLs, redirects, or inferred owners are never sufficient authority.
2. **Exact ref evidence** — reads resolve and return the exact immutable commit SHA actually inspected. Branch/tag names may be inputs only when the server resolves them and binds the result to the returned SHA.
3. **Bounded inspector operations** — the accepted read surface is an explicit allowlist of repository-inspection operations needed by the Coding lane, not a generic GitHub/API proxy.
4. **Server-side ownership** — credentials, host policy, rate limits, network transport, response validation, and repository access remain backend-owned. Frontend and model outputs never receive provider credentials or direct provider/tool authority.
5. **Read-only enforcement** — `118` cannot create/update/delete files, refs, branches, commits, issues, PRs, reviews, labels, workflows, repository settings, secrets, releases, merges, or dispatches. Read success must not have repository side effects.
6. **Bounded content** — path count, file size, aggregate payload, diff/compare size, pagination, timeout, redirect behavior, and response size must be deterministic and fail closed rather than silently widening scope.
7. **Provenance and freshness** — every material result carries enough repository/ref/path/provider provenance to distinguish exact current evidence from stale, unavailable, truncated, or unknown evidence. No result is promoted to `current` or `aligned` without exact evidence.
8. **Typed failures** — missing/private repositories, unauthorized repositories/refs, missing paths, stale/moved refs, provider/rate-limit failures, malformed provider responses, oversized results, and unsupported operations remain distinguishable failures rather than guessed data.
9. **No canonical-state promotion** — repository reads are evidence/context. They do not mutate JarvisOS canonical domain state or grant later COMMIT/EXECUTE authority.

## Trust-boundary invariants

Because this slice crosses a network/provider/credential boundary, it retains the full separate definition -> full spec -> readiness -> implementation lifecycle.

The full specification MUST preserve these invariants:

- allowlisted provider/host/repository ownership is validated before network dispatch; no arbitrary URL fetcher or SSRF-capable escape hatch;
- credentials are least-privilege, server-side only, never logged or returned, and no broader token is introduced merely to simplify implementation;
- redirects, alternate hosts, archive/submodule/LFS indirection, symlinks, encoded paths, traversal forms, and provider-specific download URLs cannot bypass host/repository/path bounds;
- repository content is untrusted data, never executable input: no checkout-triggered scripts, hooks, builds, imports, shell evaluation, workflow dispatch, or automatic code execution;
- model-proposed repository/ref/path values are advisory inputs that pass deterministic authorization and bound checks before any read;
- exact-SHA evidence outranks branch names, cached summaries, model claims, and local checkout state;
- cache, if any is later accepted, is derived evidence keyed strongly enough to avoid cross-repository/ref confusion and can never masquerade as a fresher exact read;
- truncation or partial pagination is explicit and cannot be interpreted as a complete repository/diff/file result;
- provider errors never fall back to fabricated, cached-as-current, or alternate-host data without explicit accepted semantics.

## Reuse / current-owner obligations for full-spec derivation

The full-spec pass must inventory fresh exact-master code before choosing files, schemas, endpoints, or credentials. It must prefer existing first-party seams over new ownership where they satisfy the boundary, including:

- the current backend service/API ownership pattern used by Jarvis/domain reads;
- existing approved outbound-network/provider enforcement and GitHub transport ownership;
- existing secret/configuration loading and redaction rules;
- existing exact-reference / stale-safe context contracts from `111` and subsequent merged slices;
- existing deterministic size/timeout/error patterns and audit/ledger evidence where already applicable;
- existing frontend Jarvis/Coding context seams, without granting direct frontend provider access.

Any proposed new transport, credential, cache, schema, persistent store, or provider abstraction must identify the concrete insufficiency in current owners and pass the minimum-necessary test. A generic multi-provider SCM framework is not presumed necessary.

## Questions the full specification must resolve from fresh code

1. Which concrete repository-inspection operations are necessary for the first useful Coding slice: repository/ref metadata, tree/path listing, bounded file reads, commit metadata, compare/diff evidence, or a smaller subset?
2. Which existing backend network/provider owner can lawfully perform those reads, and what exact host/repository allowlist model already exists or must be minimally added?
3. What least-privilege authentication mode is required for the user's intended repositories, and can public/read-only access satisfy any accepted path without adding a secret?
4. What exact immutable identity accompanies each operation, including provider repository identity, resolved commit SHA, path/ref, truncation/pagination state, and response provenance?
5. What deterministic bounds apply to paths, blobs, trees, compares, pagination, redirects, timeouts, retries, and provider rate limits?
6. How are hostile repository contents represented safely so binary/invalid UTF-8/huge/generated/secret-bearing files do not escape response and context limits?
7. Which repository data may become Jarvis CONTEXT under `111`, and what preview/digest/stale checks are required before model use?
8. What audit/telemetry is necessary to prove a read occurred without logging credentials or sensitive repository contents?
9. Which existing tests/gates can prove no write-capable endpoint or provider operation is reachable through the `118` surface?

## Acceptance criteria for the future full spec/readiness

Before `118` can become `ready`, fresh exact-master planning evidence must prove all of the following:

1. every accepted operation is explicitly read-only, bounded, and mapped to one server-side owner;
2. every material result is bound to an exact resolved commit SHA and explicit repository identity;
3. arbitrary hosts/repositories/URLs and traversal/redirect/provider-indirection escapes fail closed before sensitive dispatch;
4. credentials are least-privilege, server-owned, redacted, and absent from frontend/model-visible payloads;
5. repository content is treated as untrusted data and no accepted read path can execute repository-controlled code or workflows;
6. payload, pagination, file/tree/diff, timeout, retry, and rate-limit bounds are explicit and deterministically testable;
7. stale/moved refs, partial results, provider failure, unsupported content, authorization failure, and missing data have typed non-fabricating outcomes;
8. `111` READ/CONTEXT separation is preserved and no repository read grants COMMIT/EXECUTE or canonical mutation authority;
9. deterministic tests cover at minimum unauthorized repository/host/ref, stale ref, traversal/encoded path, redirect/alternate host, oversized/partial result, binary or invalid content, provider/rate-limit failure, credential redaction, exact-SHA binding, and rejection of write-capable operations;
10. the implementation plan names exact existing code owners/files and demonstrates why any new transport/config/schema is the smallest necessary change.

## Non-goals

- Repository mutation, branch creation/update, commits, PR/issue/review/label/workflow/release/settings/secrets writes.
- Merge, deployment, CI dispatch, self-update, patch application, code execution, shell/PTY, or local checkout orchestration.
- Generalized autonomous coding-agent orchestration or a second planner/lock/queue.
- A generic Git hosting abstraction across hypothetical providers unless a later accepted requirement proves it necessary.
- Runtime/deployment truth owned by `119`/`120` or domain-specific Jarvis actions owned by later accepted slices.
- Hermes release/re-derivation, provider expansion, Ruff autofix, CI digest, or unrelated governance work.
- A second canonical repository database or copied mirror of remote repository truth.

## Minimum-necessary test

Criterion: provide the Coding lane one authoritative, bounded, exact-ref, read-only server-side repository-inspection seam before later repository/runtime actions are derived.

This definition is necessary because later Coding slices otherwise need to infer repository state from model text, frontend/provider access, local checkout state, or duplicated ad-hoc transports. It deliberately stops before selecting concrete runtime files/endpoints/credentials: those choices require a fresh exact-master full-spec inventory and separate readiness decision because the slice crosses provider, credential, egress, and repository trust boundaries.

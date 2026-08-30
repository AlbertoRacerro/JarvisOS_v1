# 128 ARCHITECTURE-ENFORCEMENT-GATE-1

Status: full specification / planning authority only

## Purpose

Add deterministic repository CI architecture guards that prevent new ownership side channels while preserving current behavior. The gate is a ratchet, not a cleanup slice: existing debt is explicitly allowlisted with an owner/removal spec, and new debt fails closed.

## Authority and boundary

This slice is repository-development enforcement only. It does not change JarvisOS runtime/domain/provider authority, schemas, stores, APIs, provider routing, egress policy, or product behavior. `AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`, and `docs/specs/STATUS.md` remain higher authority.

Coordination Bus V2 artifacts are always non-authoritative proposal material. The enforcement gate MUST make it impossible for a V2 WORKPACK/CANDIDATE_PATCH to become authority or self-apply merely because its syntax is valid or a helper claims tests passed.

This full specification is derived from exact master `a1d7bf38a8072cbf19f2d341e702e3e3e0df370e`. It remains planning-only. `STATUS.md=planned` remains authoritative until a separate fresh readiness decision is accepted and the registry is reconciled to `ready`.

## Exact-master inventory requirement

Before readiness, inventory exact current `master` for first-party patterns that can create a second authority path, including at minimum:

1. raw SQLite connections/SQL ownership outside accepted database/core or explicitly owned persistence boundaries;
2. direct external-provider/network dispatch outside the accepted AI execution/provider/egress spine;
3. domain-side mutation paths that bypass accepted owner/service/CAS/reconciliation boundaries;
4. repository-development automation that could treat Coordination Bus V2 comments/workpacks/candidate patches as executable, approval, readiness, merge, queue, or shared-authority input.

Each existing exception retained by the gate must be exact and reviewable, and must name an owner/removal spec or an explicit durable accepted owner. Broad directory-wide exemptions are not acceptable when a narrower symbol/path rule is practicable.

### Inventory methodology frozen by this full spec

Readiness must perform the inventory against a fresh exact master, not this derivation SHA if master has moved. The inventory is source-based and reproducible:

- enumerate first-party Python, TypeScript/JavaScript, shell/PowerShell, workflow YAML, and repository-development scripts from the Git tree;
- classify generated/vendor/build/cache/material explicitly before scanning rather than silently excluding arbitrary directories;
- use Python AST for import/call ownership rules where aliasing matters, including `sqlite3`, HTTP/network clients, provider SDKs, and direct mutation-service imports/calls;
- use structured YAML parsing or an equivalent deterministic workflow inspection for trigger/permission/action checks;
- use exact path/symbol matching for accepted owners and debt entries; no basename-only or broad directory wildcard exemption is sufficient when a symbol-level or file-level rule is practical;
- record every retained exception as `{rule_id, exact_match, classification, owner_or_removal_spec, rationale}`;
- treat scanner uncertainty as a readiness finding to resolve, not as evidence that a path is clean.

The current exact-master tree already confirms `backend/app/core/database.py` as an accepted core database boundary. That fact does not imply that other SQLite usage is absent; readiness must complete the repository-wide inventory before acceptance.

## Gate design

The implementation SHALL provide one locally runnable deterministic command and one PR-CI invocation of the same command. The preferred minimum shape is a repository script plus narrowly scoped tests and a CI step; no service, daemon, database, durable architecture registry, model call, or provider is justified.

The gate owns four rule families:

### AE001 — persistence ownership

Reject new first-party raw SQLite connection/SQL ownership outside accepted core/persistence owners or exact retained debt entries. The rule must detect aliased imports/calls where practical. Schema/migration text and test fixtures must be classified separately from runtime connection ownership so they cannot become accidental blanket exemptions.

### AE002 — external dispatch ownership

Reject new first-party external-provider/network dispatch outside accepted AI execution/provider/egress owners or exact retained debt entries. Generic HTTP clients and provider SDK aliases must not bypass the check. Existing AI bypass debt discovered by readiness is retained only as an exact exception assigned to 129 or another already-accepted durable owner.

### AE003 — canonical mutation ownership

Reject new direct domain mutation paths that bypass accepted owner/service/CAS/reconciliation boundaries. Readiness must freeze the concrete protected owner seams and exact legacy exceptions from then-current master; the first gate must not guess domain semantics from function names alone. Where a robust AST import/call rule cannot establish a semantic boundary without false authority, the full readiness packet must choose a smaller exact seam and document residual risk rather than add a heuristic wildcard.

### AE004 — coordination negative authority

Reject repository-development automation that can consume Coordination Bus V2 material as executable/approval/readiness/queue/merge/shared-authority input. The check must cover at minimum workflows/scripts with automatic `issue_comment` handling or explicit V2 marker parsing that can reach mutation/application actions. Mere read-only diagnostics or the accepted helper append are not authority.

## Allowlist and debt contract

There is no auto-generated baseline and no command that rewrites/broadens the allowlist from observed violations. A baseline refresh that silently blesses current findings is prohibited.

Every retained exception must:

- identify one rule family;
- match an exact path plus symbol/call/import pattern when the rule has symbol semantics;
- state `accepted_owner` or a concrete removal/closure spec;
- state why the exception is legacy debt versus desirable architecture;
- fail validation if its owner/removal disposition is empty or references a cancelled/nonexistent authority without an explicit durable-owner rationale.

Removing an exception because debt was closed is allowed in a later authorized slice. Adding or broadening an exception is an architecture-governance change and must be review-visible; the scanner must not do it automatically.

## Required behavior

- Add an offline deterministic architecture check runnable locally and in CI.
- Reject newly introduced forbidden ownership patterns relative to the accepted exact allowlist/baseline.
- Keep allowlisted legacy debt visible and attributable; the gate must not silently normalize it as desirable architecture.
- Current AI bypass debt identified by the exact-master inventory is owned by 129 where applicable.
- Fail with actionable rule id, path, and symbol/pattern diagnostics.
- Avoid heuristic checks that are trivially bypassed by whitespace or aliasing when a small AST/structured check is practical.
- Do not delete, rewire, or refactor runtime code merely to make the first gate green.
- Do not introduce a second architecture registry/store; repository-controlled rule/config data may exist only as the minimum deterministic gate input.
- Do not require network, providers, credentials, runtime data root, or paid AI in tests.
- Exit non-zero on malformed rule configuration, duplicate conflicting exception identities, unknown rule ids, or an unexplained broad exemption.
- Produce stable ordering so identical trees/configuration yield identical diagnostics.

## Coordination Bus V2 negative-authority requirements

The implementation and tests must prove at least these invariants:

- bus issue/comment content is never imported/executed/applied by product or repository-development code as code;
- a WORKPACK/CANDIDATE_PATCH cannot mutate branch/files/STATUS/spec/readiness/PR/review/merge state without a separate ChatGPT writer action that re-reads canonical authority and exact SHA;
- bus content cannot establish readiness, semantic acceptance, finding closure, queue state, merge authority, or Codex budget state;
- no new workflow/action/script gains an automatic `issue_comment` path that applies candidate patches or grants authority from the V2 marker/envelope.

This requirement does not prohibit the explicitly accepted helper behavior of appending one non-authoritative V2 message while another writer is BUSY.

The gate is repository-static enforcement, not a runtime trust engine. It proves the absence of forbidden repository-owned application paths covered by AE004; it does not claim that arbitrary external actors cannot copy text manually.

## Deterministic test matrix

Readiness must bind concrete test file names/allowed paths, but implementation acceptance must include at least:

| Case | Expected |
| --- | --- |
| accepted core SQLite owner | PASS |
| aliased raw SQLite connection in a non-owner fixture tree | FAIL AE001 |
| accepted provider/egress execution seam | PASS |
| aliased direct HTTP/provider dispatch outside owner | FAIL AE002 |
| accepted canonical mutation seam | PASS |
| direct protected mutation bypass fixture | FAIL AE003 |
| inert V2 marker/workpack text fixture | PASS and never execute/apply |
| workflow/script auto-consumes V2 candidate on `issue_comment` into mutation | FAIL AE004 |
| exact retained debt entry | PASS with debt still reportable/reviewable |
| new path hidden only by a parent-directory wildcard | FAIL configuration/review test |
| malformed/unknown exception entry | FAIL closed |
| same source tree scanned twice | byte/stably equivalent ordered findings |

Tests must operate on fixtures or temporary source trees and must not mutate canonical repository state, invoke GitHub writes, contact providers/network, require secrets, or read a production data root.

## CI contract

The implementation must hook the same local architecture command into the normal pull-request deterministic CI path. The CI wrapper may select repository root/event metadata, but rule evaluation must not have a separate CI-only implementation.

The gate must run for pull requests that can change first-party runtime or repository-development automation. If path filtering is used, readiness must prove it cannot omit rule/config/scanner/workflow changes that could weaken enforcement. A conservative always-run PR step is preferred unless measured cost justifies narrower filtering.

The gate has no authority to approve or merge a PR. Green means only that the frozen architecture rules found no forbidden condition.

## Implementation path boundary to freeze at readiness

Readiness may authorize only the minimum paths needed for:

- one architecture scanner/check under the repository's existing `scripts/` or equivalent deterministic tooling owner;
- one narrow rule/config artifact if exact exceptions cannot be represented clearly in code without obscuring review;
- focused deterministic scanner tests/fixtures;
- the existing PR CI workflow file necessary to invoke the local command;
- `docs/specs/STATUS.md` only for normal lifecycle bookkeeping, not as scanner input.

Any runtime `backend/app/**`, production frontend, schema/migration, provider implementation, domain service, durable store, or product behavior mutation is outside 128 and requires a fresh authority decision.

## Acceptance criteria

1. A reproducible exact-master inventory identifies the enforced ownership classes and every retained exception.
2. Each retained debt exception has a narrow match plus owner/removal disposition; unexplained wildcard exemptions fail review.
3. Deterministic tests demonstrate at least one forbidden-new-case failure for each enforced class and demonstrate accepted owner paths remain green.
4. Dedicated tests prove the Coordination Bus V2 negative-authority requirements above, including rejection/non-execution of candidate patch text.
5. CI runs the architecture gate on pull requests without provider/network/secret dependence.
6. Existing required backend/frontend/BLUECAD gates remain green on the frozen implementation head.
7. No runtime behavior, schema, API, provider, product UI, or canonical domain ownership is changed by 128.
8. The local and CI gate use one rule implementation and fail closed on malformed configuration.
9. Findings are stable and actionable, with rule id/path/symbol or structured trigger diagnostics.
10. No automatic baseline refresh, auto-fix, patch application, queue mutation, or architecture-exception blessing exists.

## Failure modes to cover

- allowlist so broad that new debt hides under an old directory exemption;
- string/regex-only scanner misses aliased imports or structured calls that should be detectable;
- false positive on accepted database/provider owner code;
- generated/vendor/migration/test fixture content mistaken for new runtime authority without an explicit classification rule;
- bus marker/comment text accidentally treated as executable patch input;
- CI-only path diverges from the locally testable command;
- baseline refresh command can silently bless new violations;
- AST scanner ignores import aliases, qualified calls, or nested source roots;
- parser failure is treated as clean rather than fail-closed;
- an exception remains after its path/symbol disappears and obscures future drift;
- a workflow trigger is inspected by string search while equivalent structured YAML escapes detection;
- the gate starts enforcing product semantics that it cannot prove statically and thereby becomes a shadow authority registry.

## Non-goals

- no cleanup of the violations found by the inventory;
- no implementation of 127, 129, 130, 131, 132, 133, or 134;
- no `jarvis-pr-attention` integration;
- no 113–126 implementation/planning reopening;
- no new provider, credential, database, durable store, schema, migration, frontend, or domain feature;
- no auto-fix or auto-apply of architecture violations or bus candidate patches;
- no broad dependency graph, generic linter framework, policy service, or replacement for code review;
- no claim that static checks prove semantic correctness of accepted owners.

## Required readiness evidence

Readiness must bind to a fresh exact master and include:

- inventory methodology and findings, including the exact scanned first-party file set/classification;
- proposed rule implementation paths and CI hook;
- exact allowlist/debt entries and owner/removal disposition;
- concrete protected mutation seams for AE003, with rationale that the static rule is neither broader nor weaker than the accepted owner boundary;
- focused test matrix mapped to the acceptance criteria;
- proof that V2 remains proposal-only and cannot self-apply through repository-owned automation;
- minimum-necessary assessment;
- explicit implementation allowed paths and non-goals;
- expected local command and exact terminal gates for the frozen implementation head;
- residual risks or intentionally unmeasured patterns that require later authority rather than heuristic enforcement.

Only an accepted readiness decision plus `STATUS.md=ready` grants implementation authority.

## Minimum-necessary test

Acceptance criterion: prevent new architecture ownership side channels with deterministic, reviewable evidence while preserving runtime behavior.

- Is this full-spec detail necessary to satisfy the criterion? **Yes.** The definition names the rule families but does not yet freeze how aliases, exceptions, CI parity, V2 negative authority, diagnostics, fixtures, or fail-closed configuration must behave.
- Can the criterion be reached with a smaller product/runtime change? **No product/runtime change is required or authorized.** The smallest sufficient implementation is a repository-static scanner/config/tests plus one CI invocation.
- Why not perform cleanup now? Cleanup would conflate detection authority with architectural rewiring and would make a green first gate depend on changing behavior it is meant to preserve.

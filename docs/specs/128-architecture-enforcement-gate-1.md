# 128 ARCHITECTURE-ENFORCEMENT-GATE-1

Status: definition / planning authority only

## Purpose

Add deterministic repository CI architecture guards that prevent new ownership side channels while preserving current behavior. The gate is a ratchet, not a cleanup slice: existing debt is explicitly allowlisted with an owner/removal spec, and new debt fails closed.

## Authority and boundary

This slice is repository-development enforcement only. It does not change JarvisOS runtime/domain/provider authority, schemas, stores, APIs, provider routing, egress policy, or product behavior. `AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`, and `docs/specs/STATUS.md` remain higher authority.

Coordination Bus V2 artifacts are always non-authoritative proposal material. The enforcement gate MUST make it impossible for a V2 WORKPACK/CANDIDATE_PATCH to become authority or self-apply merely because its syntax is valid or a helper claims tests passed.

## Exact-master inventory requirement

Before readiness, inventory exact current `master` for first-party patterns that can create a second authority path, including at minimum:

1. raw SQLite connections/SQL ownership outside accepted database/core or explicitly owned persistence boundaries;
2. direct external-provider/network dispatch outside the accepted AI execution/provider/egress spine;
3. domain-side mutation paths that bypass accepted owner/service/CAS/reconciliation boundaries;
4. repository-development automation that could treat Coordination Bus V2 comments/workpacks/candidate patches as executable, approval, readiness, merge, queue, or shared-authority input.

Each existing exception retained by the gate must be exact and reviewable, and must name an owner/removal spec or an explicit durable accepted owner. Broad directory-wide exemptions are not acceptable when a narrower symbol/path rule is practicable.

## Required behavior

- Add an offline deterministic architecture check runnable locally and in CI.
- Reject newly introduced forbidden ownership patterns relative to the accepted allowlist/baseline.
- Keep allowlisted legacy debt visible and attributable; the gate must not silently normalize it as desirable architecture.
- Current AI bypass debt identified by the exact-master inventory is owned by 129 where applicable.
- Fail with actionable path/rule diagnostics.
- Avoid heuristic checks that are trivially bypassed by whitespace or aliasing when a small AST/structured check is practical.
- Do not delete, rewire, or refactor runtime code merely to make the first gate green.
- Do not introduce a second architecture registry/store; repository-controlled rule/config data may exist only as the minimum deterministic gate input.
- Do not require network, providers, credentials, runtime data root, or paid AI in tests.

## Coordination Bus V2 negative-authority requirements

The implementation and tests must prove at least these invariants:

- bus issue/comment content is never imported/executed/applied by product or repository-development code as code;
- a WORKPACK/CANDIDATE_PATCH cannot mutate branch/files/STATUS/spec/readiness/PR/review/merge state without a separate ChatGPT writer action that re-reads canonical authority and exact SHA;
- bus content cannot establish readiness, semantic acceptance, finding closure, queue state, merge authority, or Codex budget state;
- no new workflow/action/script gains an automatic `issue_comment` path that applies candidate patches or grants authority from the V2 marker/envelope.

This requirement does not prohibit the explicitly accepted helper behavior of appending one non-authoritative V2 message while another writer is BUSY.

## Acceptance criteria

1. A reproducible exact-master inventory identifies the enforced ownership classes and every retained exception.
2. Each retained debt exception has a narrow match plus owner/removal disposition; unexplained wildcard exemptions fail review.
3. Deterministic tests demonstrate at least one forbidden-new-case failure for each enforced class and demonstrate accepted owner paths remain green.
4. Dedicated tests prove the Coordination Bus V2 negative-authority requirements above, including rejection/non-execution of candidate patch text.
5. CI runs the architecture gate on pull requests without provider/network/secret dependence.
6. Existing required backend/frontend/BLUECAD gates remain green on the frozen implementation head.
7. No runtime behavior, schema, API, provider, product UI, or canonical domain ownership is changed by 128.

## Failure modes to cover

- allowlist so broad that new debt hides under an old directory exemption;
- string/regex-only scanner misses aliased imports or structured calls that should be detectable;
- false positive on accepted database/provider owner code;
- generated/vendor/migration/test fixture content mistaken for new runtime authority without an explicit classification rule;
- bus marker/comment text accidentally treated as executable patch input;
- CI-only path diverges from the locally testable command;
- baseline refresh command can silently bless new violations.

## Non-goals

- no cleanup of the violations found by the inventory;
- no implementation of 127, 129, 130, 131, 132, 133, or 134;
- no `jarvis-pr-attention` integration;
- no 113–126 implementation/planning reopening;
- no new provider, credential, database, durable store, schema, migration, frontend, or domain feature;
- no auto-fix or auto-apply of architecture violations or bus candidate patches.

## Required readiness evidence

Readiness must bind to a fresh exact master and include:

- inventory methodology and findings;
- proposed rule implementation paths and CI hook;
- exact allowlist/debt entries and owner/removal disposition;
- focused test matrix mapped to the acceptance criteria;
- proof that V2 remains proposal-only and cannot self-apply;
- minimum-necessary assessment;
- explicit implementation allowed paths and non-goals.

Only an accepted readiness decision plus `STATUS.md=ready` grants implementation authority.
# GitHub connector compatibility policy

Status: **ACTIVE TEMPORARY TRANSPORT SUPPLEMENT — NO INDEPENDENT GOVERNANCE AUTHORITY**  
Effective date: 2026-08-30  
Reconciled: 2026-09-07  
Scope: repository-development transport mechanics only

This file exists only for a known GitHub-connector Draft/Ready transport defect. It does **not** define model roles, builder behavior, review policy, lifecycle, roadmap priority, merge authority, product/runtime authority, provider policy, credentials, budgets, or security boundaries.

Current governance is owned elsewhere:

- `AGENTS.md` — engineering constitution and hard invariants;
- `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` — Generic Frontier Builder Contract and delivery/review/evidence mechanics;
- `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` — concurrency/shared-writer mechanics only;
- `docs/specs/STATUS.md` — live spec state, hard dependencies, and implementation-PR association;
- the active accepted spec/readiness — slice outcome, scope, non-goals, and any stronger evidence requirements.

If any wording in an older revision of this file conflicts with those surfaces, the older wording is **superseded**. In particular, historical ChatGPT/Claude/Codex role ordering, blanket review rules, Coordination Bus rules, queue policy, and merge policy carried here have no current authority.

## 1. Incident and activation

Compatibility mode remains ACTIVE while either condition holds:

1. upstream OpenAI connector bug `openai/codex#41433` remains open/unresolved; or
2. a bounded live use of the dedicated `mark_pull_request_ready_for_review` action still fails with the known GraphQL schema-selection error involving `Repository.fullDatabaseId` / `headRepository.fullDatabaseId`.

The observed failure is connector transport behavior. Do not reinterpret it as repository corruption, product failure, permission failure, CI failure, or a reason to change JarvisOS runtime code.

## 2. Transport behavior while active

For automated JarvisOS delivery, prefer creating a coherent PR directly with `draft=false` rather than depending on a Draft → Ready transition.

`draft=false` is transport metadata only. It does not imply semantic acceptance, readiness, review completion, queue promotion, or merge authorization.

If a draft PR already exists:

- do not repeatedly retry a known-broken transition;
- never use generic PR metadata mutation as a fake Ready transition;
- preserve exact base/head and any review/comment/thread provenance;
- one bounded live attempt with the dedicated Ready action is allowed when useful to verify connector recovery;
- if the dedicated action still fails, use the least-cost provenance-preserving route available under current canonical governance rather than changing product code or inventing new review infrastructure.

All exact-head invalidation, review/evidence, mutex, merge, and reconciliation behavior is inherited from the higher-authority canonical files above and is intentionally not duplicated here.

## 3. Exit from compatibility mode

Do not disable compatibility mode merely because time passed or one unrelated connector operation works.

Retire this supplement only after both are true:

1. upstream evidence indicates the reported connector defect is fixed/resolved; and
2. one bounded live verification confirms the dedicated Draft → Ready action succeeds, followed by a fresh independent PR read showing `draft=false`.

If the reverse Ready → Draft direction becomes important, verify it separately before relying on it.

After exit criteria are satisfied, mark this file `SUPERSEDED/INACTIVE` or remove the temporary transport rule in a bounded documentation change. Do not leave a temporary workaround pretending to be permanent governance.

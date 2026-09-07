# GitHub connector compatibility policy

Status: **SUPERSEDED / INACTIVE TRANSPORT TOMBSTONE — NO CURRENT AUTHORITY**

This file is retained only as provenance for a GitHub-connector Draft → Ready regression observed in August 2026. It is not current builder governance and must not be used to derive model roles, review policy, lifecycle, roadmap priority, merge authority, or transport behavior.

On 2026-09-07, the currently connected `mark_pull_request_ready_for_review` action was exercised on JarvisOS PR #567 and successfully changed the PR from draft to ready; a fresh independent PR read confirmed `draft=false`. The upstream issue `openai/codex#41433` was still open at that time, so upstream issue state alone is not a reliable activation predicate for this repository.

The previous compatibility rules are therefore superseded and preserved only in Git history.

If a comparable connector defect recurs, treat it as fresh transport evidence. Use the least-cost reversible route under current canonical governance and add a temporary workaround only if the defect materially blocks delivery. Do not reactivate historical instructions merely because an old issue remains open.

Current repository-development authority remains:

- `AGENTS.md` — engineering constitution and hard invariants;
- `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` — Generic Frontier Builder Contract and delivery/review/evidence mechanics;
- `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` — concurrency/shared-writer mechanics only;
- `docs/specs/STATUS.md` — live spec state, hard dependencies, roadmap rows, and implementation-PR association;
- the active accepted spec/readiness — slice outcome, scope, non-goals, and stronger evidence requirements;
- fresh exact Git/PR/runtime/test/proof evidence.

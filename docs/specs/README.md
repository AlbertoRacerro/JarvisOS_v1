# Work-item specs

Each `NNN-<slug>.md` defines one accepted implementation slice. [`STATUS.md`](STATUS.md) is the sole live repository registry for spec state, hard dependencies, roadmap rows, and implementation-PR association; individual specs define accepted outcome, scope, acceptance criteria, required evidence, and non-goals. An explicit current maintainer scheduling directive may order already-authorized work without changing registry authority. Legacy `Status:` prose inside specs is not authoritative.

This file contains **spec registry/lifecycle mechanics only**. Frontier-agent philosophy and review/merge policy live in `../../AGENTS.md` and `../AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`. Post-112 concurrency mechanics live only in `../POST_112_PARALLEL_DELIVERY_PROFILE.md`.

## Startup and lifecycle

For repository work, use current exact GitHub state rather than cached handoffs:

1. Read `../../AGENTS.md`, `../AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, this file, and [`STATUS.md`](STATUS.md). After its activation gate, read `../POST_112_PARALLEL_DELIVERY_PROFILE.md` when concurrency matters.
2. Recover unfinished authorized work before creating duplicates. Otherwise select only work whose live state/dependencies grant the needed authority. `planned` never authorizes product implementation.
3. Read the selected accepted spec/readiness from exact refs and revalidate its outcome/boundaries against current code. Accepted scope, non-goals, hard boundaries, and explicit evidence requirements are binding; implementation method is not binding unless the spec makes the mechanism itself part of acceptance.
4. Keep the registry truthful: implementation starts only after readiness; an open implementation PR uses `**Spec gate:** implementation NNN` and is associated as `in_review`; verified merge transitions to `merged`. Definition/readiness and `N/A` process work use the smallest truthful canonical transition and do not pretend to be implementation.
5. Definition/full-spec/readiness may be combined when the frontier coordinator can resolve the accepted contract safely in one planning change and separate checkpoints would not reduce real uncertainty/risk. Readiness must still become explicit before product implementation.
6. Run the deterministic gates required by `AGENTS.md`, `python scripts/check_spec_status.py --self-test`, and the selected slice. Use proportional review/proof from the execution protocol plus any stronger explicit requirement in the accepted active contract.
7. Merge only under exact-head/CAS rules; GitHub deferred auto-merge is prohibited. Verify fresh `master` and perform only necessary mechanical registry/README reconciliation.

Do not encode permanent scheduling order in this file. Current scheduling comes from fresh registry/dependency truth plus explicit maintainer scheduling directives. A scheduling preference never overrides a hard dependency or creates implementation authority.

## Scope and review boundary

Accepted scope is a closed target, not permission for semantic exhaustiveness.

A finding blocks when fresh evidence proves an accepted criterion/invariant fails, a concrete current in-scope path bypasses the boundary, the diff introduces a material regression, or changed behavior contains a material correctness/security/authority defect. Reviewer severity or architectural preference alone creates no scope.

For one causal mechanism, perform one bounded sibling sweep over directly analogous current in-scope surfaces and batch qualifying repairs. `PARK` concrete valuable out-of-scope/nonblocking findings; `DROP` vague, cosmetic, preference-only, or speculative findings.

The required level and independence of semantic review is defined by `../AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` and any stronger explicit accepted-slice requirement. Do not encode permanent vendor/model ordering here.

A head mutation invalidates affected exact-head review/proof evidence. Unaffected environment/deterministic evidence may be reused when its conclusion cannot have changed.

When accepted scope is complete, required evidence is sufficient, and no concrete material blocker remains, converge and merge rather than extending the slice.

## Status values

The canonical values and transition rules are defined in [`STATUS.md`](STATUS.md). Do not recreate a live status index, queue, roadmap, or model-role policy in this file, root README, strategy documents, chat handoffs, automation prompts, or individual specs.

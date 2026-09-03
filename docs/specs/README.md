# Work-item specs

Each `NNN-<slug>.md` is one implementation slice. [`STATUS.md`](STATUS.md) is the sole live work-state/roadmap authority; individual specs define accepted scope, acceptance criteria, tests, and non-goals. Legacy `Status:` prose inside specs is not authoritative.

## Startup and lifecycle

For repository work, use the current exact GitHub state rather than cached handoffs:

1. Read `../../AGENTS.md`, `../AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, this file, and [`STATUS.md`](STATUS.md). After its activation gate, also apply `../POST_112_PARALLEL_DELIVERY_PROFILE.md`.
2. Recover an unfinished authorized PR/front before creating work. Otherwise select only a `ready` row whose hard dependencies are `merged`; `planned` never authorizes implementation.
3. Read the selected spec/readiness from exact refs and revalidate its stated files/boundaries against current code. Accepted scope and non-goals are binding.
4. Follow the canonical lifecycle and registry handshake in `STATUS.md`: start -> `in_progress`; implementation PR with `**Spec gate:** implementation NNN` -> `in_review` plus PR number; verified merge -> `merged`. Definition/readiness and `N/A` process work use their canonical gates without pretending to be implementation.
5. Run the deterministic gates in `AGENTS.md`, `python scripts/check_spec_status.py --self-test`, and all selected-slice gates. A green workflow or self-authored test is evidence, never semantic acceptance by itself.
6. Merge only under the exact-head/CAS rules in `AGENTS.md` and the execution protocol; GitHub auto-merge is prohibited. Verify fresh `master` and perform only the required mechanical registry reconciliation.

Detailed authority precedence, implementation/recovery mechanics, merge rules, interruption classes, and model roles live in `AGENTS.md` and `../AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`. Post-112 lane/mutex mechanics live only in `../POST_112_PARALLEL_DELIVERY_PROFILE.md`. Do not copy those policies or live queue order here.

## V3.2 material-review boundary

Repository delivery has one serial ChatGPT mutation owner. A builder that observes another enabled A/B/C/D `BUSY` lease inside the canonical freshness window exits without helper-mode analysis, ordinary Coordination Bus production, or shared mutation. Fresh GitHub/PR state is the continuation surface; ordinary Coordination Bus V2 workpacks are retired historical provenance.

Every material implementation PR, and every material workflow/architecture/security/egress/provider/credential/merge-authority/canonical-ownership change, requires independent exact-head semantic review unless a narrower fresh canonical rule explicitly supersedes it. Claude is primary. `Manual Expert Review` first requires exact-head deterministic `backend` and `evidence` success, deduplicates validated Claude evidence for the same review identity, and must materialize a structured verdict/findings marker. Workflow success without that marker is not approval. If Claude terminally fails or yields no trustworthy consumable exact-head verdict, request exactly one current-head Codex review unless one already exists. ChatGPT self-review never substitutes for required independence. Any head mutation invalidates affected review evidence.

Accepted scope is a closed target, not permission for semantic exhaustiveness. A finding blocks only when fresh evidence proves an accepted requirement/invariant or frozen fixture fails, a concrete current first-party in-scope path bypasses the invariant, the diff introduced a concrete regression, or behavior changed by the PR contains a material P0/P1 correctness/security defect. Reviewer severity or architectural preference alone creates no scope. For one causal mechanism, perform one bounded sibling sweep over directly analogous current in-scope surfaces and batch qualifying repairs. `PARK` concrete valuable out-of-scope P2/P3 findings as non-blocking; `DROP` vague, cosmetic, preference-only, or speculative findings. When accepted scope is complete and no concrete material blocker remains, verdict is `APPROVE`.

## Status values

The canonical values and transition rules are defined in [`STATUS.md`](STATUS.md). Do not recreate a live status index, queue, or roadmap in this file, root README, strategy documents, chat handoffs, or individual specs.

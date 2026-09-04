# Spec 119 readiness normative amendment — 2026-09-04

**Status:** normative amendment to `docs/specs/119-coding-runtime-truth-1.md`, paired with `docs/specs/119-readiness-2026-09-04.md`.

Exact parent head: `b80ddcaa3fe8ea0e12c2fdab1ad26f0926c232ef`.

This amendment reconciles the bounded implementation corrections proven during readiness review. It changes no product scope and grants no implementation authority while the live `119` registry row remains `planned`.

## Superseded full-spec clauses

For the behaviors below, this amendment plus the readiness record supersede the conflicting wording in the merged full spec. All unaffected full-spec scope, acceptance criteria and non-goals remain binding.

1. **118 compare `partial` semantics.** Full-spec wording that any `compare_truth.partial` forces `unknown` and acceptance case 11 are superseded. In merged 118, `partial` describes bounded file/commit projection truncation and does not by itself invalidate the top-level exact-pair relationship fields. Readiness therefore governs: validated, internally consistent `status`/`ahead_by`/`behind_by` may establish `local_behind` or `divergent` even when the returned delta projection is partial; the projection must still remain marked partial. Missing, malformed, contradictory or stale relation evidence remains `unknown`.
2. **Git-probe timeout semantics.** Full-spec wording that freezes an independent `2.0 s` timeout for each probe and the corresponding per-probe-timeout reading of acceptance case 14 are superseded. One snapshot has a shared `2.0 s` total monotonic deadline; each fixed probe receives only the remaining budget, with no retries. Readiness tests 14–17 govern the fixed probe seam, total deadline, event-loop nonblocking behavior and child reaping.
3. **Runtime repository mismatch.** The full-spec local failure taxonomy is extended by exactly one bounded code, `repository_mismatch`, for a request whose repository is not both the canonical JarvisOS runtime repository `AlbertoRacerro/JarvisOS_v1` and present in `settings.coding_repositories`. No arbitrary local-repository mapping or remote discovery is added.
4. **Target stability.** Full-spec permissive wording that the route *may* re-resolve the target is superseded: re-resolution is mandatory immediately before every non-`unknown` classification. A changed exact target SHA yields `remote_target_moved` and `unknown`.

## AE002 / security-gate revalidation

Fresh review revalidated `scripts/check_architecture_enforcement.py` and the current architecture-enforcement ownership: AE002 network dispatch covers the accepted network client families/provider completion paths, while the 119 fixed local `subprocess` Git observer performs no direct network call. Therefore 119 requires **no new AE002 network owner, allowlist exception or `configs/architecture_enforcement.json` change**. All remote GitHub reads remain owned by merged 118.

If implementation introduces a direct network call from 119, this revalidation is invalidated and the change is outside current readiness authority.

## Acceptance-test reconciliation

The implementation test floor is the readiness list plus all non-superseded full-spec cases. Explicit mapping for the previously omitted full-spec acceptance case 20 is added:

26. **Startup snapshot anti-forgery:** capture one startup snapshot, mutate the injected live-worktree observation, invoke the request/alignment path repeatedly, and prove the stored startup snapshot object/evidence is never recomputed or replaced by request handling to manufacture `aligned`.

For avoidance of doubt:
- full-spec case 11 is replaced by readiness cases 4–6 and the partial-projection rule above;
- the timeout part of full-spec case 14 is replaced by readiness cases 14–17;
- full-spec case 20 maps to test 26 above;
- all other full-spec deterministic acceptance cases remain required and are covered by the readiness test floor/prose mapping.

## Result

There is now one satisfiable normative rule per corrected behavior: the full spec remains the scope owner, while this explicit amendment/readiness pair governs only the four readiness-proven corrections above and records the missing AE002/test evidence. No implementation may begin until this amendment/readiness PR merges and the live `119` row transitions mechanically to `ready`.
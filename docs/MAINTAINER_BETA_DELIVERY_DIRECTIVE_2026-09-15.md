# Maintainer beta delivery directive — 2026-09-15

Status: current scheduling directive
Supersedes: `docs/MAINTAINER_BETA_DELIVERY_DIRECTIVE_2026-09-09.md` for current scheduling priority.
Authority: maintainer scheduling only; this does not change spec state/readiness, product authority, security boundaries, credentials, egress, Git, filesystem, execution, or merge authority.

## Objective

Optimize for the fastest high-quality first beta with strong future foundations using an 80/20 bias: finish the two current bounded lanes before opening lower-value roadmap or Hermes work.

## Lane 1 — spec 122

Scheduler slots A and B own `122 JARVIS-DEVELOPMENT-ACTIONS-1` until it is merged and canonically reconciled. Derive from fresh master and move through planning/readiness/implementation/reconciliation as efficiently as canonical governance permits.

Reuse accepted 111/116/117 owners. The target is explicit multi-record Development context plus bounded scheduling/reconciliation/Roadmap/promotion `PROPOSE` actions. Preserve context-neutral browsing/opening, domain-owned acceptance, and the existing single context/store/queue owners. No direct domain `COMMIT`/`EXECUTE`, second context/store/queue, or Hermes runtime is authorized by this lane.

After 122 is merged and reconciled, A/B stop Lane 1 and wait for the Lane 2 / Hermes Product checkpoint unless a later maintainer directive changes priority.

## Lane 2 — subscription-backed development pipeline

Scheduler slots C and D own a bounded development-pipeline expansion using already-owned subscriptions/entitlements only: GitHub Education/Copilot Student and Google AI Pro, especially Jules; assess Antigravity only where it materially helps.

Integrate useful workers inside the existing JarvisOS repository-development control plane. Preserve GitHub/`STATUS.md` authority, exact-head/CAS, CI, cloud-delivery/worktree primitives, review boundaries, and the shared-writer mutex. Do not create a second canonical queue/lifecycle/store and do not implement Hermes DEV in this phase.

Hard economic boundary: no new PAYG API use, automatic top-ups/credit purchase, or hidden fallback from included/free quota to billable API. Existing ChatGPT Plus/Codex, Claude Pro, Google AI Pro, and GitHub Education entitlements may be used. Verify real current product/account/repository capability before relying on it. Any path requiring PAT/OAuth/secret exposure must first prove the least-privilege boundary.

If no accepted spec/authority safely covers a material pipeline expansion, derive the minimum spec/ADR/readiness before implementation. Capture useful throughput/quota/failure evidence for later comparison.

After Lane 2 is merged and canonically reconciled, C/D stop and wait for the Lane 1 / Hermes Product checkpoint unless a later directive changes priority.

## Concurrency and convergence

A/B and C/D may perform disjoint work in parallel under `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`. Shared `STATUS.md`, governance, control-path, schema/migration, shared integration, merge, or other colliding writes remain serialized through the canonical shared-writer mutex.

Recover existing work before opening duplicates. Use independent frontier review when it materially reduces risk, but provider/tool unavailability alone must not stall reversible convergence. Do not self-certify material implementation when a practical independent review route exists.

## Checkpoint

Do not advance Hermes Product/DEV, 125, 126, 102+, or later engineering work from these lanes before both current lanes reach their stated closure checkpoints, unless a newer maintainer directive explicitly changes the phase.

## Expiry

This directive remains current until both lanes have converged and the maintainer selects the Hermes Product checkpoint or explicitly supersedes it. The 2026-09-09 directive remains historical evidence for the cloud-delivery/tooling-generalization phase but no longer determines current scheduling priority.

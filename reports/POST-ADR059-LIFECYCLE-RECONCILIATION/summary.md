# Post-ADR-059 lifecycle reconciliation

## Scope

Docs/registry/report only. PR #98 merged ADR-059 before PR #95, but PR #95 was
subsequently merged with temporal wording that still described ADR-059 as pending.
This slice reconciles those lifecycle statements with current canonical history.

## Changed files

- `docs/specs/059-ip-egress-1.md`: ADR-059 is treated as accepted durable authority;
  all substantive egress policy remains unchanged.
- `docs/specs/059b-ip-egress-enforcement.md`: 059b remains blocked on full-spec
  reconciliation and explicit promotion, not on an already-merged ADR.
- `docs/specs/STATUS.md`: PR #95 and PR #98 are recorded as merged; the 059b blocker
  reflects the remaining implementation-spec ladder.
- `reports/059-EGRESS-AUTOPILOT-AMENDMENT/summary.md`: lifecycle history is current
  while prior review dispositions and policy evidence are preserved.
- this report.

## Preserved invariants

- No runtime, schema, provider, workflow, frontend, test, `AGENTS.md`, or
  `docs/DECISIONS.md` change.
- PR #90 / merged 059a remains untouched.
- Effective external eligibility remains S0/S1 only.
- Models remain advisory; model-backed sanitizers use `run_ai_task` and `ai_jobs`.
- Raw/final secret-bearing S4 and monthly hard-budget denial remain
  non-overridable.
- Confirmation cannot convert final effective S2/S3 into externally eligible
  content.
- 059b remains `blocked`; no implementation or external autopilot execution is
  authorized.

## Policy-change assessment

No substantive policy changed in this slice. The modifications remove only stale
pre-merge temporal conditions and align status/merge-gate prose with the already
accepted ADR-059 and merged definition amendment.

## Verification gate

The final diff must contain exactly the four reconciled docs/registry files plus
this report. Required before merge:

1. exact five-file scope verification;
2. GitHub Actions success on the final repository-reachable head;
3. current-head failure-mode-first review;
4. all findings resolved or explicitly dispositioned;
5. explicit maintainer merge authorization.

# Post-ADR-059 lifecycle reconciliation

## Scope

Docs/registry/report only. PR #98 merged ADR-059 before PR #95, but PR #95 was
subsequently merged with temporal wording that still described ADR-059 as pending.
This slice reconciles those lifecycle statements with current canonical history.

## Allowed changes

- `docs/specs/059-ip-egress-1.md`: treat ADR-059 as accepted authority while
  preserving all substantive egress policy.
- `docs/specs/059b-ip-egress-enforcement.md`: keep 059b blocked on full-spec
  reconciliation and promotion, not on an already-merged ADR.
- `docs/specs/STATUS.md`: record the current merge order accurately.
- `reports/059-EGRESS-AUTOPILOT-AMENDMENT/summary.md`: update historical lifecycle
  wording without changing review dispositions or policy.
- this report.

## Invariants

- No runtime, schema, provider, workflow, frontend, test, `AGENTS.md`, or
  `docs/DECISIONS.md` change.
- PR #90 / merged 059a remains untouched.
- Effective external eligibility remains S0/S1 only.
- Models remain advisory; model-backed sanitizers use `run_ai_task` and `ai_jobs`.
- Raw/final secret-bearing S4 and monthly hard-budget denial remain
  non-overridable.
- 059b remains blocked and no implementation is authorized.

## Verification gate

The final diff must contain exactly the four reconciled docs/registry files plus
this report. CI, current-head review, and explicit maintainer merge authorization
remain required.

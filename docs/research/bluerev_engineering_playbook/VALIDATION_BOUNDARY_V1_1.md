# Playbook v1.1 Validation Boundary

## Automated checks in the external package

- JSON Schema: **324/324 records passed**;
- record-level retention and completeness assertions: **3240/3240 passed**;
- catalog-level checks: **26/26 passed**;
- exact duplicate titles: **0**;
- unresolved source IDs: **0**;
- formula-only primary records: **0**;
- case-specific exercise-result records: **0**.

These checks verify structure, completeness, source resolution and policy boundaries. They do not prove universal technical validity or industrial readiness.

## Deliberately non-green gates

- independent domain review: `NOT_RUN`;
- standards-compliance review: `NOT_RUN`;
- legal/regulatory review: `NOT_RUN`;
- BlueRev prototype validation: `NOT_RUN`;
- BlueRev field validation: `NOT_RUN`;
- industrial deployment validation: `NOT_RUN`.

The strict validator therefore returns exit code `2` and status `FAIL`, while the package-integrity validator returns `0`.

## Permitted use

- engineering learning and study;
- method and architecture comparison;
- research radar;
- design framing;
- experiment planning;
- advisory review checklists.

## Prohibited automatic use

- design approval;
- control or safety authority;
- certification basis;
- unreviewed procurement or irreversible capital decisions.

A structurally complete playbook remains guidance until the evidence threshold appropriate to the consequence has been met.

# Quality Gates v2.2

## Non-cheating rule

A gate may pass only from evidence generated independently of the value being checked. A failed gate cannot be cleared by:

- copying the source result into the expected value;
- increasing tolerance without a physical or numerical justification;
- deleting the failing assertion;
- reclassifying a failed check as informational;
- treating schema validity as engineering correctness;
- claiming multiple review agents when only one runtime performed the work.

## Gate A — source identity and grounding

Required:

- source SHA-256 matches the manifest;
- exact PDF page or spreadsheet sheet/range exists;
- anchor terms are found in the selected source region;
- equations are checked against the rendered or cell-level source.

Failure blocks promotion.

## Gate B — canonical-only retention

The retrievable record contains:

- corrected normalized knowledge;
- provenance;
- verification evidence supporting the corrected knowledge.

It does not contain:

- rejected numerical values;
- rejected formulas;
- source-error narratives;
- copied solutions used as unquestioned gold;
- failing source-audit evidence.

Rejected fragments may exist only in temporary QA evidence.

## Gate C — structural completeness

Required:

- unique atomic microtopic ID;
- every equation symbol is registered;
- units and bases are explicit;
- assumptions and validity are present where applicable;
- typed relations use valid targets or remain explicitly unresolved;
- conditional contracts are present for correlations, graphical methods, spreadsheets and FEM.

Schema success alone does not satisfy engineering verification.

## Gate D — engineering verification

At least one load-bearing check must be appropriate to the record:

- dimensional consistency;
- independent numerical reproduction;
- material/energy/elemental balance;
- limiting-case behavior;
- residual of governing equations;
- spreadsheet formula lineage and cell recomputation;
- FEM target at a declared location with expected convergence behavior.

Major or critical failures block export.

## Gate E — strict promotion

A record is exportable only when all conditions hold:

- status is `dimensionally_checked`, `numerically_reproduced` or `cross_checked`;
- source-grounding, deterministic and domain passes are present;
- confidence is at least `0.90`;
- no unresolved issue;
- no major or critical failed check;
- no unresolved variable unit or basis;
- required typed contract has been verified;
- spreadsheet records have a substantive numeric, balance or dimensional check;
- FEM records with verification targets pass a FEM-target check.

The v2.2 rehearsal promoted 37/150 records. The other 113 remain QA-only.

## Gate F — benchmark promotion

Not run in this slice. Before benchmark generation:

- prompt and gold must be separable;
- gold must be independently reproduced;
- alternative valid methods must be accepted;
- deterministic grading must cover load-bearing outputs;
- holdout families must be split before model exposure;
- a failed source audit cannot become benchmark gold.

## Gate G — independent review

Full-corpus mapping requires two genuinely independent review passes, or one independent domain pass plus deterministic authority. Orthogonal checks from one runtime do not count as independent reviewers.

Status in the v2.2 rehearsal: `not_run`.

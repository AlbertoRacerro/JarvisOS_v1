# Engineering Knowledge Quality Gates

## Gate A — candidate extraction

- source SHA-256 and exact location are present;
- equations, diagrams and tables are checked against the rendered source;
- authority is evidence, not proof;
- extracted content remains non-exportable.

## Gate B — canonicalization

- the microtopic is atomic enough to explain and test independently;
- equations, symbols, units, assumptions and validity conditions are explicit;
- conceptual or numerical errors are corrected before the `knowledge` block is written;
- rejected alternatives and error narratives are not copied into retrievable knowledge;
- source evidence records only provenance and which canonical fields it supports.

## Gate C — engineering verification

- dimensions and units pass;
- balances and governing-equation residuals pass where applicable;
- numerical outputs are independently reproduced when data are sufficient;
- limiting cases and physical sanity are checked;
- empirical coefficients are bound to convention, units, range and source;
- unresolved ambiguity keeps `knowledge_exportable` false.

## Gate D — knowledge export

Export is allowed only when:

- `governance.retention_policy` is `canonical_verified_knowledge_only`;
- `verification.knowledge_exportable` is true;
- verification status meets the configured threshold;
- the record contains no rejected values, source-error narrative or evaluator-only material.

## Gate E — benchmark promotion

- prompt, reference knowledge, solution and gold are separable;
- gold is independently reproduced;
- deterministic grading covers all load-bearing outputs;
- alternative valid methods are accepted;
- contamination class and allowed context are explicit;
- adversarial variants test assumptions, units, model choice or interpretation.

## Gate F — Jarvis capability promotion

- deterministic authority is identified wherever a mechanical check exists;
- AI remains advisory around that authority;
- regression tests cover the important failure modes;
- tool and runtime requirements are explicit;
- no production caller is added until boundary tests pass.
